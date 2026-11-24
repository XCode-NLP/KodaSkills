---
name: moex-market-data
description: "Работа с рыночными данными Московской биржи через библиотеку moexalgo на Python: `Market` и `Ticker`, токен в `.env`, DataFrame из pandas, метаданные бумаг, котировки marketdata, свечи, сделки, стакан, псевдонимы рынков, переопределение режима торгов, выбор полей, пагинация через offset и анализ данных EQ, FO и FX."
license: MIT
metadata:
  author: moexalgo
  source: https://github.com/moexalgo/algopack-skills
  tags: [moex, биржа, python, данные]
---

# Рыночные данные MOEXAlgo

## Обзор

Этот навык нужен, когда пользователь хочет пакет `moexalgo` на Python, DataFrame в стиле pandas или помощники `Market` и `Ticker` для рыночных данных.

## Быстрый старт

```bash
python -m pip install "moexalgo[dataframe]" python-dotenv
```

```python
import os
from dotenv import load_dotenv
from moexalgo import session, Market, Ticker

load_dotenv()
session.TOKEN = os.environ["APIKEY"]

eq = Market("EQ")
tickers = eq.tickers("ticker", "shortname", "minstep")
quotes = eq.marketdata("ticker", "last", "bid", "offer", "updatetime")

sber = Ticker("SBER")
info = sber.info("ticker", "title", "market", "engine", "decimals")
candles = sber.candles(start="2025-01-01", end="2025-01-31", period="1h")
trades = sber.trades(latest=True)
book = sber.orderbook()
```

## Основной порядок работы

1. Установи `moexalgo[dataframe]` и `python-dotenv` для вывода в DataFrame и загрузки `.env`.
2. Храни `APIKEY` в `.env`, вызывай `load_dotenv()`, затем ставь `session.TOKEN` из `os.environ["APIKEY"]` для доступа по тарифу. Бесплатный токен «Стартовый» даёт свечи и сделки с задержкой 15 минут; `Promo` включает онлайн-стаканы, свечи и сделки.
3. Используй `Market("EQ"|"FO"|"FX")` для строк по всему рынку и `Ticker("SBER")` для одного инструмента.
4. Держи метаданные и котировки раздельно: `tickers(...)` читает блок `securities` из ISS, а `marketdata(...)` — блок `marketdata`.
5. Передавай явные имена полей для компактных DataFrame; `tickers("*")` берёт все поля `securities`, `marketdata("*")` — все поля `marketdata`.
6. Используй `board=...` только после того, как метаданные показали, что нужен нестандартный режим торгов.

## Справочники

Читай `references/market-data.md` про сигнатуры, псевдонимы, поля `securities` и `marketdata`, периоды свечей, оговорки про режимы торгов, пагинацию и примеры DataFrame.

## Границы

Для сырых адресов REST, curl, механики пагинации ISS и интеграций не на Python используй навыки прямого ISS и API.
