---
name: moex-mega-alerts
description: "Работа с Mega Alerts Московской биржи через библиотеку moexalgo на Python: `Market.alerts`, `Ticker.alerts`, разбор `alert_type`, сравнение порога и значения, разбор JSON в `reference`, аномалии по EQ и FO, пагинация через offset, группировки, сводные таблицы и исторический контекст после сигнала."
license: MIT
metadata:
  author: moexalgo
  source: https://github.com/moexalgo/algopack-skills
  tags: [moex, биржа, python, алерты]
---

# Mega Alerts MOEXAlgo

## Обзор

Этот навык нужен, когда пользователь хочет Mega Alerts через пакет `moexalgo` на Python и анализ в DataFrame.

Про доступ: `Promo` включает Mega Alerts. Доступность на бесплатном токене «Стартовый» запланирована на уровне `T - 1 день`; проверь текущие условия, прежде чем обещать доступ.

## Быстрый старт

```bash
python -m pip install "moexalgo[dataframe]" python-dotenv
```

```python
import json
import os
from dotenv import load_dotenv
from moexalgo import session, Market, Ticker

load_dotenv()
session.TOKEN = os.environ["APIKEY"]

eq = Market("EQ")
alerts = eq.alerts(date="2025-01-10")

sber = Ticker("SBER")
sber_alerts = sber.alerts(start="2025-01-01", end="2025-03-30")
parsed = sber_alerts["reference"].dropna().map(json.loads)
```

## Основной порядок работы

1. Используй `Market("EQ"|"FO").alerts(date=...)` для сигналов по всему рынку.
2. Используй `Ticker(...).alerts(start=..., end=...)` для одного инструмента.
3. Группируй по `alert_type`, `ticker` и дате с временем.
4. Для пагинации используй `offset` библиотеки, где он поддержан; не передавай сырой `start` из REST в методы библиотеки.
5. Разбирай `reference` только когда нужен исторический контекст после сигнала.
6. Избегай прогнозов и рекомендаций.

## Справочники

Читай `references/mega-alerts.md` про сигнатуры, типы сигналов, поля, разбор `reference` и примеры DataFrame.

## Границы

Для сырых адресов эндпоинтов, curl, JSON и CSV или сценариев без Python используй навык прямого доступа к Mega Alerts.
