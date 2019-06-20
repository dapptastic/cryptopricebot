from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BIGINT
from sqlalchemy.orm import relationship

from cryptodata import db_connection

Base = declarative_base()


class TelegramUser(Base):
    __tablename__ = 'telegram_user'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BIGINT, unique=True)
    requests = relationship("PriceRequest", back_populates="user")


class TelegramChat(Base):
    __tablename__ = 'telegram_chat'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BIGINT, unique=True)
    requests = relationship("PriceRequest", back_populates="chat")


class CryptoCurrency(Base):
    __tablename__ = 'cryptocurrency'

    id = Column(Integer, primary_key=True)
    ticker_symbol = Column(String(10), unique=True, nullable=False)
    requests = relationship("PriceRequest", back_populates="crypto")


class PriceRequest(Base):
    __tablename__ = 'price_request'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("telegram_user.id"), nullable=False)
    chat_id = Column(Integer, ForeignKey("telegram_chat.id"), nullable=False)
    crypto_id = Column(Integer, ForeignKey("cryptocurrency.id"), nullable=False)
    request_dt = Column(DateTime, nullable=False)
    user = relationship("TelegramUser", back_populates="requests")
    chat = relationship("TelegramChat", back_populates="requests")
    crypto = relationship("CryptoCurrency", back_populates="requests")


def create_db(dbstring):
    engine = db_connection.create_db(dbstring)
    Base.metadata.create_all(engine)
