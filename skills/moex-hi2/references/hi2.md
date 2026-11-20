# Справочник по HI2 MOEXAlgo

## Импорты и авторизация

```bash
python -m pip install "moexalgo[dataframe]" python-dotenv
```

```python
import os
from dotenv import load_dotenv
from moexalgo import session, Market, Ticker

load_dotenv()
session.TOKEN = os.environ["APIKEY"]
```

`Promo` включает HI2. Доступность на бесплатном токене «Стартовый» запланирована на уровне `T - 1 день`; если пользователи видят `403`, пустые данные, ответы не в JSON или отсутствие строк, проверь текущую подписку и текущие условия DataShop, прежде чем обещать доступ.

## Смысл и частота расчёта

HI2 — индекс концентрации в стиле Херфиндаля — Хиршмана:

```text
HI2 = sum(s_i ** 2)
```

где `s_i` — доля участника в процентах. В локальной документации описан дневной расчёт для поддерживаемых инструментов EQ, FO и FX. Если по инструменту торгует слишком мало участников, строка может не рассчитываться.

## Сигнатуры методов

```text
Market(...).hi2(date=None, latest=None, offset=None, native=False)
Ticker(...).hi2(start=None, end=None, latest=None, offset=None, native=False)
```

Передавай даты явно. В текущем коде репозитория пропуск `date` в методах рынка или `start` и `end` в методах тикера приводит к `prepare_from_till_dates(...)`, который выбрасывает исключение, а не молча берёт сегодняшнюю дату. Методы рынка запрашивают все инструменты за одну дату. Методы тикера запрашивают один инструмент за диапазон `start` и `end`. Используй `latest=True`, когда достаточно последних доступных строк.

## Пагинация и большие диапазоны

Используй параметры библиотеки, а не сырые параметры REST. Методы HI2 используют `offset`, а не `start`. Методы по всему рынку внутри пагинируют до лимита вызовов рынка в библиотеке; методы тикера используют меньший лимит вызовов тикера. Для больших диапазонов итерируй по датам или диапазонам либо вызывай с растущим `offset`, где это поддержано. Прямой REST бери только когда пользователю нужны сырые средства управления вроде `start` или `limit` конкретного маршрута.

## Примеры

По всему рынку:

```python
eq = Market("EQ")
hi2 = eq.hi2(date="2025-01-10")
```

Диапазон по тикеру:

```python
sber = Ticker("SBER")
hi2 = sber.hi2(start="2025-01-01", end="2025-01-31")
```

Фьючерсы и валюта:

```python
fo_hi2 = Market("FO").hi2(date="2025-01-10")
fx_hi2 = Market("FX").hi2(date="2025-01-10")
```

## Поля

| Поле | Значение |
| --- | --- |
| `tradedate` | Дата |
| `tradetime` | Время метрики |
| `ticker` | Идентификатор инструмента, нормализованный библиотекой |
| `metric` | Имя метрики HI2 |
| `value` | Значение HHI |
| `reference` | Дополнительный контекст, часто null |
| `systime` | Время загрузки или системы |

## Имена метрик

Когда важна точность, опирайся на значения из `df["metric"].unique()`. Частые имена:

- `hhi_volume`: концентрация по объёму торгов.
- `hhi_buy`: концентрация по объёму покупок.
- `hhi_sell`: концентрация по объёму продаж.
- `hhi_netflow_buy`: концентрация по положительному нетто-потоку.
- `hhi_netflow_sell`: концентрация по отрицательному нетто-потоку.
- `hhi_passive`: концентрация по пассивному объёму, мейкерскому.
- `hhi_active` или `hhi_aggressive`: концентрация по активному объёму, тейкерскому.
- `hhi_passive_buy`, `hhi_passive_sell`.
- `hhi_active_buy`, `hhi_active_sell` или `hhi_aggressive_buy`, `hhi_aggressive_sell`.

## Полосы интерпретации

```python
def concentration_band(value):
    if value < 1500:
        return "low"
    if value <= 2500:
        return "moderate"
    return "high"
```

Считай это широкими полосами для отбора, а не правилами торговли.

## Анализ в DataFrame

Полосы по строкам:

```python
df = Ticker("SBER").hi2(start="2025-01-01", end="2025-01-31")
df["band"] = df["value"].map(concentration_band)
```

Сводная таблица метрик по датам:

```python
pivot = df.pivot_table(index="tradedate", columns="metric", values="value", aggfunc="last")
```

Поиск концентрированных инструментов:

```python
market = Market("EQ").hi2(date="2025-01-10")
high = market[(market["metric"] == "hhi_volume") & (market["value"] > 2500)]
```

Проверка доступных метрик:

```python
available_metrics = sorted(df["metric"].dropna().unique())
```

По умолчанию используй DataFrame. Если пользователь явно просит итераторы или словари, упомяни `native=True` как запасной выход.
