def get_relative_percent_change(currency_a_usd_price, currency_a_usd_change, currency_b_usd_price, currency_b_usd_change):

    currency_a_usd_start_price = _get_price_before_change(currency_a_usd_price, currency_a_usd_change)
    currency_b_usd_start_price = _get_price_before_change(currency_b_usd_price, currency_b_usd_change)

    rate_start = currency_a_usd_start_price / currency_b_usd_start_price
    rate_end = currency_a_usd_price / currency_b_usd_price

    return _get_percent_change(rate_start, rate_end)


def _get_price_before_change(usd_price, usd_change):
    return usd_price / (1 + usd_change / 100)


def _get_percent_change(rate_start, rate_end):
    return ((rate_end - rate_start) / rate_start) * 100


def format_eth(value):
    return '{:.8f}'.format(value)


def format_btc(value):
    return '{:.8f}'.format(value)


def format_usd(value):
    return ' ${:.8f}'.format(value)


def format_usd_short(value):
    return ' ${:.2f}'.format(value)


def format_volume(value):
    return '${:,.0f}'.format(value)


def format_market_cap(value):
    return '${:,.0f}'.format(value)


def format_percent_change(percent_change):
    if percent_change > 0:
        return '+{:.2f}%'.format(percent_change)
    else:
        return '{:.2f}%'.format(percent_change)