import unittest
from cryptopricebot import crypto_price_bot


class MockHelper(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class ValidateArgTests(unittest.TestCase):
    def test_invalid_bot_key(self):
        cmd_args = MockHelper(botkey=' ')
        with self.assertRaises(crypto_price_bot.InvalidArgument) as context:
            crypto_price_bot._validate_cmd_args(cmd_args)
        self.assertTrue('botkey' in str(context.exception))

    def test_invalid_log_lvl(self):
        cmd_args = MockHelper(botkey='valid-string-for-bot-key', loglvl=' ')
        with self.assertRaises(crypto_price_bot.InvalidArgument) as context:
            crypto_price_bot._validate_cmd_args(cmd_args)
        self.assertTrue('loglvl' in str(context.exception))
        cmd_args.loglvl = 'not-a-real-log-level'
        with self.assertRaises(crypto_price_bot.InvalidArgument) as context:
            crypto_price_bot._validate_cmd_args(cmd_args)
        self.assertTrue('loglvl' in str(context.exception))


class StripBotUserNameTests(unittest.TestCase):
    def test_strip_bot_name(self):
        command = '@randombot btc'
        result = crypto_price_bot._strip_bot_user_name(command)
        self.assertEqual('btc', result)

        command = '@randombot'
        result = crypto_price_bot._strip_bot_user_name(command)
        self.assertEqual('', result)

    def test_return_og_string(self):
        command = 'btc'
        result = crypto_price_bot._strip_bot_user_name(command)
        self.assertEqual('btc', result)

    def test_extra_spaces(self):
        command = '@randombot    btc'
        result = crypto_price_bot._strip_bot_user_name(command)
        self.assertEqual('btc', result)


if __name__ == '__main__':
    unittest.main()
