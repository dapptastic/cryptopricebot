from datetime import datetime

from cryptodata.data_models import *


def log_price_request(session_maker, tg_user_id, tg_chat_id, ticker_symbol):
    db_session = None
    try:
        db_session = session_maker()
        db_user = db_session.query(TelegramUser).filter(TelegramUser.telegram_id == tg_user_id).first()
        if db_user is None:
            db_user = TelegramUser()
            db_user.telegram_id = tg_user_id
            db_session.add(db_user)
            db_session.commit()
        db_chat = db_session.query(TelegramChat).filter(TelegramChat.telegram_id == tg_chat_id).first()
        if db_chat is None:
            db_chat = TelegramChat()
            db_chat.telegram_id = tg_chat_id
            db_session.add(db_chat)
            db_session.commit()
        db_crypto = db_session.query(CryptoCurrency).filter(CryptoCurrency.ticker_symbol == ticker_symbol).first()
        if db_crypto is None:
            db_crypto = CryptoCurrency()
            db_crypto.ticker_symbol = ticker_symbol
            db_session.add(db_crypto)
            db_session.commit()
        price_req = PriceRequest()
        price_req.user_id = db_user.id
        price_req.chat_id = db_chat.id
        price_req.crypto_id = db_crypto.id
        price_req.request_dt = datetime.utcnow()
        db_session.add(price_req)
        db_session.commit()
    finally:
        if db_session is not None:
            db_session.close()
