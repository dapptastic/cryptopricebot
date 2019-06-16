from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_db(db_string):
    engine = create_engine('mysql+pymysql://{}'.format(db_string), echo=False)
    engine.execute("CREATE DATABASE IF NOT EXISTS cryptopricebot")  # create db
    engine.execute("USE cryptopricebot")  # select db
    return engine


def get_session_maker_from_string(db_string):
    engine = _get_db_engine_from_string(db_string)
    connection = engine.connect()
    connection.close()
    session_maker = sessionmaker(bind=engine)
    return session_maker


def _get_db_engine_from_string(db_string):
    return create_engine('mysql+pymysql://{}/cryptopricebot'.format(db_string), echo=False)
