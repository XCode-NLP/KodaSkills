# Python

```bash
pip install wildberries-sdk
```

Все модули входят в один пакет; импортируй тот, к которому относится операция.

```python
import os
from wildberries_sdk import finances

config = finances.Configuration(api_key={"HeaderApiKey": os.environ["WB_API_TOKEN"]})
api = finances.DefaultApi(finances.ApiClient(config))

balance = api.get_v1_account_balance()
print(balance.data.current)
```

Большинство операций лежит в `DefaultApi`; некоторые — в другом классе (`WBAPIApi`,
`APIApi`). Строка `python:` в сводке называет класс для операции.

## Хост

Настраивать нечего: продакшен-хост вшит в каждый метод. Передай
`_host_index=1`, чтобы попасть в песочницу, где в сводке есть строка `sandbox:` —
индекс позиционный, так что `1` — это всегда песочница, а `0` — продакшен.

```python
api.get_v1_feedbacks(is_answered=False, take=100, skip=0, _host_index=1)
```

## Ошибки

```python
from wildberries_sdk.finances.exceptions import ApiException

try:
    api.get_v1_account_balance()
except ApiException as exc:
    # exc.status — HTTP-код, exc.body — сырой ответ WB
    if exc.status == 429:
        ...  # сделай паузу; лимиты WB считаются на профиль продавца
    raise
```

401 и 403 почти всегда означают токен не из той категории, а не ошибку в коде.

## Параметры и ответы

Параметры запроса — именованные аргументы в snake_case (`is_answered`, `take`,
`skip`); тело запроса — типизированная модель или словарь. Ответы — модели pydantic,
так что обращайся к атрибутам, а не по индексу.

Чтобы получить ответ как простые данные: `result.to_dict()`.

## Параметр тела запроса

Называется по модели, никогда не `body`. `body: SalesReportListReq` в сводке
означает, что ключевой аргумент — `sales_report_list_req`; `body: object` означает, что WB объявил
тело внутри описания, и генератор назвал его по операции, например
`put_v3_stocks_warehouse_id_request`.
