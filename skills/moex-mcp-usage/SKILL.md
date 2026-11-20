---
name: moex-mcp-usage
description: "Правила вызова инструментов MOEX MCP-сервера: форматы дат и массивов, лимит свечей, коды рынков, авторизация и разбор ошибок. Используй при работе с MOEX MCP: свечи, сделки, стакан, статистика, фьючерсы и опционы, FUTOI, HI2 и оповещения."
license: MIT
metadata:
  author: hdworker
  source: https://github.com/hdworker/ru-moex-mcp
---

# Правила работы с MOEX MCP

Правила корректного вызова инструментов MOEX MCP-сервера. Собраны по реальным ошибкам — соблюдай их, чтобы вызовы не падали.

## Основные правила

### 1. Формат даты: только `YYYY-MM-DD`

**Все аргументы-даты** (`start`, `end`, `date`) во ВСЕХ инструментах должны быть строками только с датой:

```
✅ "2026-06-04"
❌ "2026-06-04 14:00:00"     → Invalid isoformat string
❌ "2026-06-04T14:00:00"     → Invalid isoformat string
❌ "04.06.2026"              → Invalid isoformat string
❌ "June 4, 2026"            → Invalid isoformat string
```

Это относится к:

- `moex_get_ticker_candles` — `start`, `end`
- `moex_get_ticker_tradestats` — `start`, `end`
- `moex_get_ticker_orderstats` — `start`, `end`
- `moex_get_ticker_obstats` — `start`, `end`
- `moex_get_ticker_futoi` — `start`, `end`
- `moex_get_ticker_hi2` — `start`, `end`
- `moex_get_ticker_alerts` — `start`, `end`
- `moex_get_market_tradestats` — `date`
- `moex_get_market_orderstats` — `date`
- `moex_get_market_obstats` — `date`
- `moex_get_market_futoi` — `date`
- `moex_get_market_hi2` — `date`
- `moex_get_market_alerts` — `date`

### 2. Параметр `fields`: нативный массив JSON, а не строка

Если инструмент принимает `fields: list[str] | None`, передавай **нативный массив**:

```json
✅ ["SECID", "SHORTNAME", "LOTSIZE"]
❌ "[\"SECID\", \"SHORTNAME\", \"LOTSIZE\"]"   → Input should be a valid list
❌ "SECID,SHORTNAME,LOTSIZE"                   → неверный тип
```

Это относится к:

- `moex_list_securities` — `fields`
- `moex_get_market_marketdata` — `fields`

### 3. Лимит свечей: не более 500 за вызов

`moex_get_ticker_candles` возвращает **максимум 500 свечей**. Ключевое поведение:

| Сценарий | Результат |
|----------|-----------|
| Широкий диапазон дат + `latest=false` | Возвращает 500 самых старых свечей диапазона (может быть пусто или далеко от нужных дат) |
| Широкий диапазон дат + `latest=true` | Возвращает 500 самых новых свечей (обычно это и нужно) |
| Узкий диапазон (меньше 500 свечей) | Возвращает все свечи диапазона |

**Правило:** всегда используй `latest=true`, если только тебе не нужны исторические данные именно с начала диапазона.

### 4. Определение рынка

Если не уверен в названии рынка, вызови `moex_resolve_market` либо используй эти канонические названия напрямую:

| Псевдоним | Каноническое имя | Режим торгов |
|-------|-----------|-------|
| `EQ`, `shares`, `stocks` | `shares` | TQBR |
| `FO`, `forts`, `futures` | `forts` | RFUD |
| `FX`, `selt`, `currency` | `selt` | CETS |
| `bonds` | `bonds` | TQOB |
| `index` | `index` | SNDX |
| `options` | `options` | ROPD |

### 5. Периоды свечей

Допустимые строки периода (регистр важен):

```
1min, 5min, 10min, 15min, 20min, 30min
1h, 2h, 3h, 6h, 12h
1D, 5D, 10D
1W, 2W, 4W
1M
```

### 6. Требования авторизации

| Уровень авторизации | Инструменты |
|------------|-------|
| **Без авторизации** (публичный ISS) | `moex_list_engines`, `moex_list_markets`, `moex_resolve_market`, `moex_get_ticker_info` |
| **Нужен токен ALGOPACK** | Все остальные инструменты (свечи, marketdata, стакан, сделки, статистика, оповещения, futoi, hi2, календарь) |

Если инструмент вернул `{"status": "error", "kind": "auth"}`, значит `MOEXALGO_TOKEN` отсутствует или неверен.

### 7. Формат ответа

Все инструменты возвращают **строку JSON**. Сначала разбери её:

```json
// Успех
{"market": "shares", "board": null, "candles": [...]}

// Ошибка
{"status": "error", "op": "moex_get_ticker_candles", "kind": "broker", "error": "..."}
```

Значения `kind` у ошибок:

- `auth` — токен ALGOPACK отсутствует или неверен;
- `rate_limit` — HTTP 429, сделай паузу и повтори;
- `transport` — ошибка сети или таймаут;
- `broker` — ошибка moexalgo (неверные аргументы, пустой ответ и т. п.);
- `internal` — непредвиденная ошибка.

## Типовые сценарии

### Самые ликвидные акции

```
1. moex_get_market_marketdata(market="EQ", fields=["SECID", "VALTODAY", "VOLTODAY", "LAST", "LASTCHANGEPRCNT"])
2. Отсортируй по VALTODAY по убыванию
3. Возьми первые 3–10
```

### Внутридневные свечи по акции

```
moex_get_ticker_candles(
  secid="SBER",
  start="2026-06-04",
  end="2026-06-04",
  period="1min",
  latest=true
)
```

Учти: свечи включают вечернюю сессию (14:00–23:50 МСК).

### Снимок стакана

```
moex_get_ticker_orderbook(secid="SBER")
```

### Последние сделки

```
moex_get_ticker_trades(secid="SBER")
```

## Чего не делать

1. **Не** передавай строки с датой и временем в поля-даты — moexalgo принимает только `YYYY-MM-DD`.
2. **Не** передавай JSON-строки в `fields` — используй нативные массивы.
3. **Не** считай, что свечи покрывают весь торговый день — moexalgo отдаёт то, что есть, но не больше 500.
4. **Не** забывай `latest=true` для свежих свечей.
5. **Не** используй `moex_get_market_candles` для истории по инструменту — он отдаёт только 2 последние минутные свечи по каждому инструменту; для истории нужен `moex_get_ticker_candles`.
6. **Не** передавай `board`, если бумага не торгуется в нескольких режимах — параметр необязательный и обычно не нужен.
