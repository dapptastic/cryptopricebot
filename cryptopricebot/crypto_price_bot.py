import threading, time, pathlib, argparse
from telegram.ext import Updater, CommandHandler

from coingeckoapi import coingecko_api
from cryptodata import db_connection, data_models, price_req_repo
from cryptoshared import crypto_helpers, logging_helpers


class InvalidArgument(Exception):
    pass


# global variables initialized on startup
logger = None
session_maker = None
bot_key = None

# updated on separate thread by get_tickers_from_api()
crypto_list = []
crypto_by_ticker = {}


def main():
    global logger, bot_key, session_maker

    cmd_args = _get_args()

    _validate_cmd_args(cmd_args)

    pathlib.Path('logs').mkdir(parents=True, exist_ok=True)
    logger = logging_helpers.build_logger('bot-logger', 'logs/cryptopricebot.log', cmd_args.loglvl)
    logger.info('Initializing bot...')

    bot_key = cmd_args.botkey

    # If optional dbstring argument was included, build session_maker. Used later to log price requests to db.
    if cmd_args.dbstring is not None:
        try:
            data_models.create_db(cmd_args.dbstring)
            session_maker = db_connection.get_session_maker_from_string(cmd_args.dbstring)
            logger.info('Database connection successful!')
        except Exception as e:
            logger.error('Unable to connect to the given mysql instance.  Error Message: \'{}\''.format(e))
            logger.info('Running bot with no database connection!  Price requests will not be logged...')

    api_thread = threading.Thread(target=_get_tickers_from_api)
    api_thread.daemon = True
    api_thread.start()

    updater = Updater(bot_key)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("help", _get_help))
    dp.add_handler(CommandHandler("p", _get_price))
    dp.add_handler(CommandHandler("cap", _get_market_cap))
    dp.add_handler(CommandHandler("change", _get_change))
    dp.add_handler(CommandHandler("top", _top_ten))
    dp.add_handler(CommandHandler("bottom", _bottom_ten))
    dp.add_handler(CommandHandler("compare", _compare))
    dp.add_error_handler(_error)

    updater.start_polling(timeout=20, read_latency=5)
    logger.info('Bot initialized!  Waiting for commands...')
    updater.idle()


def _get_args():
    parser = argparse.ArgumentParser()
    # obtained when you create your bot using the BotFather in Telegram
    parser.add_argument("-botkey", required=True)
    # loglvl options are debug, info, error
    parser.add_argument("-loglvl", default='info')
    # optional mysql db. format is 'username:password@instance'
    parser.add_argument("-dbstring")
    cmd_args = parser.parse_args()
    return cmd_args


def _validate_cmd_args(cmd_args):
    cmd_bot_key = cmd_args.botkey
    if cmd_bot_key.strip() == '':
        raise InvalidArgument('-botkey argument is required.')
    cmd_log_lvl = cmd_args.loglvl
    if cmd_log_lvl not in ['debug', 'info', 'error']:
        raise InvalidArgument('-loglvl argument is required. Options are debug|info|error')


def _get_tickers_from_api():
    # set global crypto collections, which are then referenced by the bot commands.
    global crypto_by_ticker
    global crypto_list
    while True:
        try:
            crypto_by_ticker = coingecko_api.get_all_tickers()
            crypto_list = list(crypto_by_ticker.values())
        except Exception as e:
            logger.exception(r'An error occurred with coingecko api:')
        finally:
            time.sleep(10)


def _get_price(bot, update):
    try:
        if not _validate_telegram_update(update):
            return
        _log_command(update.message.from_user.id, update.message.chat.id, update.message.text)

        request_text = update.message.text.lower().replace("/p", "").strip()
        request_text = _strip_bot_user_name(request_text)
        if request_text == '':
            update.message.reply_text('Invalid Request Format.  Try \'/p eth\' or /help for more info', quote=False)
            return
        requested_ticker = request_text.upper()
        if requested_ticker not in crypto_by_ticker:
            update.message.reply_text('Invalid Ticker Symbol', quote=False)
            return
        if 'BTC' not in crypto_by_ticker or 'ETH' not in crypto_by_ticker:
            update.message.reply_text('We are having some API connection issues :( Please try again in a few minutes.',
                                      quote=False)
            return

        # if dbstring argument was used, log price request to the specified db.
        if session_maker is not None:
            try:
                price_req_repo.log_price_request(session_maker, update.message.from_user.id, update.message.chat.id,
                                                 requested_ticker)
            except Exception as e:
                logger.exception(r'An error occurred trying to write this request to the specified DB:')

        ticker = crypto_by_ticker[requested_ticker]
        btc_ticker = crypto_by_ticker['BTC']
        eth_ticker = crypto_by_ticker['ETH']
        ticker.btc_price = ticker.usd_price / btc_ticker.usd_price
        ticker.eth_price = ticker.usd_price / eth_ticker.usd_price

        reply = '{} ({}): {}'.format(ticker.currency_name, requested_ticker, crypto_helpers.format_usd(ticker.usd_price))
        if ticker.percent_change_24h is not None:
            reply += ' | {}'.format(crypto_helpers.format_percent_change(ticker.percent_change_24h))
        if ticker.btc_price is not None:
            reply += '\n{} BTC'.format(crypto_helpers.format_btc(ticker.btc_price))
            if ticker.percent_change_24h is not None and btc_ticker.percent_change_24h is not None:
                reply += ' | {}'.format(
                    crypto_helpers.format_percent_change(crypto_helpers.get_relative_percent_change(ticker.usd_price,
                                                                                                    ticker.percent_change_24h,
                                                                                                    btc_ticker.usd_price,
                                                                                                    btc_ticker.percent_change_24h)))
        if ticker.eth_price is not None:
            reply += '\n{} ETH'.format(crypto_helpers.format_eth(ticker.eth_price))
            if ticker.percent_change_24h is not None and eth_ticker.percent_change_24h is not None:
                reply += ' | {}'.format(
                    crypto_helpers.format_percent_change(crypto_helpers.get_relative_percent_change(ticker.usd_price,
                                                                                                    ticker.percent_change_24h,
                                                                                                    eth_ticker.usd_price,
                                                                                                    eth_ticker.percent_change_24h)))
        if ticker.volume_24h is not None:
            reply += '\nVolume: {}'.format(crypto_helpers.format_volume(ticker.volume_24h))
        update.message.reply_text(reply, quote=False)
    except Exception as e:
        logger.exception(r'An error occurred while processing this command:')
        update.message.reply_text('Oops! Something went wrong with this request. Please try again later.')


def _get_market_cap(bot, update):
    try:
        if not _validate_telegram_update(update):
            return
        _log_command(update.message.from_user.id, update.message.chat.id, update.message.text)

        request_text = update.message.text.lower().replace("/cap", "").strip()
        request_text = _strip_bot_user_name(request_text)
        if request_text == '':
            update.message.reply_text('Invalid Request Format.  Try \'/cap eth\' or /help for more info', quote=False)
            return
        requested_ticker = request_text.upper()
        if requested_ticker not in crypto_by_ticker:
            update.message.reply_text('Invalid Ticker Symbol', quote=False)
            return

        ticker = crypto_by_ticker[requested_ticker]

        reply = '{} ({}) Market Cap:\n'.format(ticker.currency_name, requested_ticker)
        if ticker.market_cap is not None:
            reply += crypto_helpers.format_market_cap(ticker.market_cap)
        else:
            reply += 'Not Available'.format(ticker.market_cap)
        update.message.reply_text(reply, quote=False)
    except Exception as e:
        logger.exception(r'An error occurred while processing this command:')
        update.message.reply_text('Oops! Something went wrong with this request. Please try again later.')


def _get_change(bot, update):
    try:
        if not _validate_telegram_update(update):
            return
        _log_command(update.message.from_user.id, update.message.chat.id, update.message.text)

        request_text = update.message.text.lower().replace("/change", "").strip()
        request_text = _strip_bot_user_name(request_text)
        if request_text == '':
            update.message.reply_text('Invalid Request Format.  Try \'/change eth\' or /help for more info', quote=False)
            return
        requested_ticker = request_text.upper()
        if requested_ticker not in crypto_by_ticker:
            update.message.reply_text('Invalid Ticker Symbol', quote=False)
            return

        ticker = crypto_by_ticker[requested_ticker]

        reply = '{} ({}) Change:'.format(ticker.currency_name, requested_ticker)
        if ticker.percent_change_1h is not None:
            reply += '\n01H | {}'.format(crypto_helpers.format_percent_change(ticker.percent_change_1h))
        else:
            reply += '\n01H | Not Available'
        if ticker.percent_change_24h is not None:
            reply += '\n24H | {}'.format(crypto_helpers.format_percent_change(ticker.percent_change_24h))
        else:
            reply += '\n24H | Not Available'
        if ticker.percent_change_7d is not None:
            reply += '\n07D | {}'.format(crypto_helpers.format_percent_change(ticker.percent_change_7d))
        else:
            reply += '\n07D | Not Available'
        if ticker.percent_change_30d is not None:
            reply += '\n30D | {}'.format(crypto_helpers.format_percent_change(ticker.percent_change_30d))
        else:
            reply += '\n30D | Not Available'
        if ticker.percent_change_1y is not None:
            reply += '\n01Y  | {}'.format(crypto_helpers.format_percent_change(ticker.percent_change_1y))
        else:
            reply += '\n01Y  | Not Available'
        update.message.reply_text(reply, quote=False)
    except Exception as e:
        logger.exception(r'An error occurred while processing this command:')
        update.message.reply_text('Oops! Something went wrong with this request. Please try again later.')


def _top_ten(bot, update):
    try:
        if not _validate_telegram_update(update):
            return
        _log_command(update.message.from_user.id, update.message.chat.id, update.message.text)

        tickers = crypto_list[:200]
        tickers = list(filter(lambda x: x.percent_change_24h is not None, tickers))
        tickers.sort(key=lambda x: x.percent_change_24h, reverse=True)
        top_tickers = tickers[:10]

        top_result = 'Biggest 24h gainers out of top 200 by market cap:\n'
        for index, ticker in enumerate(top_tickers):
            top_result += '{}. {} ({}): {}\n'.format(index + 1, ticker.currency_name, ticker.ticker_symbol,
                                                crypto_helpers.format_percent_change(ticker.percent_change_24h))
        update.message.reply_text(top_result, quote=False)
    except Exception as e:
        logger.exception(r'An error occurred while processing this command:')
        update.message.reply_text('Oops! Something went wrong with this request. Please try again later.')


def _bottom_ten(bot, update):
    try:
        if not _validate_telegram_update(update):
            return
        _log_command(update.message.from_user.id, update.message.chat.id, update.message.text)

        tickers = crypto_list[:200]
        tickers = list(filter(lambda x: x.percent_change_24h is not None, tickers))
        tickers.sort(key=lambda x: x.percent_change_24h)
        bottom_tickers = tickers[:10]

        bottom_result = 'Biggest 24h losers out of top 200 by market cap:\n'
        for index, ticker in enumerate(bottom_tickers):
            bottom_result += '{}. {} ({}): {}\n'.format(index + 1, ticker.currency_name, ticker.ticker_symbol,
                                                   crypto_helpers.format_percent_change(ticker.percent_change_24h))
        update.message.reply_text(bottom_result, quote=False)
    except Exception as e:
        logger.exception(r'An error occurred while processing this command:')
        update.message.reply_text('Oops! Something went wrong with this request. Please try again later.')


def _compare(bot, update):
    try:
        if not _validate_telegram_update(update):
            return
        _log_command(update.message.from_user.id, update.message.chat.id, update.message.text)

        request_text = update.message.text.lower().replace("/compare", "").strip()
        request_text = _strip_bot_user_name(request_text)
        if request_text == '' or '/' not in request_text:
            update.message.reply_text('Invalid Request Format.  Try \'/compare eth/btc\' or /help for more info', quote=False)
            return
        symbols = request_text.split('/')
        if symbols[0].strip() == '' or symbols[1].strip() == '':
            update.message.reply_text('Invalid Request Format.  Try \'/compare eth/btc\' or /help for more info', quote=False)
            return
        requested_ticker_1 = symbols[0].strip().upper()
        requested_ticker_2 = symbols[1].strip().upper()
        if requested_ticker_1 not in crypto_by_ticker or requested_ticker_2 not in crypto_by_ticker:
            update.message.reply_text('Invalid Ticker Symbol', quote=False)
            return
        if requested_ticker_1 == requested_ticker_2:
            update.message.reply_text('Use two different ticker symbols.  Try \'/compare eth/btc\' or /help for more info', quote=False)
            return
        ticker_1 = crypto_by_ticker[requested_ticker_1]
        ticker_2 = crypto_by_ticker[requested_ticker_2]

        reply = '{} ({}) vs. {} ({}):'.format(ticker_1.currency_name, requested_ticker_1, ticker_2.currency_name, requested_ticker_2)
        if ticker_1.percent_change_1h is not None and ticker_2.percent_change_1h is not None:
            reply += '\n01H | {}'.format(
                crypto_helpers.format_percent_change(crypto_helpers.get_relative_percent_change(ticker_1.usd_price,
                                                                                                ticker_1.percent_change_1h, ticker_2.usd_price,
                                                                                                ticker_2.percent_change_1h)))
        else:
            reply += '\n01H | Not Available'
        if ticker_1.percent_change_24h is not None and ticker_2.percent_change_24h is not None:
            reply += '\n24H | {}'.format(
                crypto_helpers.format_percent_change(crypto_helpers.get_relative_percent_change(ticker_1.usd_price,
                                                                                                ticker_1.percent_change_24h, ticker_2.usd_price,
                                                                                                ticker_2.percent_change_24h)))
        else:
            reply += '\n24H | Not Available'
        if ticker_1.percent_change_7d is not None and ticker_2.percent_change_7d is not None:
            reply += '\n07D | {}'.format(
                crypto_helpers.format_percent_change(crypto_helpers.get_relative_percent_change(ticker_1.usd_price,
                                                                                                ticker_1.percent_change_7d, ticker_2.usd_price,
                                                                                                ticker_2.percent_change_7d)))
        else:
            reply += '\n07D | Not Available'
        if ticker_1.percent_change_30d is not None and ticker_2.percent_change_30d is not None:
            reply += '\n30D | {}'.format(
                crypto_helpers.format_percent_change(crypto_helpers.get_relative_percent_change(ticker_1.usd_price,
                                                                                                ticker_1.percent_change_30d, ticker_2.usd_price,
                                                                                                ticker_2.percent_change_30d)))
        else:
            reply += '\n30D | Not Available'
        if ticker_1.percent_change_1y is not None and ticker_2.percent_change_1y is not None:
            reply += '\n01Y  | {}'.format(
                crypto_helpers.format_percent_change(crypto_helpers.get_relative_percent_change(ticker_1.usd_price,
                                                                                                ticker_1.percent_change_1y, ticker_2.usd_price,
                                                                                                ticker_2.percent_change_1y)))
        else:
            reply += '\n01Y  | Not Available'
        update.message.reply_text(reply, quote=False)
    except Exception as e:
        logger.exception(r'An error occurred while processing this command:')
        update.message.reply_text('Oops! Something went wrong with this request. Please try again later.')


def _get_help(bot, update):
    if not _validate_telegram_update(update):
        return
    _log_command(update.message.from_user.id, update.message.chat.id, update.message.text)
    update.message.reply_text('The following commands are available:\n' \
                '/p {ticker_symbol} - get the price of a crypto. volume and % change are for the past 24h\n' \
                '/cap {ticker_symbol} - get the market cap of a crypto.\n' \
                '/change {ticker_symbol} - get % change over time for a crypto.\n' \
                '/compare {ticker_symbol}/{ticker_symbol} - compare crypto A vs crypto B over time.\n' \
                '/top - get the 10 best performing cryptos (out of top 200 market cap) in the past 24 hours.\n' \
                '/bottom - get the 10 worst performing cryptos (out of top 200 market cap) in the past 24 hours.', quote=False)


def _validate_telegram_update(update):
    return update is not None and update.message is not None and update.message.from_user is not None and update.message.chat is not None


def _strip_bot_user_name(request_text):
    # commands can be sent from telegram with this format sometimes: /command@botusername
    # in this case we strip out the username so we can get raw command text
    if request_text.startswith('@'):
        if ' ' in request_text:
            return request_text[request_text.index(' '):].strip()
        else:
            return ''
    return request_text


def _log_command(user_id, chat_id, command_text):
    if logger is not None:
        logger.debug('User: {} | Chat: {} | Command: {}'.format(user_id, chat_id, command_text))


def _error(bot, update, error):
    if logger is not None:
        logger.exception('Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    main()
