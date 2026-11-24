---
name: moex-hi2
description: "Работа с HI2 Московской биржи через библиотеку moexalgo на Python: `Market.hi2`, `Ticker.hi2`, индекс концентрации Херфиндаля — Хиршмана, метрики `hhi_*`, дневной анализ концентрации по EQ, FO и FX, пагинация через offset, сводные таблицы и группировки, полосы интерпретации и оговорки по пропущенным строкам."
license: MIT
metadata:
  author: moexalgo
  source: https://github.com/moexalgo/algopack-skills
  tags: [moex, биржа, python, аналитика]
---

# HI2 MOEXAlgo

## Обзор

Этот навык нужен, когда пользователь хочет HI2 через пакет `moexalgo` на Python и анализ в DataFrame.

Про доступ: `Promo` включает HI2. Доступность на бесплатном токене «Стартовый» запланирована на уровне `T - 1 день`; проверь текущие условия, прежде чем обещать доступ.

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
market_hi2 = eq.hi2(date="2025-01-10")

sber = Ticker("SBER")
sber_hi2 = sber.hi2(start="2025-01-01", end="2025-01-31")
```

## Основной порядок работы

1. Используй `Market("EQ"|"FO"|"FX").hi2(date=...)` для всех инструментов.
2. Используй `Ticker(...).hi2(start=..., end=...)` для одного инструмента.
3. Фильтруй или своди в таблицу по `metric`.
4. Для пагинации используй `offset` библиотеки, где он поддержан; не передавай сырой `start` из REST в методы библиотеки.
5. Применяй широкие полосы концентрации, когда это полезно.
6. Объясняй пропущенные строки возможным покрытием, подпиской, датой или порогом числа участников.

## Справочники

Читай `references/hi2.md` про сигнатуры, имена метрик, поля, полосы интерпретации и примеры DataFrame.

## Границы

Для сырых адресов эндпоинтов, curl, JSON и CSV или сценариев без Python используй навык прямого доступа к HI2.
