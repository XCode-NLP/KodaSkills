# Node.js и TypeScript

```bash
npm install wildberries-sdk
```

```ts
import { Configuration, DefaultApi } from 'wildberries-sdk';

const api = new DefaultApi(new Configuration({
  basePath: 'https://finance-api.wildberries.ru',   // обязательно — см. ниже
  apiKey: process.env.WB_API_TOKEN!,
}));

const balance = await api.getV1AccountBalance();
```

## Хост: его нужно задать самому

Сгенерированный рантайм по умолчанию берёт `basePath` равным `http://localhost`, и, в отличие от
клиентов Python и Go, он не знает хост конкретной операции. Всегда передавай
`basePath` из строки `host:` сводки для этой операции (или из её строки `sandbox:`),
иначе запрос молча уйдёт в никуда.

Операции одного модуля могут жить на разных хостах — `communications` охватывает
отзывы, чат и возвраты, — поэтому строй по клиенту на хост, а не на модуль.

## Ошибки

Отклонённые запросы выбрасывают `ResponseError` с исходным `response`:

```ts
import { ResponseError } from 'wildberries-sdk';

try {
  await api.getV1AccountBalance();
} catch (err) {
  if (err instanceof ResponseError && err.response.status === 429) {
    // сделай паузу
  }
  throw err;
}
```

## Формы

Методы в camelCase (`getV1Feedbacks`), принимают один объект-аргумент, когда есть параметры,
и возвращают разобранный JSON, типизированный сгенерированными моделями.
Вариант метода с суффиксом `…Raw` возвращает `Response`, когда важны заголовки.

## Параметр тела запроса

Всё идёт одним объектом-аргументом, и ключ тела называется по модели, а не `body`:
`{ warehouseId, putV3StocksWarehouseIdRequest: {...} }` для тела внутри описания,
`{ salesReportListReq: {...} }`, когда в сводке названа модель. WB не проверяет имена полей
в нескольких методах записи — он отвечает `204` и ничего не меняет, — так что неверный ключ падает молча.
