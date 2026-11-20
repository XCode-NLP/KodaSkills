# Справочник по календарям ISS

Для торговых календарей используй ISS напрямую. В локальной документации сказано, что методы календарей поддерживают `from`, `till` и пагинацию через `start`; некоторые эндпоинты поддерживают `show_all_days=1` и `iss.only`. В ALGOPACK `Promo` есть машиночитаемый календарь, но не подразумевай, что каждому публичному маршруту календаря нужен `Promo`. Если адрес календаря возвращает `text/html` вместо JSON, сверь текущий маршрут в живом справочнике ISS, прежде чем полагаться на этот эндпоинт.

## Нерабочие дни по всем рынкам

Эндпоинт:

```text
/iss/calendars.json
```

Поля:

- `tradedate`: дата календаря.
- `currency_workday`, `futures_workday`, `stock_workday`: `1` — торговый день, `0` — неторговый, `null` — неизвестно.
- `currency_trade_session_date`, `futures_trade_session_date`, `stock_trade_session_date`.
- `currency_reason`, `futures_reason`, `stock_reason`: код причины.

Коды причин в локальной документации:

- `H`: праздник.
- `W`: выходной или особый неторговый день.
- `N`: обычные торги.
- `T`: перенесённый день.

Пример:

```python
import requests
import pandas as pd

url = "https://iss.moex.com/iss/calendars.json"
params = {"from": "2025-01-01", "till": "2025-01-31", "show_all_days": 1}
payload = requests.get(url, params=params, timeout=30).json()
block = payload["off_days"]
calendar = pd.DataFrame(block["data"], columns=[c.lower() for c in block["columns"]])
```

## Календарь фондового рынка

Эндпоинты:

- `/iss/calendars/stock.json`: неторговые дни фондового рынка.
- `/iss/calendars/stock/static.json?iss.only=markets_classifier`: классификатор рынков.
- `/iss/calendars/stock/static.json?iss.only=boards_classifier`: классификатор режимов торгов.
- `/iss/calendars/stock/securities/boards.json`: режимы по бумаге и дате.
- `/iss/calendars/stock/session/settlecodes.json`: коды расчётов.
- `/iss/calendars/stock/securities/suspended/details.json`: приостановки торгов.
- `/iss/calendars/stock/securities/changes.json`: изменения атрибутов бумаг.
- `/iss/calendars/stock/session.json`: расписание торговых сессий.

Полезные поля сессий фондового рынка:

- `tradedate`, `tradingsession`, `boardid`, `secid`.
- `type`, `time_from`, `time_till`, `updatetime`.
- `tradingsession`: в локальной документации указаны `0` — утренняя, `1` — основная, `2` — вечерняя, `5` — особый день.

## Календарь срочного рынка

Эндпоинты:

- `/iss/calendars/futures.json`: неторговые дни срочного рынка.
- `/iss/calendars/futures/securities.json`: метаданные фьючерсов и опционов.
- `/iss/calendars/futures/session.json`: расписание сессий.

`futures/securities.json` содержит блоки опционов и FORTS. Поля фьючерсов включают `secid`, `asset_code`, `shortname`, `exec_type`, `expiration_date`, `end_date`, `weekend_session`.

## Календарь валютного рынка

Эндпоинты:

- `/iss/calendars/currency.json`: неторговые дни и данные расчётов валютного рынка.
- `/iss/calendars/currency/session.json`: данные сессий и бумаг валютного рынка.
- `/iss/calendars/currency/securities.json`: приостановленные инструменты и сдвиги расчётов.
- `/iss/calendars/currency/changes.json`: изменения.

Поля валютного рынка включают `tradedate`, `secid`, `boardid`, `currencyid`, `faceunit`, `prevdate`, `settledate`, `updatetime`.

## Помощник для пагинации

```python
def calendar_pages(url, block_name, params=None):
    import pandas as pd
    import requests

    params = dict(params or {})
    start = int(params.get("start", 0))
    frames = []
    while True:
        params["start"] = start
        payload = requests.get(url, params=params, timeout=30).json()
        block = payload[block_name]
        rows = block["data"]
        if not rows:
            break
        frames.append(pd.DataFrame(rows, columns=[c.lower() for c in block["columns"]]))
        start += len(rows)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
```
