# Справочник по SuperCandles MOEXAlgo

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

`Promo` включает SuperCandles. Доступность на бесплатном токене «Стартовый» запланирована на уровне `T - 1 день`; если пользователи видят `403`, пустые данные, ответы не в JSON или отсутствие строк, проверь текущую подписку и текущие условия DataShop, прежде чем обещать доступ.

## Выбор метода

- `tradestats`: OHLC, VWAP, объём, число сделок, разбивка покупок и продаж, `disb`.
- `orderstats`: выставленные и отменённые заявки, объёмы и стоимости заявок, VWAP потока заявок.
- `obstats`: видимая ликвидность, спреды, уровни, VWAP стакана, дисбаланс.

Рынки: `Market("EQ")`, `Market("FO")`, `Market("FX")`.

## Сигнатуры методов

По всему рынку за дату:

```text
Market(...).tradestats(date=None, latest=None, offset=None, native=False)
Market(...).orderstats(date=None, latest=None, offset=None, native=False)
Market(...).obstats(date=None, latest=None, offset=None, native=False)
```

Один тикер за диапазон дат:

```text
Ticker(...).tradestats(start=None, end=None, latest=None, offset=None, native=False)
Ticker(...).orderstats(start=None, end=None, latest=None, offset=None, native=False)
Ticker(...).obstats(start=None, end=None, latest=None, offset=None, native=False)
```

Передавай даты явно. В текущем коде репозитория пропуск `date` в методах рынка или `start` и `end` в методах тикера приводит к `prepare_from_till_dates(...)`, который выбрасывает исключение, а не молча берёт сегодняшнюю дату.

## Пагинация и большие диапазоны

Используй параметры библиотеки, а не сырые параметры REST. Методы SuperCandles используют `offset`, а не `start`. Методы по всему рынку внутри пагинируют до лимита вызовов рынка в библиотеке; методы тикера используют меньший лимит вызовов тикера. Для больших диапазонов итерируй по датам или диапазонам либо вызывай с растущим `offset`, где это поддержано. Прямой REST бери только когда пользователю нужны сырые средства управления вроде `start` или `limit` конкретного маршрута.

## Примеры

Последние строки по всему рынку:

```python
eq = Market("EQ")
latest_book = eq.obstats(date="2025-01-10", latest=True)
latest_trades = eq.tradestats(date="2025-01-10", latest=True)
```

Диапазон по тикеру:

```python
sber = Ticker("SBER")
df = sber.tradestats(start="2025-01-01", end="2025-01-31")
df["datetime"] = df["tradedate"].astype(str) + " " + df["tradetime"].astype(str)
```

Фьючерсы и валюта:

```python
si = Ticker("SiH5")
si_book = si.obstats(start="2025-01-10", end="2025-01-10")

fx = Market("FX")
fx_orders = fx.orderstats(date="2025-01-10")
```

## Поля TradeStats

- `tradedate`, `tradetime`, `ticker`, `systime`.
- `pr_open`, `pr_high`, `pr_low`, `pr_close`: OHLC за 5 минут.
- `pr_vwap`, `pr_vwap_b`, `pr_vwap_s`: общий VWAP, VWAP покупок и продаж.
- `pr_change`, `pr_std`: изменение цены и волатильность.
- `trades`, `trades_b`, `trades_s`: число сделок.
- `vol`, `vol_b`, `vol_s`: объём.
- `val`, `val_b`, `val_s`: стоимость.
- `disb`: дисбаланс покупок и продаж, положительный при преобладании покупок.

Строки FO могут включать `asset_code`, `im`, `oi_open`, `oi_high`, `oi_low`, `oi_close`.

## Поля OrderStats

- `put_orders_b`, `put_orders_s`, `put_orders`: число выставленных заявок.
- `put_vol_b`, `put_vol_s`, `put_vol`: выставленный объём.
- `put_val_b`, `put_val_s`, `put_val`: выставленная стоимость.
- `put_vwap_b`, `put_vwap_s`: VWAP выставленных заявок.
- `cancel_orders_b`, `cancel_orders_s`, `cancel_orders`: число отменённых заявок.
- `cancel_vol_b`, `cancel_vol_s`, `cancel_vol`: отменённый объём.
- `cancel_val_b`, `cancel_val_s`, `cancel_val`: отменённая стоимость.
- `cancel_vwap_b`, `cancel_vwap_s`: VWAP отменённых заявок.

## Поля OBStats

Основные для акций:

- `spread_bbo`, `spread_lv10`, `spread_1mio`.
- `levels_b`, `levels_s`.
- `vol_b`, `vol_s`, `val_b`, `val_s`.
- `imbalance_vol_bbo`, `imbalance_val_bbo`, `imbalance_vol`, `imbalance_val`.
- `vwap_b`, `vwap_s`, `vwap_b_1mio`, `vwap_s_1mio`.

Строки FO и FX могут включать `mid_price`, `micro_price`, спреды по уровням, накопленные глубины и VWAP по уровням.

## Работа с DataFrame

Строй таблицу или график из полей, которые запросил пользователь. Начни с создания столбца метки времени, когда выводу нужны сортировка или график:

```python
df = Ticker("SBER").tradestats(start="2025-01-01", end="2025-01-31")
df["datetime"] = df["tradedate"].astype(str) + " " + df["tradetime"].astype(str)
```

Для передачи отбирай только запрошенные столбцы:

```python
table = df[["datetime", "ticker", "pr_open", "pr_high", "pr_low", "pr_close", "vol"]]
```

Используй агрегации pandas только когда пользователь просит агрегат:

```python
daily = df.groupby("tradedate", as_index=False).agg(vol=("vol", "sum"), trades=("trades", "sum"))
```

Для ноутбука и скрипта используй графики pandas или Matplotlib, а внутри приложения — уже принятый там стек графиков. Не придумывай панели VWAP, дисбаланса, оборота или ликвидности, если пользователь не просил эти метрики.
