# Справочник по рыночным данным MOEXAlgo

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

Задай `APIKEY=...` в локальном файле `.env` и не добавляй этот файл в систему контроля версий. Когда `session.TOKEN` задан, библиотека использует `https://apim.moex.com/iss` и добавляет `Authorization: Bearer ...` для доступа по тарифу. Бесплатный токен «Стартовый» даёт свечи и сделки с задержкой 15 минут; `Promo` включает онлайн-стаканы, свечи и сделки. Без токена библиотека использует публичный ISS, данные в котором могут быть с задержкой или урезаны.

## Рынки и режимы торгов

| Примеры псевдонимов | Движок и рынок | Режим по умолчанию | Заметки |
| --- | --- | --- | --- |
| `EQ`, `eq`, `shares`, `stocks`, `equity` | `stock/shares` | `TQBR` | Акции |
| `FO`, `fo`, `futures`, `forts` | `futures/forts` | `RFUD` | Фьючерсы, поддерживает FUTOI |
| `FX`, `fx`, `currency`, `selt` | `currency/selt` | `CETS` | Валюта |
| `index` | `stock/index` | `SNDX` | Базовые рыночные данные |
| `bonds` | `stock/bonds` | `TQOB` | Базовые рыночные данные |
| `options` | `futures/options` | `ROPD` | Базовые рыночные данные |

Переопределение режима торгов:

```python
eq_tqpi = Market("EQ", board="TQPI")
instrument = Ticker("SOME_TICKER", board="TQPI")
```

Переопределяй режим только когда режим по умолчанию не находит инструмент или диапазон дат захватывает миграцию между режимами.

## Методы Market

```python
eq = Market("EQ")

tickers = eq.tickers("ticker", "shortname", "minstep")
all_ticker_fields = eq.tickers("*")
quotes = eq.marketdata("ticker", "last", "bid", "offer", "updatetime")
all_quote_fields = eq.marketdata("*")
trades = eq.trades()
recent_candles = eq.candles()
```

`Market.candles()` возвращает недавние рассчитанные минутные свечи из сделок текущего дня. Это не метод исторического диапазона свечей.

## Методы Ticker

```python
sber = Ticker("SBER")

info = sber.info("ticker", "title", "market", "engine", "decimals")
all_info = sber.info("*")
trades = sber.trades()
latest_trade = sber.trades(latest=True)
book = sber.orderbook()
candles = sber.candles(start="2025-01-01", end="2025-01-31", period="1h")
latest_candle = sber.candles(start="2025-01-01", end="2025-01-31", period="1h", latest=True)
```

Частые сигнатуры:

```text
Market(name: str, board: str = None)
Ticker(name: str, board: str = None)
Market.tickers(*fields: str, native: bool = False)
Market.marketdata(*fields: str, native: bool = False)
Ticker.info(*fields: str, native: bool = False)
Ticker.candles(start, end, period=None, offset=0, latest=False, native=False)
Ticker.trades(tradeno_or_recno=None, offset=0, latest=False, native=False)
Ticker.orderbook(native=False)
```

Сделки фьючерсов принимают первым аргументом `recno`; сделки акций и валюты используют `tradeno`.

## Блоки securities и marketdata

- `Market.tickers(...)` читает блок `securities` из ISS. Используй его для метаданных: `minstep`, `lotsize`, `stepprice`, `shortname`, `sectype`.
- `Market.marketdata(...)` читает блок `marketdata` из ISS. Используй его для котировок и полей сессии: `last`, `bid`, `offer`, `voltoday`, `updatetime`.
- `tickers("*")` означает все поля `securities`. `marketdata("*")` — все поля `marketdata`.
- Поля не переходят между блоками. Забирай метаданные и котировки отдельно, затем соединяй или фильтруй DataFrame в pandas.

Оба метода нормализуют `SECID` в `ticker`, а `BOARDID` в `board`. Даже при запросе короткого списка полей возвращаемый DataFrame может содержать `ticker` и `board`, если эти исходные столбцы есть.

Пример в стиле тестов репозитория. `minstep` и `stepprice` берутся из блока `securities`, а `last` — из блока `marketdata`, поэтому здесь нужны два вызова библиотеки:

```python
market = Market("futures")
securities = market.tickers("minstep", "stepprice")
market_data = market.marketdata("last")

security = securities[securities["ticker"] == "GDM6"]
quote = market_data[market_data["ticker"] == "GDM6"]
```

## Периоды свечей

Нативные интервалы ISS:

- Строки: `"1min"`, `"10min"`, `"1h"`, `"1D"`, `"1W"`, `"1M"`.
- Числа: `1`, `10`, `60`, `24`, `7`, `31`.

Интервалы, пересобираемые библиотекой:

- `"5min"`, `"15min"`, `"20min"`, `"30min"`, `"2h"`, `"3h"`, `"6h"`, `"12h"`, `"5D"`, `"10D"`, `"2W"`, `"4W"`.

Для исторических свечей указывай `start` и `end` явно.

## Пагинация и большие диапазоны

Используй параметры библиотеки, а не сырые параметры REST. `Ticker.candles(...)` и `Ticker.trades(...)` предоставляют `offset`; не передавай сырой `start` из ISS в методы библиотеки. Для больших исторических выгрузок итерируй по датам или диапазонам либо вызывай с растущим `offset`, где метод это поддерживает. Прямой ISS и REST бери только когда пользователю нужны сырые средства управления пагинацией.

## Важные поля

Метаданные бумаги:

- `ticker`, `shortname`, `lotsize`, `decimals`, `minstep`, `isin`, `listlevel`.
- У фьючерсов обычно есть `sectype`, `assetcode`, `lotvolume`, `initialmargin`, `lasttradedate` и поля вроде `stepprice`, если их запросить.

Marketdata:

- `bid`, `offer`, `last`, `open`, `high`, `low`, `waprice`, `numtrades`, `voltoday`, `valtoday`, `updatetime`, `systime`.

Свечи:

- `open`, `high`, `low`, `close`, `volume`, `value`, `begin`, `end`.

Сделки:

- `tradeno` или `recno`, `tradetime`, `price`, `quantity`, `value`, `buysell`, `systime`.

Стакан:

- `buysell`, `price`, `quantity`, `seqnum`, `updatetime`.

## Примеры с DataFrame

Соединение метаданных и котировок:

```python
eq = Market("EQ")
tickers = eq.tickers("ticker", "shortname", "minstep")
quotes = eq.marketdata("ticker", "last", "bid", "offer", "updatetime")
snapshot = tickers.merge(quotes, on="ticker", how="left")
```

Стоимость контракта из котировки и стоимости шага:

```python
market = Market("futures")
secid = "GDM6"
securities = market.tickers("minstep", "stepprice")
market_data = market.marketdata("last")

security = securities[securities["ticker"] == secid]
quote = market_data[market_data["ticker"] == secid]
contract_value = (quote["last"].iloc[0] / security["minstep"].iloc[0]) * security["stepprice"].iloc[0]
```

Свёртка часового объёма в дневной:

```python
sber = Ticker("SBER")
candles = sber.candles(start="2025-01-01", end="2025-01-31", period="1h")
candles["begin"] = candles["begin"].astype("datetime64[ns]")
daily_volume = candles.groupby(candles["begin"].dt.date)["volume"].sum()
```

По умолчанию используй DataFrame. Если пользователь явно просит итераторы или словари, упомяни `native=True` как запасной выход.

## Граничные случаи

- Отсутствие данных может означать праздник, неподдерживаемый режим торгов, задержку публикации или недостаточную подписку.
- У некоторых индексов и режимов может быть ограниченный набор интервалов свечей для конкретных дат. Проверяй метаданные и пробуй сырой маршрут ISS, когда значение библиотеки по умолчанию не разрешается.
- `Ticker(...)` разрешается через метаданные ISS и может падать, если тикер делистингован или не основной на запрошенном режиме. Передавай `board=` явно, когда нужно.
