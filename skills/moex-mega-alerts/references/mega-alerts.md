# Справочник по Mega Alerts MOEXAlgo

## Импорты и авторизация

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
```

`Promo` включает Mega Alerts. Доступность на бесплатном токене «Стартовый» запланирована на уровне `T - 1 день`; если пользователи видят `403`, пустые данные, ответы не в JSON или отсутствие строк, проверь текущую подписку и текущие условия DataShop, прежде чем обещать доступ. В списках эндпоинтов указаны EQ и FO.

## Сигнатуры методов

```text
Market(...).alerts(date=None, latest=None, offset=None, native=False)
Ticker(...).alerts(start=None, end=None, latest=None, offset=None, native=False)
```

Передавай даты явно. В текущем коде репозитория пропуск `date` в методах рынка или `start` и `end` в методах тикера приводит к `prepare_from_till_dates(...)`, который выбрасывает исключение, а не молча берёт сегодняшнюю дату. Используй `Market("EQ")` или `Market("FO")`, если только текущие данные не подтверждают, что другой рынок наполняется и доступен по подписке.

## Пагинация и большие диапазоны

Используй параметры библиотеки, а не сырые параметры REST. Методы Mega Alerts используют `offset`, а не `start`. Методы по всему рынку внутри пагинируют до лимита вызовов рынка в библиотеке; методы тикера используют меньший лимит вызовов тикера. Для больших диапазонов итерируй по датам или диапазонам либо вызывай с растущим `offset`, где это поддержано. Прямой REST бери только когда пользователю нужны сырые средства управления вроде `start` или `limit` конкретного маршрута.

## Примеры

По всему рынку:

```python
alerts = Market("EQ").alerts(date="2025-01-10")
```

Диапазон по тикеру:

```python
sber_alerts = Ticker("SBER").alerts(start="2025-01-01", end="2025-03-30")
```

Последние строки:

```python
latest = Market("EQ").alerts(date="2025-01-10", latest=True)
```

## Поля

| Поле | Значение |
| --- | --- |
| `tradedate` | Дата |
| `tradetime` | Время сигнала |
| `ticker` | Идентификатор инструмента, нормализованный библиотекой |
| `alert_type` | Код аномалии |
| `threshold` | Порог срабатывания |
| `value` | Наблюдённое значение |
| `reference` | Строка JSON с исторической статистикой после сигналов |
| `systime` | Время загрузки или системы |

## Типы сигналов

Объём:

- `vol_s_99_9_pctl`, `vol_b_99_9_pctl`, `vol_99_9_pctl`.
- `vol_s_max`, `vol_b_max`, `vol_max`.

Нетто-объём:

- `net_vol_99_9_pctl-`, `net_vol_99_9_pctl+`.
- `net_vol_min`, `net_vol_max`.

Изменение цены:

- `pr_change_99_9_pctl-`, `pr_change_99_9_pctl+`.
- `pr_change_min`, `pr_change_max`.

Ценовые уровни:

- `pr_high_max`, `pr_low_min`.

Суффикс `+` означает положительное направление, вверх. Суффикс `-` — отрицательное, вниз.

## Разбор reference

`reference` — это исторический контекст после похожих сигналов, а не прогноз.

```python
import json
import pandas as pd

def parse_reference(value):
    if not value:
        return {}
    try:
        data = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return data[0] if data else {}

refs = alerts["reference"].map(parse_reference)
ref_df = pd.json_normalize(refs)
combined = alerts.join(ref_df.add_prefix("ref_"))
```

Для ключей `reference` вроде `m_5`, `m_15`, `m_30` и `h_1` в локальных примерах закодированы пять значений:

1. Среднее изменение цены при росте, в процентах.
2. Среднее изменение цены при падении, в процентах.
3. Число случаев роста.
4. Число случаев падения.
5. Среднее изменение по всем наблюдениям, в процентах.

## Анализ в DataFrame

Число сигналов:

```python
counts = alerts.groupby(["ticker", "alert_type"]).size().sort_values(ascending=False)
```

Самые сильные абсолютные превышения порога:

```python
alerts["breach_abs"] = (alerts["value"] - alerts["threshold"]).abs()
top = alerts.sort_values("breach_abs", ascending=False).head(20)
```

Таблица по времени:

```python
alerts["datetime"] = alerts["tradedate"].astype(str) + " " + alerts["tradetime"].astype(str)
timeline = alerts[["datetime", "ticker", "alert_type", "value", "threshold"]]
```

Сводка сигналов по дням:

```python
daily = alerts.pivot_table(index="tradedate", columns="alert_type", values="ticker", aggfunc="count", fill_value=0)
```

По умолчанию используй DataFrame. Если пользователь явно просит итераторы или словари, упомяни `native=True` как запасной выход.
