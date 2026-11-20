# Понятия websocket и STOMP в ISS+

Используй этот справочник для общего понимания. Не обещай учётные данные для WebSocket и покрытие, не проверив подписку пользователя и текущий порядок доступа MOEX.

## Эндпоинт и протокол

В локальной документации ISS+ описан как сервис распространения данных в реальном времени по WebSocket с кадрами STOMP:

```text
wss://iss.moex.com/infocx/v3/websocket
```

Команды клиента STOMP:

- `CONNECT`
- `DISCONNECT`
- `SUBSCRIBE`
- `UNSUBSCRIBE`
- `REQUEST`
- `SEND`

Команды сервера:

- `CONNECTED`
- `ERROR`
- `RECEIPT`
- `MESSAGE`
- `REPLY`
- `CLOSED`

## Понятия авторизации

Заголовки `CONNECT` включают:

- `domain`: в локальной документации указаны `DEMO` для гостя и `passport` для подписанных пользователей.
- `login`: логин гостя или аккаунта.
- `passcode`: пароль гостя или аккаунта.
- `language`: необязательный, например `ru` или `en`.

В заметках сообщества в репозитории говорится, что API-ключи могут не работать с WebSocket напрямую и может понадобиться ручной доступ. Считай это зависящим от аккаунта и направляй пользователя к актуальным инструкциям MOEX и DataShop.

## Оговорки по подписке и селекторам

- В локальных вопросах и ответах сказано, что доступ к ISS+ WebSocket может требовать отдельной ручной заявки или привязки аккаунта; одного API-ключа DataShop может не хватить для авторизации.
- Для селекторов FORTS используй значения вида `FORTS.RFUD.{ticker}`, проверив назначение и ресурс в структуре `CONNECTED`.
- В локальных заметках указано, что покрытие FORTS по WebSocket может отдавать `candles` и `securities`, а покрытие акций — `candles`, `securities` и `orderbook`. Не обещай стакан FORTS через ISS+, не проверив текущую структуру и подписку.

## Облик локального клиента Python

В репозитории есть `moexalgo.beta.issplus` с:

- `Credentials(domain, login, passcode)`
- асинхронным контекстным менеджером `connect(url, credentials)`
- `ISSPlusSTOMP.request(destination, selector)`
- `ISSPlusSTOMP.subscribe(destination, selector)`
- `ISSPlusSTOMP.unsubscribe(id)`

Скелет:

```python
import asyncio
from moexalgo.beta.issplus import Credentials, connect

async def main():
    credentials = Credentials(domain="DEMO", login="guest", passcode="guest")
    async with connect("wss://iss.moex.com/infocx/v3/websocket", credentials) as iss:
        print(iss.structure.keys())

asyncio.run(main())
```

## Эксплуатационные заметки

- Ожидай бинарные сообщения WebSocket с данными кадров STOMP.
- Отслеживай последовательность при реализации низкоуровневого клиента.
- Добавляй небольшие паузы между множественными подписками.
- Предпочитай REST для массовой исторической выгрузки, а WebSocket — для потоков текущих данных с малой задержкой.
- Проверяй доступные назначения и селекторы в структуре `CONNECTED` до подписки.
