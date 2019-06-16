import unittest
from cryptoshared import crypto_helpers


class TestPercentChange(unittest.TestCase):
    def test_positive_percent_change(self):
        start, end = 5, 10
        result = crypto_helpers._get_percent_change(start, end)
        self.assertEqual(100, result)

        start, end = .05, .1
        result = crypto_helpers._get_percent_change(start, end)
        self.assertEqual(100, result)

    def test_negative_percent_change(self):
        start, end = 10, 5
        result = crypto_helpers._get_percent_change(start, end)
        self.assertEqual(-50, result)

        start, end = .1, .05
        result = crypto_helpers._get_percent_change(start, end)
        self.assertEqual(-50, result)


class GetPreviousPrice(unittest.TestCase):
    def test_higher_prev_price(self):
        price, change = 5, -50
        result = crypto_helpers._get_price_before_change(price, change)
        self.assertEqual(10, result)

        price, change = .05, -50
        result = crypto_helpers._get_price_before_change(price, change)
        self.assertEqual(.1, result)

    def test_lower_prev_price(self):
        price, change = 10, 100
        result = crypto_helpers._get_price_before_change(price, change)
        self.assertEqual(5, result)

        price, change = .1, 100
        result = crypto_helpers._get_price_before_change(price, change)
        self.assertEqual(.05, result)


if __name__ == '__main__':
    unittest.main()
