# Повторы, ожидания и согласованность в конечном счёте

Большинство реальных API согласованы в конечном счёте: успешный ответ Create
не означает, что объект готов, виден или вообще уже находится. Провайдеры, которые
это игнорируют, дают нестабильные применения, которые «работают при повторе» — худший вид
сообщения о баге. Этот справочник даёт стандартные приёмы; примитивы
(`retry.StateChangeConf`, `retry.NotFoundError`) берутся из
`github.com/hashicorp/terraform-plugin-sdk/v2/helper/retry` и работают
в провайдерах на Plugin Framework.

## Три класса сбоев

1. **Ещё не видно** — Create вернулся, но немедленный Get даёт 404, потому что
   реплики не сошлись. Решение: кратко повторять ошибки *not-found* сразу
   после создания.
2. **Временно отказано** — API отвергает операцию, потому что зависимость ещё
   не распространилась (политика аутентификации, только что созданный родитель). Решение:
   повторять по *конкретной* ошибке в ограниченном окне.
3. **Асинхронное завершение** — API принимает запрос и работает в
   фоне (поле статуса: `CREATING` → `ACTIVE`). Решение: ожидание, которое
   опрашивает статус до достижения цели.

Определи, какой класс у тебя, до написания кода; решения выглядят похоже, но
повторяют разные условия.

## Ожидания: пары функций статуса и ожидания

Раздели ожидание на функцию *статуса* (один опрос, построенный на поисковике
пакета) и функцию *ожидания* (машина состояний). Разделение делает каждое ожидание
одним очевидным объявлением и позволяет тестам вызывать функцию статуса
напрямую.

```go
const (
    widgetCreatedTimeout = 5 * time.Minute
    widgetDeletedTimeout = 10 * time.Minute
)

func statusWidget(ctx context.Context, client *examplecloud.Client, id string) retry.StateRefreshFunc {
    return func() (any, string, error) {
        output, err := findWidgetByID(ctx, client, id)
        if isNotFound(err) {
            return nil, "", nil // nil result, empty status = "gone"
        }
        if err != nil {
            return nil, "", err
        }
        return output, string(output.Status), nil
    }
}

func waitWidgetCreated(ctx context.Context, client *examplecloud.Client, id string) (*examplecloud.Widget, error) {
    stateConf := &retry.StateChangeConf{
        Pending: []string{"CREATING", "PENDING"},
        Target:  []string{"ACTIVE"},
        Refresh: statusWidget(ctx, client, id),
        Timeout: widgetCreatedTimeout,
    }
    outputRaw, err := stateConf.WaitForStateContext(ctx)
    if output, ok := outputRaw.(*examplecloud.Widget); ok {
        return output, err
    }
    return nil, err
}

func waitWidgetDeleted(ctx context.Context, client *examplecloud.Client, id string) error {
    stateConf := &retry.StateChangeConf{
        Pending: []string{"ACTIVE", "DELETING"},
        Target:  []string{}, // empty target: wait until the status func reports gone
        Refresh: statusWidget(ctx, client, id),
        Timeout: widgetDeletedTimeout,
    }
    _, err := stateConf.WaitForStateContext(ctx)
    return err
}
```

Практические правила:

- **Перечисляй ожидаемые состояния `Pending`**, через которые пройдёт объект; неожиданное
  состояние падает быстро с ясной ошибкой вместо зависания до таймаута. Не включай
  состояния сбоя (`FAILED`, `ERROR`) ни в один список, чтобы они давали ошибку
  сразу, — либо проверяй их в функции статуса и возвращай описательную
  ошибку с причиной сбоя из API.
- **Таймауты в именованных константах**, щедрые, но ограниченные. Если пользователям
  ресурса действительно нужно управление, добавь таймауты уровня схемы.
- Вызывай `waitWidgetCreated` в конце `Create` (а `waitWidgetDeleted`
  в `Delete`), чтобы нижестоящие ресурсы могли полагаться на готовность.

## Повторы not-found после создания

Для сбоев класса 1 (задержка видимости) оберни первое чтение после создания в
краткий повтор not-found, а не в полное ожидание:

```go
const propagationTimeout = 2 * time.Minute

func findWidgetByIDRetryOnCreate(ctx context.Context, client *examplecloud.Client, id string) (*examplecloud.Widget, error) {
    var output *examplecloud.Widget
    err := retry.RetryContext(ctx, propagationTimeout, func() *retry.RetryError {
        var err error
        output, err = findWidgetByID(ctx, client, id)
        if isNotFound(err) {
            return retry.RetryableError(err) // just created: keep looking
        }
        if err != nil {
            return retry.NonRetryableError(err)
        }
        return nil
    })
    return output, err
}
```

Используй это только сразу после создания. В обычном `Read` not-found повторять
*нельзя* — это сигнал убрать ресурс из состояния.

## Повторы ошибок конкретных операций

Для класса 2 повторяй только конкретную, распознаваемую ошибку, в ограниченном
окне:

```go
err := retry.RetryContext(ctx, propagationTimeout, func() *retry.RetryError {
    _, err := client.AttachPolicy(ctx, input)
    var conflictErr *examplecloud.DependencyNotReadyError
    if errors.As(err, &conflictErr) {
        return retry.RetryableError(err)
    }
    if err != nil {
        return retry.NonRetryableError(err)
    }
    return nil
})
```

Никогда не повторяй по *подстрокам сообщения* об ошибке, если SDK даёт типизированные ошибки,
и никогда не повторяй широкие классы («любой 400») — это превращает реальные
ошибки конфигурации в двухминутные зависания с последующим непонятным таймаутом.

## Ожидания значения атрибута при обновлении

Когда само обновление асинхронное (API подтверждает, но поле
читается устаревшим), жди, пока атрибут достигнет запланированного значения, той же формой
StateChangeConf, где значение атрибута — это «статус». Симптомы, что это нужно:
тесты падают на плане обновления после применения с диффом по только что
обновлённому атрибуту.

## Где живёт этот код

Небольшие провайдеры: тот же файл, что и ресурс. Крупные пакеты: `status.go` и
`wait.go` согласно таксономии файлов из основного навыка, чтобы ожидания каждого ресурса
были видны в одном месте.
