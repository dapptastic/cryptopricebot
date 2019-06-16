FROM python:3

WORKDIR /app

ADD . /app

RUN pip install --trusted-host pypi.python.org -r cryptopricebot/docker/requirements.txt

ENV PYTHONPATH="$PYTHONPATH:/app"

ENTRYPOINT ["python", "cryptopricebot/crypto_price_bot.py"]