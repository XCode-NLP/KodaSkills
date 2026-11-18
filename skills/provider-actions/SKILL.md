---
name: provider-actions
description: "Реализация действий провайдера Terraform на Plugin Framework. Используй при разработке императивных операций, которые выполняются на событиях жизненного цикла (до и после создания, обновления, удаления)."
license: MPL-2.0
metadata:
  author: hashicorp
  source: https://github.com/hashicorp/agent-skills
---

# Руководство по реализации действий провайдера Terraform

## Обзор

Действия Terraform дают императивные операции во время жизненного цикла Terraform. Это экспериментальная возможность, позволяющая выполнять операции провайдера на определённых событиях жизненного цикла (до и после создания, обновления, удаления).

**Ссылки:**
- [Terraform Plugin Framework](https://developer.hashicorp.com/terraform/plugin/framework)
- [Действия в Terraform Plugin Framework](https://developer.hashicorp.com/terraform/plugin/framework/actions)

## Настройка первого действия

Когда в провайдер добавляется первое действие, требуется несколько разовых шагов по созданию каркаса:

1. **Реализуй `ProviderWithActions`** — добавь провайдеру метод `Actions()`, возвращающий `[]func() action.Action`.
2. **Задай `ActionData` в `Configure`** — метод `Configure` провайдера должен задавать `resp.ActionData = v` рядом с существующими присваиваниями `ResourceData`, `DataSourceData` и `EphemeralResourceData`.
3. **Создай базовый тип `ActionWithConfigure`** — если провайдер использует встраиваемые базовые типы (например, `ResourceWithConfigure`), создай эквивалентный тип `ActionWithConfigure`, реализующий `action.ConfigureRequest` и `action.ConfigureResponse`.
4. **Варианты вспомогательных функций схемы действия** — если провайдер внедряет общие атрибуты схемы (например, `namespace`) через вспомогательные функции, нужны варианты для схем действий, поскольку типы `action/schema` отличаются от типов `resource/schema`.

## Структура файлов

Большинство провайдеров держит действия рядом с ресурсами в пакете провайдера:

```
internal/provider/
├── <action_name>_action.go       # Action implementation
└── <action_name>_action_test.go  # Action tests
```

(Крупные мультисервисные провайдеры используют пакеты `internal/service/<service>/` —
следуй структуре целевого репозитория.)

Документация лежит вместе с остальной сгенерированной:

```
docs/actions/
└── <action_name>.md              # User-facing documentation
```

(Некоторые старые крупные провайдеры пишут
`website/docs/actions/<name>.html.markdown` вручную — подстраивайся под репозиторий.)

## Определение схемы действия

Действия используют Terraform Plugin Framework со стандартным шаблоном схемы:

```go
func (a *actionType) Schema(ctx context.Context, req action.SchemaRequest, resp *action.SchemaResponse) {
    resp.Schema = schema.Schema{
        Attributes: map[string]schema.Attribute{
            // Required configuration parameters
            "resource_id": schema.StringAttribute{
                Required:    true,
                Description: "ID of the resource to operate on",
            },
            // Optional parameters with defaults
            "timeout": schema.Int64Attribute{
                Optional:    true,
                Description: "Operation timeout in seconds",
                Default:     int64default.StaticInt64(1800),
                Computed:    true,
            },
        },
    }
}
```

### Частые проблемы схемы

**Обращай особое внимание на определение схемы** — частые проблемы после первого черновика:

1. **Несовпадения типов**
   - Модельные структуры используют `types.String` и `types.Int64`, а схемы — `types.StringType`
     из `github.com/hashicorp/terraform-plugin-framework/types` — не смешивай типы из других пакетов.
   - Некоторые крупные провайдеры надстраивают свой пакет типов (например,
     внутренний `fwtypes` в terraform-provider-aws); внутри такого репозитория
     следуй его соглашению, а не простым типам.

2. **Типы элементов списков и карт**
   ```go
   // WRONG - missing ElementType
   "items": schema.ListAttribute{
       Optional: true,
   }

   // CORRECT
   "items": schema.ListAttribute{
       Optional:    true,
       ElementType: types.StringType,
   }
   ```

3. **Computed и Optional**
   - Атрибуты со значениями по умолчанию должны быть одновременно `Optional: true` и `Computed: true`.
   - Не помечай входные данные действия как `Computed`, если у них нет значений по умолчанию.

4. **Импорты валидаторов**
   ```go
   // Ensure proper imports
   "github.com/hashicorp/terraform-plugin-framework-validators/int64validator"
   "github.com/hashicorp/terraform-plugin-framework-validators/stringvalidator"
   ```

5. **Атрибут региона или провайдера** (мультирегиональные провайдеры, например AWS)
   - Используй общую обработку региона провайдера, если она есть.
   - Не переопределяй вручную конфигурацию уровня провайдера в схеме действия.

6. **Вложенные атрибуты**
   - Используй подходящие типы вложенных объектов для сложных структур.
   - Убедись, что вложенные типы определены правильно.

### Чек-лист проверки схемы

Перед отправкой проверь:
- [ ] У всех атрибутов есть описания
- [ ] У атрибутов списков и карт задан ElementType
- [ ] Валидаторы импортированы и применены правильно
- [ ] Модельная структура использует правильные типы фреймворка
- [ ] Необязательные атрибуты со значениями по умолчанию помечены Computed
- [ ] Код компилируется без ошибок типов
- [ ] Запусти `go build`, чтобы поймать несовпадения типов

## Метод Invoke

Метод Invoke содержит логику действия:

```go
func (a *actionType) Invoke(ctx context.Context, req action.InvokeRequest, resp *action.InvokeResponse) {
    var data actionModel
    resp.Diagnostics.Append(req.Config.Get(ctx, &data)...)
    if resp.Diagnostics.HasError() {
        return
    }

    // a.client was stored by Configure (from req.ProviderData), the same
    // pattern resources use.
    resp.SendProgress(action.InvokeProgressEvent{Message: "Starting operation..."})

    // Implement action logic with error handling
    // Use context for timeout management
    // Poll for completion if async operation

    resp.SendProgress(action.InvokeProgressEvent{Message: "Operation completed"})
}
```

## Ключевые требования к реализации

### 1. Отчёты о ходе выполнения

- Используй `resp.SendProgress(action.InvokeProgressEvent{...})` для обновлений в реальном времени.
- Давай осмысленные сообщения о ходе выполнения во время долгих операций.
- Обновляй прогресс на ключевых этапах.
- Указывай прошедшее время для долгих операций.

### 2. Управление таймаутами

- Всегда добавляй настраиваемый параметр таймаута (по умолчанию 1800 с).
- Используй `context.WithTimeout()` для вызовов API.
- Аккуратно обрабатывай ошибки таймаута.
- Проверяй диапазон таймаута (обычно 60–7200 секунд).

### 3. Обработка ошибок

- Добавляй диагностику через `resp.Diagnostics.AddError()`.
- Давай ясные сообщения об ошибках с контекстом.
- Включай подробности ошибки API, когда это уместно.
- Переводи типы ошибок провайдера в понятные пользователю сообщения.
- Описывай в документации все возможные случаи ошибок.

Пример обработки ошибок:
```go
// Handle specific errors
var notFound *types.ResourceNotFoundException
if errors.As(err, &notFound) {
    resp.Diagnostics.AddError(
        "Resource Not Found",
        fmt.Sprintf("Resource %s was not found", resourceID),
    )
    return
}

// Generic error handling
resp.Diagnostics.AddError(
    "Operation Failed",
    fmt.Sprintf("Could not complete operation for %s: %s", resourceID, err),
)
```

### 4. Интеграция с SDK провайдера

- Используй клиент API, сохранённый при Configure (`a.client`), общий с
  ресурсами и источниками данных.
- Обрабатывай постраничную выдачу в операциях со списками.
- Реализуй повторы для временных сбоев.
- Используй подходящие типы ошибок.

### 5. Проверка параметров

- Используй валидаторы фреймворка для проверки входных данных.
- Проверяй существование ресурса до операций.
- Проверяй конфликтующие параметры.
- Проверяй соответствие требованиям к именованию провайдера.

### 6. Опрос и ожидание

Для операций, требующих ожидания завершения, опрашивай по тикеру под
дедлайном контекста, сообщая о прогрессе по ходу. (Как вариант используй
`retry.StateChangeConf` из
`github.com/hashicorp/terraform-plugin-sdk/v2/helper/retry` — тот же примитив ожидания,
что и у ресурсов.)

```go
ctx, cancel := context.WithTimeout(ctx, timeout)
defer cancel()

ticker := time.NewTicker(5 * time.Second)
defer ticker.Stop()

// Poll fast, report slow: progress events cross the plugin protocol, so
// throttle them instead of emitting one per poll.
start := time.Now()
var lastProgress time.Time
for {
    res, err := findResource(ctx, a.client, id)
    if err != nil {
        resp.Diagnostics.AddError("Error polling operation", fmt.Sprintf("checking status of %s: %s", id, err))
        return
    }
    switch res.Status {
    case "AVAILABLE", "COMPLETED":
        resp.SendProgress(action.InvokeProgressEvent{Message: "Operation completed"})
        return
    case "CREATING", "PENDING":
        if time.Since(lastProgress) >= 30*time.Second {
            lastProgress = time.Now()
            resp.SendProgress(action.InvokeProgressEvent{
                Message: fmt.Sprintf("Status: %s, Elapsed: %v", res.Status, time.Since(start).Round(time.Second)),
            })
        }
    default:
        resp.Diagnostics.AddError("Operation Failed", fmt.Sprintf("%s entered unexpected status %q", id, res.Status))
        return
    }

    select {
    case <-ctx.Done():
        resp.Diagnostics.AddError("Operation Timed Out", fmt.Sprintf("%s did not complete within %v", id, timeout))
        return
    case <-ticker.C:
    }
}
```

## Частые приёмы для действий

### Пакетные операции
- Обрабатывай элементы пакетами настраиваемого размера.
- Сообщай о прогрессе по каждому пакету.
- Аккуратно обрабатывай частичные сбои.
- Поддерживай параметры префикса и фильтра.

### Выполнение команд
- Отправь команду и получи идентификатор операции.
- Опрашивай статус завершения.
- Получи и сообщи вывод.
- Обрабатывай таймаут во время опроса.
- Проверяй существование ресурсов перед выполнением.

### Вызов сервиса
- Вызови сервис с параметрами.
- Дождись завершения (если операция синхронная).
- Верни вывод или результаты.
- Обрабатывай ошибки, специфичные для сервиса.

### Изменение состояния ресурса
- Проверь текущее состояние.
- Примени изменение состояния.
- Опрашивай целевое состояние.
- Обрабатывай промежуточные состояния.

### Отправка асинхронной задачи
- Отправь задачу с конфигурацией.
- Получи идентификатор задачи.
- По желанию дождись завершения.
- Сообщи статус задачи.

## Триггеры действий

Действия вызываются через блоки жизненного цикла `action_trigger` в конфигурациях Terraform. Отдельный блок `action` без соответствующего триггера объявлен, но никогда не выполняется.

### Синтаксис HCL

Параметры действия должны быть обёрнуты в блок `config {}`. Ссылки на триггер используют префикс `action.`, а `actions` — это список. События — это простые идентификаторы, а не строки в кавычках.

```hcl
action "provider_service_action" "name" {
  config {
    parameter = value
  }
}

resource "terraform_data" "trigger" {
  lifecycle {
    action_trigger {
      events  = [after_create]
      actions = [action.provider_service_action.name]
    }
  }
}
```

### Доступные события триггера

**Поддерживаемые события (на момент Terraform 1.14):**
- `before_create` — до создания ресурса;
- `after_create` — после создания ресурса;
- `before_update` — до обновления ресурса;
- `after_update` — после обновления ресурса.

**Не поддерживаются (на момент Terraform 1.14; сверяйся с текущими заметками о выпуске):**
- `before_destroy` — недоступно (даёт ошибку валидации);
- `after_destroy` — недоступно (даёт ошибку валидации).

## Тестирование действий

### Приёмочные тесты

- Проверь вызов действия с валидными параметрами.
- Проверь сценарии таймаута.
- Проверь условия ошибок.
- Проверь изменения состояния провайдера.
- Проверь отчёты о ходе выполнения.
- Проверь с собственными параметрами.
- Проверь вызов через триггер.

### Шаблон теста

```go
func TestAccExampleAction_basic(t *testing.T) {
    resource.ParallelTest(t, resource.TestCase{
        PreCheck:                 func() { testAccPreCheck(t) },
        ProtoV6ProviderFactories: testAccProtoV6ProviderFactories,
        TerraformVersionChecks: []tfversion.TerraformVersionCheck{
            tfversion.SkipBelow(tfversion.Version1_14_0),
        },
        Steps: []resource.TestStep{
            {
                Config: testAccActionConfig_basic(),
                ConfigStateChecks: []statecheck.StateCheck{
                    // assert the observable effect of the action on the
                    // triggering resource
                },
            },
        },
    })
}
```

### Очистка тестов через sweep-функции

Действия, вызванные в тестах, могут оставлять настоящие ресурсы; регистрируй уборщики
(перечисли → отфильтруй имена с тестовым префиксом → удали), чтобы утёкшие ресурсы можно было
убрать. Уборщики не специфичны для действий — используй
навык `provider-test-patterns` (если доступен) для шаблона sweep-функции,
регистрации, `TestMain` и порядка зависимостей.

### Использование `terraform_data` как пустого триггера

`terraform_data` может служить пустым триггерным ресурсом для тестов действий, которым не нужна настоящая инфраструктура. Это ценно для тестов ошибок и валидации:

```hcl
resource "terraform_data" "trigger" {
  lifecycle {
    action_trigger {
      events  = [after_create]
      actions = [action.provider_service_action.test]
    }
  }
}

action "provider_service_action" "test" {
  config {
    param = "invalid-value"
  }
}
```

### Использование `PostApplyFunc` для проверки побочных эффектов

Действия не создают состояние, которое можно проверить через `resource.TestCheckResourceAttr`. Используй `PostApplyFunc` в `resource.TestStep`, чтобы запросить API после применения и подтвердить, что действие дало ожидаемый побочный эффект:

```go
Steps: []resource.TestStep{
    {
        Config: testConfig,
        PostApplyFunc: func() {
            // query the API to verify the action's side effect occurred
        },
    },
},
```

### Рекомендации по тестированию

**Предусловия конкретного сервиса**
- Всегда проверяй предусловия конкретного сервиса, которые должны быть выполнены, чтобы действия могли завершиться успешно.
- Описывай предусловия в документации действия и тестовых конфигурациях.

**Сопоставление шаблонов ошибок**
- Terraform оборачивает ошибки действий дополнительным контекстом.
- Используй гибкие регулярные выражения: `regexp.MustCompile(\`(?s)Error Title.*key phrase\`)`.

**Приёмы тестирования, неприменимые к действиям**
1. Действия срабатывают на события жизненного цикла, а не на повторное применение конфигурации.
2. Тесты до и после уничтожения: не поддерживаются на момент Terraform 1.14.

### Запуск тестов

Сначала проверь компиляцию, затем запусти нужный приёмочный тест:
```bash
go test -c -o /dev/null ./internal/provider
TF_ACC=1 go test ./internal/provider -run TestAccExampleAction_ -timeout 60m
```

Используй навык `run-acceptance-tests` (если доступен) для настройки
переменных окружения, отладки падающих тестов и запуска уборщиков.

## Стандарты документации

Генерируй документацию действий через `tfplugindocs`, где провайдер его
использует (для этого порядка работы используй навык `provider-docs`, если доступен). Каждая
страница документации действия должна включать:

1. **Front matter** (только для ручных старых макетов)
   ```yaml
   ---
   subcategory: "Service Name"
   layout: "provider"
   page_title: "Provider: provider_service_action"
   description: |-
     Brief description of what the action does.
   ---
   ```

2. **Заголовок с предупреждениями**
   - уведомление о статусе beta или alpha;
   - предупреждение о возможных непреднамеренных последствиях;
   - ссылка на документацию провайдера.

3. **Пример использования**
   - базовый пример;
   - продвинутый пример со всеми опциями;
   - пример с триггером через `terraform_data`;
   - примеры реальных сценариев.

4. **Справочник аргументов**
   - перечисли все обязательные и необязательные аргументы;
   - укажи описания и значения по умолчанию;
   - отметь правила валидации.

5. **Линтинг документации** (необязательный инструментарий)
   - Если репозиторий использует `terrafmt`, запусти `terrafmt fmt` перед отправкой и
     проверь через `terrafmt diff`.

## Формат записи в журнале изменений (соглашение конкретного провайдера)

Некоторые провайдеры (например, terraform-provider-aws) ведут заметки о выпуске через
[go-changelog](https://github.com/hashicorp/go-changelog): один файл на pull request
в директории `.changelog/`. Смотри CONTRIBUTING целевого репозитория;
пропусти этот раздел, если репозиторий его не использует.

```
.changelog/<pr_number>.txt
```

Формат содержимого:
```release-note:new-action
action/provider_service_action: Brief description of the action
```

## Чек-лист перед отправкой

Перед отправкой реализации действия:

- [ ] Код компилируется: `go build -o /dev/null .`
- [ ] Тесты компилируются: `go test -c -o /dev/null ./internal/provider`
- [ ] Код отформатирован: `gofmt` (или `make fmt` репозитория)
- [ ] Документация сгенерирована или отформатирована по соглашению репозитория
- [ ] Создана запись в журнале изменений (если репозиторий его использует)
- [ ] Схема использует правильные типы
- [ ] У всех атрибутов списков и карт задан ElementType
- [ ] Для долгих операций реализованы обновления прогресса
- [ ] Сообщения об ошибках содержат контекст и идентификаторы ресурсов
- [ ] В документации несколько примеров
- [ ] В документации есть предусловия и предупреждения

## Ссылки

- [Документация Terraform Plugin Framework](https://developer.hashicorp.com/terraform/plugin/framework)
- [Разработка провайдера Terraform](https://developer.hashicorp.com/terraform/plugin)
- [terraform-plugin-framework на GitHub](https://github.com/hashicorp/terraform-plugin-framework)
- [terraform-plugin-testing](https://github.com/hashicorp/terraform-plugin-testing)
- [Writing a Terraform Action (блог)](https://danielmschmidt.de/posts/2025-09-26-writing-a-terraform-action/)
- Эталонные реализации: `terraform-provider-tfe` (`action_query_run.go`, `action_query_run_test.go`), `terraform-provider-vault` (`action_rotate_root.go`)
