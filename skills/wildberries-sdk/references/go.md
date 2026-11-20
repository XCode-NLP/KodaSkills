# Go

Один модуль на область API:

```bash
go get github.com/eslazarev/wildberries-sdk/clients/go/finances
```

```go
import (
    "context"
    "os"

    finances "github.com/eslazarev/wildberries-sdk/clients/go/finances"
)

client := finances.NewAPIClient(finances.NewConfiguration())

ctx := context.WithValue(context.Background(), finances.ContextAPIKeys,
    map[string]finances.APIKey{"HeaderApiKey": {Key: os.Getenv("WB_API_TOKEN")}})

balance, resp, err := client.DefaultApi.GetV1AccountBalance(ctx).Execute()
```

Поле сервиса соответствует строке `go:` в сводке — обычно `DefaultApi`,
иногда `WBAPIAPI` или `APIAPI`.

## Хост

Уже учтён: сгенерированная карта `OperationServers` привязывает каждую операцию к
её хосту WB. Не трогай `cfg.Servers`. Для песочницы передай индекс сервера операции:

```go
ctx = context.WithValue(ctx, finances.ContextOperationServerIndices,
    map[string]int{"DefaultApiService.GetV1AccountBalance": 1})
```

## Ошибки

`err` — это `*GenericOpenAPIError`; `resp` — сырой `*http.Response`, так что проверяй
`resp.StatusCode` на 429 и делай паузу. `err.Body()` возвращает ответ WB,
который обычно объясняет 400 лучше типизированной модели.

## Вызовы через builder

Параметры выстраиваются в цепочку до `Execute()`:

```go
feedbacks, _, err := client.DefaultApi.GetV1Feedbacks(ctx).
    IsAnswered(false).Take(100).Skip(0).Execute()
```

## Параметр тела запроса

Метод builder, названный по модели:
`.PutV3StocksWarehouseIdRequest(body)` для тела внутри описания,
`.SalesReportListReq(body)`, когда в сводке названа модель, затем `.Execute()`.
