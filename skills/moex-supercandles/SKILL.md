---
name: moex-supercandles
description: "Работа с SuperCandles Московской биржи через библиотеку moexalgo на Python: `Market.tradestats`, `Market.orderstats`, `Market.obstats`, `Ticker.tradestats`, `Ticker.orderstats`, `Ticker.obstats`, разбор полей, пагинация через offset, сводные таблицы и группировки, аналитика по EQ, FO и FX."
license: MIT
metadata:
  author: moexalgo
  source: https://github.com/moexalgo/algopack-skills
  tags: [moex, биржа, python, данные]
---

# SuperCandles MOEXAlgo

## Обзор

Этот навык нужен, когда пользователь хочет SuperCandles через пакет `moexalgo` на Python и анализ в DataFrame.

Про доступ: `Promo` включает SuperCandles. Доступность на бесплатном токене «Стартовый» запланирована на уровне `T - 1 день`; проверь текущие условия, прежде чем обещать доступ.

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
trades_all = eq.tradestats(date="2025-01-10")
orders_all = eq.orderstats(date="2025-01-10")
book_latest = eq.obstats(date="2025-01-10", latest=True)

sber = Ticker("SBER")
trades = sber.tradestats(start="2025-01-01", end="2025-01-31")
orders = sber.orderstats(start="2025-01-01", end="2025-01-31")
book = sber.obstats(start="2025-01-01", end="2025-01-31")
```

## Основной порядок работы

1. Используй `Market("EQ"|"FO"|"FX")` для всех инструментов по дате.
2. Используй `Ticker(...)` для одного инструмента на диапазоне `start` и `end`.
3. Выбирай `tradestats`, `orderstats` или `obstats` по метрике, которая нужна пользователю.
4. Анализируй через группировки, сводные таблицы, отношения или графики pandas под запрошенный вывод.
5. Для пагинации используй `offset` библиотеки, где он поддержан; не передавай сырой `start` из REST в методы библиотеки.
6. По умолчанию держи DataFrame; упоминай `native=True` только когда пользователь явно просит итераторы словарей.

## Справочники

Читай `references/supercandles.md` про сигнатуры методов, поля, заметки по разбору и примеры анализа в DataFrame.

## Границы

Для сырых адресов эндпоинтов, curl, JSON и CSV или ответов без Python используй навык прямого доступа к SuperCandles.
