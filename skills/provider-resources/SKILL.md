---
name: provider-resources
description: "Реализация ресурсов и источников данных провайдера Terraform на Plugin Framework: операции CRUD, проектирование схемы, модификаторы плана и валидаторы, обработка отсутствия объекта, ожидание для API с согласованностью в конечном счёте, поддержка импорта, принципы проектирования ресурсов и обязательное покрытие приёмочными тестами. Используй при добавлении или изменении ресурса либо источника данных, при решении, должен ли концепт API быть ресурсом, при подключении ресурса к настроенному клиенту провайдера, при работе с расхождением состояния и отсутствием ресурса, а также при проверке реализации ресурса перед отправкой."
license: MPL-2.0
metadata:
  author: hashicorp
  source: https://github.com/hashicorp/agent-skills
---

# Руководство по реализации ресурсов провайдера Terraform

## Обзор

Это руководство покрывает разработку ресурсов и источников данных провайдера Terraform.
Ресурсы представляют объекты инфраструктуры, которыми Terraform управляет через
операции Create, Read, Update и Delete (CRUD).

**Используй [Plugin Framework](https://developer.hashicorp.com/terraform/plugin/framework)
для всех новых ресурсов и источников данных.** Plugin SDKv2 — для поддержки
ресурсов, которые уже на нём написаны; не пиши новый код на нём. Провайдер
может обслуживать оба во время переноса через мультиплексирование
([terraform-plugin-mux](https://developer.hashicorp.com/terraform/plugin/mux)),
поэтому переход на Framework никогда не требует переписывания всего сразу. Чтобы понять,
в каком режиме существующий провайдер, посмотри `go.mod`: наличие `terraform-plugin-mux`
значит, что он обслуживает и SDKv2, и Framework; только
`terraform-plugin-sdk/v2` значит только SDKv2; только
`terraform-plugin-framework` значит только Framework. Будь осторожен с
*переносом* существующих ресурсов SDKv2: Framework различает null и
нулевые значения, поэтому наивный перенос меняет поведение для существующих пользователей (используй
навык `provider-framework-migration`, если доступен).

**Справочники** (загружай по необходимости):
- `references/design-principles.md` — что должно (и не должно) становиться
  ресурсом; семантика источников данных; моделирование связей и асинхронных задач;
- `references/retries-and-waiters.md` — согласованность в конечном счёте, приёмы
  повторов и структура функций статуса и ожидания.

## Структура файлов

Большинство провайдеров держит каждый ресурс в одном пакете:

```
internal/provider/
├── provider.go                  # Provider schema + Configure
├── widget_resource.go           # Resource implementation
├── widget_resource_test.go      # Acceptance tests
├── widget_data_source.go        # Data source (if applicable)
└── widget_data_source_test.go
```

Крупные мультисервисные провайдеры (например, terraform-provider-aws) делят код на
пакеты `internal/service/<service>/`, и стоит перенять идиоматичную таксономию файлов,
когда пакет разрастается: `consts.go`, `find.go`
(поисковики), `status.go` (функции статуса), `wait.go` (ожидания), `sweep.go`
(уборщики тестов), `exports_test.go`.

Документация живёт в `docs/` и генерируется через `tfplugindocs`:

```
docs/
├── resources/<name>.md          # generated; optional <name>.md.tmpl template
└── data-sources/<name>.md
```

(Написанные вручную деревья `website/docs/r/*.html.markdown` есть в некоторых старых
крупных провайдерах — следуй соглашениям целевого репозитория, когда правишь такой.)

## Структура ресурса

Ресурс Framework — это структура, хранящая клиент API, с утверждениями интерфейсов,
делающими реализуемое поведение явным:

```go
var (
    _ resource.Resource                = &widgetResource{}
    _ resource.ResourceWithConfigure   = &widgetResource{}
    _ resource.ResourceWithImportState = &widgetResource{}
)

func NewWidgetResource() resource.Resource {
    return &widgetResource{}
}

type widgetResource struct {
    client *examplecloud.Client
}

func (r *widgetResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
    resp.TypeName = req.ProviderTypeName + "_widget"
}

// Configure receives the client the provider built in its own Configure.
func (r *widgetResource) Configure(_ context.Context, req resource.ConfigureRequest, resp *resource.ConfigureResponse) {
    if req.ProviderData == nil {
        return // provider not yet configured (e.g. validation phase)
    }
    client, ok := req.ProviderData.(*examplecloud.Client)
    if !ok {
        resp.Diagnostics.AddError(
            "Unexpected Resource Configure Type",
            fmt.Sprintf("Expected *examplecloud.Client, got: %T.", req.ProviderData),
        )
        return
    }
    r.client = client
}

func (r *widgetResource) Schema(ctx context.Context, req resource.SchemaRequest, resp *resource.SchemaResponse) {
    resp.Schema = schema.Schema{
        Attributes: map[string]schema.Attribute{
            "name": schema.StringAttribute{
                Required: true,
                PlanModifiers: []planmodifier.String{
                    stringplanmodifier.RequiresReplace(),
                },
                Validators: []validator.String{
                    stringvalidator.LengthBetween(1, 255),
                },
            },
            "id": schema.StringAttribute{
                Computed: true,
                PlanModifiers: []planmodifier.String{
                    stringplanmodifier.UseStateForUnknown(),
                },
            },
        },
    }
}
```

Как `Configure` провайдера создаёт этого клиента — схема, поиск учётных данных,
проверка — покрыто навыком `provider-configuration` (если доступен).

**Про `id`:** SDKv2 требовал магический атрибут `id`; Framework — нет.
Если у API есть собственный идентификатор, открывай его под его настоящим смыслом и
не добавляй второй, избыточный `id`. Оставляй `id` только когда он *и есть*
идентификатор API (как выше).

## Операции CRUD

### Create

```go
func (r *widgetResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
    var data widgetResourceModel
    resp.Diagnostics.Append(req.Plan.Get(ctx, &data)...)
    if resp.Diagnostics.HasError() {
        return
    }

    input := &examplecloud.CreateWidgetInput{
        Name: data.Name.ValueStringPointer(),
    }

    output, err := r.client.CreateWidget(ctx, input)
    if err != nil {
        resp.Diagnostics.AddError(
            "Error creating Widget",
            fmt.Sprintf("creating Widget (%s): %s", data.Name.ValueString(), err),
        )
        return
    }

    data.ID = types.StringPointerValue(output.ID)

    // For eventually consistent APIs, wait for the resource to be usable
    // before returning — see references/retries-and-waiters.md.

    resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}
```

### Read

Read должен обрабатывать удаление вне Terraform, убирая ресурс из состояния, чтобы
следующий план пересоздал его, а не падал бесконечно:

```go
func (r *widgetResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
    var data widgetResourceModel
    resp.Diagnostics.Append(req.State.Get(ctx, &data)...)
    if resp.Diagnostics.HasError() {
        return
    }

    output, err := findWidgetByID(ctx, r.client, data.ID.ValueString())
    if isNotFound(err) {
        tflog.Warn(ctx, "Widget not found, removing from state", map[string]any{"id": data.ID.ValueString()})
        resp.State.RemoveResource(ctx)
        return
    }
    if err != nil {
        resp.Diagnostics.AddError(
            "Error reading Widget",
            fmt.Sprintf("reading Widget (%s): %s", data.ID.ValueString(), err),
        )
        return
    }

    data.Name = types.StringPointerValue(output.Name)

    resp.Diagnostics.Append(resp.State.Set(ctx, &data)...)
}
```

### Update

Вызывай API только для атрибутов, которые действительно изменились; сравнивай план
с состоянием:

```go
func (r *widgetResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
    var plan, state widgetResourceModel
    resp.Diagnostics.Append(req.Plan.Get(ctx, &plan)...)
    resp.Diagnostics.Append(req.State.Get(ctx, &state)...)
    if resp.Diagnostics.HasError() {
        return
    }

    if !plan.Description.Equal(state.Description) {
        input := &examplecloud.UpdateWidgetInput{
            ID:          plan.ID.ValueStringPointer(),
            Description: plan.Description.ValueStringPointer(),
        }
        if _, err := r.client.UpdateWidget(ctx, input); err != nil {
            resp.Diagnostics.AddError(
                "Error updating Widget",
                fmt.Sprintf("updating Widget (%s): %s", plan.ID.ValueString(), err),
            )
            return
        }
    }

    resp.Diagnostics.Append(resp.State.Set(ctx, &plan)...)
}
```

### Delete

Считай «уже нет» успехом — нужное конечное состояние достигнуто:

```go
func (r *widgetResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
    var data widgetResourceModel
    resp.Diagnostics.Append(req.State.Get(ctx, &data)...)
    if resp.Diagnostics.HasError() {
        return
    }

    _, err := r.client.DeleteWidget(ctx, &examplecloud.DeleteWidgetInput{
        ID: data.ID.ValueStringPointer(),
    })
    if isNotFound(err) {
        return
    }
    if err != nil {
        resp.Diagnostics.AddError(
            "Error deleting Widget",
            fmt.Sprintf("deleting Widget (%s): %s", data.ID.ValueString(), err),
        )
        return
    }
}
```

### Импорт

Когда утверждён `ResourceWithImportState`, передача идентификатора без изменений —
одна строка:

```go
func (r *widgetResource) ImportState(ctx context.Context, req resource.ImportStateRequest, resp *resource.ImportStateResponse) {
    resource.ImportStatePassthroughID(ctx, path.Root("id"), req, resp)
}
```

Для составных идентификаторов разбирай разделённый ID импорта (обычно через запятую)
и задавай каждый атрибут явно.

## Принципы проектирования ресурсов

Прежде чем реализовывать, проверь форму моделируемой сущности (полностью —
в `references/design-principles.md`):

- Ресурс — *наименьший* полезный строительный блок; если API даёт для него
  CRUD, он, вероятно, заслуживает собственного ресурса.
- Ресурс должен обращаться только к **одному** API или сервису — кросс-сервисные
  ресурсы ломают права, аудит и настройку эндпоинтов.
- Источники данных только читают и не имеют побочных эффектов. *Единичный* источник данных
  падает при нуле или нескольких совпадениях; *множественный* источник данных (имя во множественном
  числе) возвращает ноль или больше как коллекцию и не падает ни в одном случае.
- Прикреплённые политики и правила, вызовы долгих задач и версионируемые
  артефакты обычно заслуживают *собственных* ресурсов, а не атрибутов у
  родителя.
- Состояние «запущено/остановлено» или «включено/выключено» относится атрибутом *внутри*
  ресурса, а не отдельным ресурсом.

## Проектирование схемы

### Типы атрибутов

| Тип Terraform | Тип Framework | Сценарий использования |
|----------------|----------------|----------------|
| `string` | `schema.StringAttribute` | Имена, идентификаторы |
| `number` | `schema.Int64Attribute`, `schema.Float64Attribute` | Счётчики, размеры |
| `bool` | `schema.BoolAttribute` | Флаги возможностей |
| `list` | `schema.ListAttribute` | Упорядоченные коллекции |
| `set` | `schema.SetAttribute` | Неупорядоченные уникальные элементы |
| `map` | `schema.MapAttribute` | Пары ключ-значение |
| `object` | `schema.SingleNestedAttribute` | Сложная вложенная конфигурация |

Дай каждому атрибуту `MarkdownDescription` — `tfplugindocs` его публикует,
и это основная документация для пользователя.

### Модификаторы плана

```go
// Force replacement when value changes
stringplanmodifier.RequiresReplace()

// Keep a known value during plan instead of (known after apply)
stringplanmodifier.UseStateForUnknown()
```

### Валидаторы

```go
stringvalidator.LengthBetween(1, 255)
stringvalidator.RegexMatches(regexp.MustCompile(`^[a-z0-9-]+$`), "must be lowercase alphanumeric with hyphens")
stringvalidator.OneOf("small", "medium", "large")
int64validator.Between(1, 100)
listvalidator.SizeAtLeast(1)
```

### Чувствительные атрибуты

```go
"password": schema.StringAttribute{
    Required:  true,
    Sensitive: true,
},
```

## Управление состоянием

### Поисковики

Централизуй «получить один объект или типизированное not-found» в поисковике, чтобы Read, Delete,
ожидания и тесты делили одинаковую семантику отсутствия:

```go
func findWidgetByID(ctx context.Context, client *examplecloud.Client, id string) (*examplecloud.Widget, error) {
    output, err := client.GetWidget(ctx, &examplecloud.GetWidgetInput{ID: &id})
    if err != nil {
        var apiErr *examplecloud.NotFoundError
        if errors.As(err, &apiErr) {
            return nil, &retry.NotFoundError{LastError: err}
        }
        return nil, fmt.Errorf("getting Widget (%s): %w", id, err)
    }
    if output == nil || output.Widget == nil {
        return nil, &retry.NotFoundError{Message: "empty result"}
    }
    return output.Widget, nil
}

func isNotFound(err error) bool {
    var nfe *retry.NotFoundError
    return errors.As(err, &nfe)
}
```

### Ожидание состояний ресурса

Многие API возвращаются из Create или Delete раньше, чем ресурс стал пригоден или исчез. Используй
`retry.StateChangeConf` (из
`github.com/hashicorp/terraform-plugin-sdk/v2/helper/retry` — работает и в
провайдерах на Framework), с функцией статуса на основе поисковика и
таймаутами в именованных константах:

```go
stateConf := &retry.StateChangeConf{
    Pending: []string{"CREATING", "PENDING"},
    Target:  []string{"ACTIVE"},
    Refresh: statusWidget(ctx, r.client, id), // one poll of the finder: (obj, status, err)
    Timeout: widgetCreatedTimeout,
}
outputRaw, err := stateConf.WaitForStateContext(ctx)
```

Полные пары функций статуса и ожидания (ожидания создания и удаления, обработка
состояний сбоя, повторные проверки отсутствия после создания, приёмы для согласованности
в конечном счёте) — в `references/retries-and-waiters.md`; читай его всякий раз, когда API
асинхронный или согласован в конечном счёте.

## Тестирование

Каждый ресурс поставляется как минимум с:

- **`_basic`** — создание с минимальной конфигурацией, проверка атрибутов, затем шаг
  импорта (`ImportState: true`, `ImportStateVerify: true`);
- **`_disappears`** — удаление объекта вне Terraform посреди теста; следующий план
  должен предложить пересоздание, а не упасть;
- **тестами по каждому атрибуту** — проверка обновлений для каждого нетривиального аргумента.

Грамматика имён: тесты `TestAcc{Resource}_{group?}_{description}`, вспомогательные функции
`testAccCheck{Resource}Exists` и `testAccCheck{Resource}Destroy`, функции конфигурации
`testAcc{Resource}Config_{description}`. Держи конфигурации
самодостаточными, рандомизируй настоящие имена ресурсов и никогда не вшивай
значения, специфичные для окружения (идентификаторы аккаунтов, зоны, версии).

```go
func TestAccWidget_basic(t *testing.T) {
    rName := acctest.RandStringFromCharSet(10, acctest.CharSetAlphaNum)
    resourceName := "examplecloud_widget.test"

    resource.ParallelTest(t, resource.TestCase{
        PreCheck:                 func() { testAccPreCheck(t) },
        ProtoV6ProviderFactories: testAccProtoV6ProviderFactories,
        CheckDestroy:             testAccCheckWidgetDestroy,
        Steps: []resource.TestStep{
            {
                Config: testAccWidgetConfig_basic(rName),
                ConfigStateChecks: []statecheck.StateCheck{
                    statecheck.ExpectKnownValue(resourceName, tfjsonpath.New("name"), knownvalue.StringExact(rName)),
                    statecheck.ExpectKnownValue(resourceName, tfjsonpath.New("id"), knownvalue.NotNull()),
                },
            },
            {
                ResourceName:      resourceName,
                ImportState:       true,
                ImportStateVerify: true,
            },
        },
    })
}

func testAccWidgetConfig_basic(rName string) string {
    return fmt.Sprintf(`
resource "examplecloud_widget" "test" {
  name = %[1]q
}
`, rName)
}
```

Используй навык `provider-test-patterns` (если доступен) для полного освещения
тестирования: стиль вспомогательных функций конфигурации (индексированные глаголы `%[1]q`), statecheck и plancheck,
CompareValue, собственные реализации StateCheck для вспомогательных функций exists и disappears,
уборщики и тестирование эфемерных ресурсов. Используй навык
`run-acceptance-tests` для запуска и отладки тестов.

## Обработка ошибок

Сопоставляй ошибки API по типу, а не по тексту сообщения, и оборачивай с контекстом:

```go
var notFound *examplecloud.NotFoundError
if errors.As(err, &notFound) {
    // resource doesn't exist
}

// Wrapping inside helpers: preserve the cause with %w
return fmt.Errorf("creating Widget (%s): %w", name, err)
```

Диагностика следует единой грамматике — сводка называет операцию и
тип, подробность несёт идентификатор и причину:

```go
resp.Diagnostics.AddError(
    "Error creating Widget",
    fmt.Sprintf("creating Widget (%s): %s", name, err),
)

resp.Diagnostics.AddAttributeError(
    path.Root("name"),
    "Invalid name",
    "Name must be lowercase alphanumeric",
)
```

## Документация

Сначала напиши `MarkdownDescription` атрибутов — они источник
истины. Затем сгенерируй документацию для Registry через `tfplugindocs`
(`go generate ./...`, где это настроено), добавляя шаблоны `docs/**/*.md.tmpl`
только для прозы и примеров, которые генератор не может вывести. Используй
навык `provider-docs` (если доступен) для полного порядка работы с документацией и
правил публикации в Registry.

## Чек-лист перед отправкой

- [ ] Используется Plugin Framework (никакого нового кода на SDKv2)
- [ ] Реализованы все операции CRUD
- [ ] Read убирает отсутствующие ресурсы из состояния; Delete терпит уже удалённые
- [ ] Нет избыточного атрибута `id` (открыт настоящий идентификатор API)
- [ ] Импорт реализован и покрыт шагом `ImportStateVerify`
- [ ] Есть тесты `_basic`, `_disappears` и по каждому атрибуту
- [ ] Ожидания используются там, где API согласован в конечном счёте
- [ ] Сообщения об ошибках называют операцию, тип и идентификатор
- [ ] Чувствительные атрибуты помечены; у каждого атрибута есть описание
- [ ] Документация сгенерирована через `tfplugindocs`
- [ ] Добавлена запись в журнал изменений, если репозиторий ведёт заметки о выпуске (см. CONTRIBUTING)

## Ссылки

- [Terraform Plugin Framework](https://developer.hashicorp.com/terraform/plugin/framework)
- [Разработка ресурсов](https://developer.hashicorp.com/terraform/plugin/framework/resources)
- [Разработка источников данных](https://developer.hashicorp.com/terraform/plugin/framework/data-sources)
- [Принципы проектирования провайдеров HashiCorp](https://developer.hashicorp.com/terraform/plugin/best-practices/hashicorp-provider-design-principles)
