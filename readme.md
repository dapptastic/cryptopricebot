# cryptopricebot
A python-based telegram bot that allows you to quickly check the price of a cryptocurrency in the Telegram app.  
Along with basic price checking, there are several other useful functions.  See below for more information.

## Getting Started

### Using @moontrackerbot (Crypto Classic Bot)
Open the Telegram app and simply start a conversation with @moontrackerbot or add it to an existing group.  
Once the bot has been added, type /help for an explanation of the available commands, which are also listed at the bottom of this file.

### Using Docker
To run your own instance of the bot, you can follow the steps below and quickly launch the pre-built docker container:

1. Create a bot with Telegram and save the bot key.
2. Install docker on the server where you want to host the bot, then run the following command:

	*docker run dapptastic/cryptopricebot -botkey 'your-bot-key' -loglvl 'info' -dbstring 'user:password@instance*
	
	- **botkey**: The key you received when you created your bot with Telegram.
	- **loglvl**: Options are debug|info|error.  Debug will log every single command, so typically 'info' is recommended.
	- **dbstring**: Optional connection string to a mysql database.  The user must have permission to create a database on this instance.  
	Alternatively, you can create a database called cryptopricebot before running the bot, and create a user specifically to interact with it.  This method is more secure.  
3.  Start a conversation with your bot on Telegram and make sure it works!

### From source
1. Install Python 3.6
2. Install the following dependencies with pip: 
    python-telegram-bot, requests, sqlalchemy, pymysql
3. Tinker with the code and have fun :)

## Bot Commands

The following commands are available:  
**/p** {ticker_symbol} - get the price of a crypto. volume and % change are for the past 24h.  
**/cap** {ticker_symbol} - get the market cap of a crypto.  
**/change** {ticker_symbol} - get % change over time for a crypto.  
**/compare** {ticker_symbol}/{ticker_symbol} - compare crypto A vs crypto B over time.  
**/top** - get the 10 best performing cryptos (out of top 200 market cap) in the past 24 hours.  
**/bottom** - get the 10 worst performing cryptos (out of top 200 market cap) in the past 24 hours.
