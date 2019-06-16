import requests

from cryptoshared.ticker_result import TickerResult


class InvalidTicker(Exception):
    pass


def get_all_tickers(min_volume=0, logger=None):
    tickers = {}
    for i in range(1, 9):
        response = _api_get_all_tickers(i)
        json_response = response.json()
        for item in json_response:
            try:
                volume = float(item['total_volume'])
                if volume > min_volume:
                    ticker_result = TickerResult()
                    _build_ticker_result(item, ticker_result)
                    if ticker_result.ticker_symbol not in tickers:
                        tickers[ticker_result.ticker_symbol] = ticker_result
            except KeyError as key_error:
                key_err_msg = 'The following key was not present in the CoinGecko API response: \'{}\''.format(key_error)
                if logger is not None:
                    logger.error(key_err_msg)
            except ValueError as value_error:
                if logger is not None:
                    logger.error(value_error)
            except InvalidTicker as ticker_error:
                if logger is not None:
                    logger.debug(ticker_error)
            except Exception as e:
                if logger is not None:
                    logger.exception('An error occurred while processing the response from CG API:')
    return tickers


def _build_ticker_result(json_response, ticker_result):
    ticker_result.exchange_name = 'CoinGecko'
    ticker_result.currency_id = json_response['id']

    name = json_response['name']
    if not name:
        raise InvalidTicker('\'Name\' is a required field.  Skipping this currency.')
    symbol = json_response['symbol']
    if not symbol:
        raise InvalidTicker('\'Symbol\' is a required field.  Skipping this currency.')
    usd_price = json_response['current_price']
    if not usd_price:
        raise InvalidTicker('\'USD Price\' is a required field.  Skipping this currency.')
    ticker_result.currency_name = name
    ticker_result.ticker_symbol = symbol.upper()
    ticker_result.usd_price = float(usd_price)

    market_cap = json_response['market_cap']
    volume_24h = json_response['total_volume']
    change_1h = json_response['price_change_percentage_1h_in_currency']
    change_24h = json_response['price_change_percentage_24h_in_currency']
    change_7d = json_response['price_change_percentage_7d_in_currency']
    change_30d = json_response['price_change_percentage_30d_in_currency']
    change_1y = json_response['price_change_percentage_1y_in_currency']
    if market_cap:
        ticker_result.market_cap = float(market_cap)
    if volume_24h:
        ticker_result.volume_24h = float(volume_24h)
    if change_1h:
        ticker_result.percent_change_1h = float(change_1h)
    if change_24h:
        ticker_result.percent_change_24h = float(change_24h)
    if change_7d:
        ticker_result.percent_change_7d = float(change_7d)
    if change_30d:
        ticker_result.percent_change_30d = float(change_30d)
    if change_1y:
        ticker_result.percent_change_1y = float(change_1y)


def _api_get_all_tickers(page_number):
    response = requests.get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&'
                            'per_page=250&page={}&sparkline=false&'
                            'price_change_percentage=1h%2C24h%2C7d%2C30d%2C1y'.format(page_number))
    return response

