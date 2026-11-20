---
name: moex-futoi
description: "Работа с FUTOI Московской биржи через библиотеку moexalgo на Python: `Market(\"FO\").futoi`, `Ticker(...).futoi`, открытый интерес фьючерсов, разделение FIZ и YUR, поля `pos`, `pos_long` и `pos_short`, число участников, оговорки по параметрам и агрегации."
license: MIT
metadata:
  author: moexalgo
  source: https://github.com/moexalgo/algopack-skills
---

# FUTOI MOEXAlgo

## Обзор

Этот навык нужен, когда пользователь хочет FUTOI через пакет `moexalgo` на Python и анализ в DataFrame.

Про доступ: на бесплатном токене «Стартовый» FUTOI отстаёт на `T - 15 дней`; `Promo` даёт более полный и онлайн-доступ в рамках текущей подписки.

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

fo = Market("FO")
all_futoi = fo.futoi(date="2025-01-10")

si = Ticker("SiH5")
si_futoi = si.futoi(start="2025-01-10", end="2025-01-10")
```

## Основной порядок работы

1. Используй `Market("FO").futoi(date=...)` для всех строк FUTOI по фьючерсам.
2. Используй `Ticker(...).futoi(start=..., end=...)` для одного инструмента срочного рынка.
3. Разделяй по `clgroup`, обычно `FIZ` и `YUR`.
4. Группировки, сводные таблицы и графики pandas применяй только когда пользователь просит такой анализ.
5. Помни, что методы FUTOI в библиотеке не дают `latest` и `offset`; если нужны эти сырые средства эндпоинта, используй прямой REST.
6. Объясняй, что строки — агрегированные снимки по фьючерсам, а не записи отдельных трейдеров и не точное позиционирование FIZ и YUR по одному контракту.

## Справочники

Читай `references/futoi.md` про сигнатуры, поля, оговорки по агрегации и примеры DataFrame.

## Границы

Для адресов в браузере, curl, сырых JSON и CSV или вывода без Python используй навык прямого доступа к FUTOI.
