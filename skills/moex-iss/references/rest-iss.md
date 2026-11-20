# Прямой справочник по ISS REST

## Содержание

- [Хосты](#хосты)
- [Пример с requests](#пример-с-requests)
- [Пример с curl](#пример-с-curl)
- [Форматы вывода](#форматы-вывода)
- [Разбор ответа](#разбор-ответа)
- [Пагинация](#пагинация)
- [Типовые шаблоны эндпоинтов](#типовые-шаблоны-эндпоинтов)
- [Эндпоинты поиска и истории](#эндпоинты-поиска-и-истории)
- [Полезные параметры запросов](#полезные-параметры-запросов)
- [Неподдерживаемые и граничные случаи](#неподдерживаемые-и-граничные-случаи)

## Хосты

- Публичный ISS: `https://iss.moex.com/iss`
- Авторизованный шлюз ALGOPACK и API: `https://apim.moex.com/iss`

Используй `apim.moex.com` вместе с `Authorization: Bearer ${APIKEY}` для наборов ALGOPACK в реальном времени, полностью актуальных или доступных только подписчикам. `iss.moex.com` бери для публичных эндпоинтов, когда подписка не требуется; публичные данные могут быть с задержкой или урезаны.

## Пример с requests

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()
url = "https://apim.moex.com/iss/datashop/algopack/eq/tradestats/SBER.json"
headers = {"Authorization": f"Bearer {os.environ['APIKEY']}"}
params = {"from": "2025-01-01", "till": "2025-01-31", "start": 0}

resp = requests.get(url, headers=headers, params=params, timeout=30)
resp.raise_for_status()
payload = resp.json()
```

## Пример с curl

```bash
curl -L "https://apim.moex.com/iss/datashop/algopack/eq/tradestats/SBER.json?from=2025-01-01&till=2025-01-31&start=0" \
  -H "Authorization: Bearer ${APIKEY}"
```

## Форматы вывода

Большинство маршрутов ISS выбирают формат ответа по суффиксу: `.json`, `.csv`, `.xml` или `.html`. В примерах держи `.json` для программного разбора, если пользователю явно не нужен другой формат. Для передачи данных используй `.csv` или нормализованные таблицы JSON, для вывода в браузере — простые HTML-графики, для ноутбука и скрипта — pandas или Matplotlib, а внутри приложения — уже принятый там стек графиков. Если эндпоинт описан без суффикса, добавь `.json` до написания кода разбора JSON.

## Разбор ответа

Блоки JSON в ISS обычно содержат массивы `columns` и `data`. Приведи целевой блок к строкам, прежде чем фильтровать, соединять, писать таблицы или строить графики:

```python
import pandas as pd

block = payload["data"] if "data" in payload else payload["candles"]
df = pd.DataFrame(block["data"], columns=[c.lower() for c in block["columns"]])
```

Для стандартных рыночных данных блоки могут включать `securities`, `marketdata`, `trades`, `orderbook`, `candles` или блоки конкретного продукта вроде `futoi`.

## Пагинация

Используй параметр `start`. Повторяй цикл, пока целевой блок не вернёт пустой результат:

```python
import pandas as pd
import requests

def fetch_all(url, block_name, headers=None, params=None):
    params = dict(params or {})
    start = int(params.get("start", 0))
    frames = []
    while True:
        params["start"] = start
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        block = resp.json()[block_name]
        rows = block["data"]
        if not rows:
            break
        frames.append(pd.DataFrame(rows, columns=[c.lower() for c in block["columns"]]))
        start += len(rows)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
```

Не предполагай единый максимальный размер страницы. В заметках упоминаются эндпоинты с разными лимитами, а сырые эндпоинты SuperCandles могут требовать пагинации для полных дней и диапазонов. Держи `limit` зависящим от маршрута там, где он поддержан; не обещай единый универсальный максимум.

## Типовые шаблоны эндпоинтов

Рыночные данные:

- Все бумаги и marketdata EQ: `/iss/engines/stock/markets/shares/boards/TQBR/securities.json`
- Все бумаги и marketdata FO: `/iss/engines/futures/markets/forts/boards/RFUD/securities.json`
- Все бумаги и marketdata FX: `/iss/engines/currency/markets/selt/boards/CETS/securities.json`
- Свечи тикера: `/iss/engines/{engine}/markets/{market}/boards/{board}/securities/{ticker}/candles.json`
- Сделки тикера: `/iss/engines/{engine}/markets/{market}/boards/{board}/securities/{ticker}/trades.json`
- Стакан тикера: `/iss/engines/{engine}/markets/{market}/boards/{board}/securities/{ticker}/orderbook.json`

ALGOPACK:

- SuperCandles: `/iss/datashop/algopack/{eq|fo|fx}/{tradestats|orderstats|obstats}[/{ticker}].json`
- HI2: `/iss/datashop/algopack/{eq|fo|fx}/hi2[/{ticker}].json`
- Mega Alerts: `/iss/datashop/algopack/{eq|fo}/alerts[/{ticker}].json`
- FUTOI: `/iss/analyticalproducts/futoi/securities[/{ticker}].json`

## Эндпоинты поиска и истории

Поиск бумаг и тикеров:

- Список и поиск всех бумаг: `/iss/securities.json`
- Карточка одной бумаги: `/iss/securities/{ticker}.json`
- Список бумаг акций: `/iss/engines/stock/markets/shares/securities.json`
- Список фьючерсов: `/iss/engines/futures/markets/forts/securities.json`
- Список валют: `/iss/engines/currency/markets/selt/securities.json`
- Список индексов: `/iss/engines/stock/markets/index/securities.json`

Поиск по группам режимов полезен, когда маршрут по конкретному режиму не находит инструменты:

- Группа режимов акций: `/iss/engines/stock/markets/shares/boardgroups/57/securities.json?iss.only=securities&iss.json=extended&securities.columns=SECID,SHORTNAME`
- Группа режимов фьючерсов: `/iss/engines/futures/markets/forts/boardgroups/45/securities.json?iss.only=securities&iss.json=extended&securities.columns=SECID,SHORTNAME`
- Группа режимов валют: `/iss/engines/currency/markets/selt/boardgroups/13/securities.json?iss.only=securities&iss.json=extended&securities.columns=SECID,SHORTNAME`
- Свечи по группе режимов индексов: `/iss/engines/stock/markets/index/boardgroups/9/securities/{ticker}/candles.json`

Маршруты истории используют префикс `/iss/history/...` и часто отдают другие блоки и столбцы, чем эндпоинты текущей сессии:

- История сделок фьючерсов: `/iss/history/engines/futures/markets/forts/trades.json`
- История бумаг облигаций: `/iss/history/engines/stock/markets/bonds/securities.json`
- История бумаг индексов: `/iss/history/engines/stock/markets/index/securities.json`

## Полезные параметры запросов

- `iss.only=block`: вернуть только выбранный блок, например `marketdata`, `securities` или `candles`.
- `iss.json=extended`: расширенный формат JSON, когда он нужен коду интеграции.
- `from`, `till`: исторический диапазон дат.
- `date`: запрос продукта за одну дату.
- `interval`: интервал свечей, например `1`, `10`, `60`, `24`, `7`, `31`.
- `latest=1`: последние строки продукта, где поддержано.
- `start`: смещение пагинации.

## Неподдерживаемые и граничные случаи

- Если в `moexalgo` нет помощника для календарного или статического эндпоинта, используй ISS напрямую.
- Если эндпоинт возвращает 403 с токеном, проверь подписку на продукт и покрытие эндпоинта.
- Если описанный эндпоинт возвращает `text/html` вместо JSON, считай это несовпадением текущего эндпоинта или маршрута и сверься с живым справочником ISS до написания кода разбора.
- Если эндпоинт возвращает JSON без строк, проверь торговый календарь и частоту публикации, прежде чем считать это сбоем.
