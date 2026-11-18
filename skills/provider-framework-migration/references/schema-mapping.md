# Справочник перевода SDKv2 → Plugin Framework

Механические сопоставления для переноса ресурса. Каждая строка сохраняет синтаксис
конфигурации пользователя и структуру состояния — инвариант безопасного переноса.

## Схема: типы

| SDKv2 | Framework |
|---|---|
| `Type: schema.TypeString` | `schema.StringAttribute` |
| `Type: schema.TypeBool` | `schema.BoolAttribute` |
| `Type: schema.TypeInt` | `schema.Int64Attribute` |
| `Type: schema.TypeFloat` | `schema.Float64Attribute` |
| `Type: schema.TypeList, Elem: &schema.Schema{Type: schema.TypeString}` | `schema.ListAttribute{ElementType: types.StringType}` |
| `Type: schema.TypeSet, Elem: &schema.Schema{...}` | `schema.SetAttribute{ElementType: ...}` |
| `Type: schema.TypeMap, Elem: &schema.Schema{...}` | `schema.MapAttribute{ElementType: ...}` |
| `Type: schema.TypeList, Elem: &schema.Resource{...}` (синтаксис блока в конфигурациях) | `schema.ListNestedBlock` в `Blocks:` — **не** вложенный атрибут (синтаксис атрибута сломал бы существующие конфигурации) |
| `Type: schema.TypeSet, Elem: &schema.Resource{...}` | `schema.SetNestedBlock` в `Blocks:` |
| Блок `MaxItems: 1`, использованный как псевдообъект | При переносе — `ListNestedBlock` + `listvalidator.SizeAtMost(1)`; `SingleNestedAttribute` только для новых схем |

## Схема: поведение

| SDKv2 | Framework |
|---|---|
| `Required: true` / `Optional: true` / `Computed: true` | Те же поля, те же значения |
| `ForceNew: true` | `PlanModifiers: []planmodifier.String{stringplanmodifier.RequiresReplace()}` |
| `Default: "foo"` | `Default: stringdefault.StaticString("foo")` (из `resource/schema/stringdefault`; требует `Computed: true` вместе с `Optional`) |
| `ValidateFunc` / `ValidateDiagFunc` | `Validators: []validator.String{...}` (из `terraform-plugin-framework-validators`) |
| `ConflictsWith` / `ExactlyOneOf` / `AtLeastOneOf` / `RequiredWith` | `stringvalidator.ConflictsWith(path.Expressions...)`, `ExactlyOneOf(...)`, `AtLeastOneOf(...)`, `AlsoRequires(...)` |
| `Sensitive: true` | То же поле |
| `Deprecated: "..."` | `DeprecationMessage: "..."` |
| `Description` | `Description` / `MarkdownDescription` |
| `DiffSuppressFunc` | Прямого эквивалента нет. Используй свой тип с семантическим равенством (предпочтительно; например, строковые типы без учёта регистра или с нормализованным JSON) либо модификатор плана. Если логика подавления запутанная, подумай, стоит ли переносить этот ресурс |
| `StateFunc` | Эквивалента нет — нормализуй в Create и Read до записи состояния либо используй свой тип |
| `CustomizeDiff` | Модификация плана на уровне ресурса: `ResourceWithModifyPlan.ModifyPlan` либо модификаторы плана по атрибутам |
| `Timeouts` в схеме | Блок `timeouts` через `terraform-plugin-framework-timeouts`; читается как `data.Timeouts.Create(ctx, defaultTimeout)` |

## Форма ресурса

| SDKv2 | Framework |
|---|---|
| `func resourceWidget() *schema.Resource`, возвращающая структуру функций | Структура, реализующая `resource.Resource` (+ `ResourceWithConfigure`, `ResourceWithImportState`) |
| `CreateWithoutTimeout: resourceWidgetCreate` | `func (r *widgetResource) Create(ctx, req resource.CreateRequest, resp *resource.CreateResponse)` |
| `meta.(*Client)` в каждой CRUD-функции | Клиент, сохранённый один раз в `Configure(req.ProviderData)` |
| `Importer: &schema.ResourceImporter{StateContext: schema.ImportStatePassthroughContext}` | `func (r *widgetResource) ImportState(...)`, вызывающая `resource.ImportStatePassthroughID(ctx, path.Root("id"), req, resp)` |
| Регистрация в `ResourcesMap: map[string]*schema.Resource` | Конструктор, перечисленный в `Resources() []func() resource.Resource` провайдера |

## Доступ к данным внутри CRUD

| SDKv2 | Framework |
|---|---|
| `d.Get("name").(string)` | Типизированная модель: `data.Name.ValueString()` после `req.Plan.Get(ctx, &data)` |
| `d.GetOk("name")` | `!data.Name.IsNull()` — и реши явно, что делать с unknown (`IsUnknown()`) |
| `d.Set("name", v)` | Присвой поле модели (`data.Name = types.StringPointerValue(v)`), затем `resp.State.Set(ctx, &data)` |
| `d.SetId(id)` | Задай поле `id` модели как любой другой атрибут |
| `d.SetId("")` в Read (объект исчез) | `resp.State.RemoveResource(ctx)` |
| `d.Id()` | `data.ID.ValueString()` из `req.State.Get` |
| `d.HasChange("field")` | Сравни модели плана и состояния: `!plan.Field.Equal(state.Field)` |
| `d.IsNewResource()` | Не существует — Create и *есть* путь нового ресурса; логика повторных чтений после создания переезжает в Create |
| Возвраты `diag.Diagnostics` | `resp.Diagnostics.AddError`, `AddWarning`, `Append` |

## Ловушка null и нуля (главный поведенческий риск переноса)

SDKv2 схлопывает «не задано» в нулевые значения Go: `d.Get` у незаданной строки
возвращает `""`, у незаданного int — `0`, у незаданного bool — `false`. Framework
сохраняет null, unknown и ноль различимыми. Последствия:

```go
// SDKv2 — unset and "" are the same thing:
if v, ok := d.GetOk("description"); ok {
    input.Description = aws.String(v.(string))
}

// Framework — express the same "omit when not set" explicitly:
if !data.Description.IsNull() {
    input.Description = data.Description.ValueStringPointer()
}
```

Проверь каждый атрибут на три случая: пользователь задал значение, пользователь задал нулевое
значение (`""`, `0`, `false` — SDKv2 не мог отличить это от незаданного;
пользователи могут полагаться на любую из трактовок) и пользователь опустил его. API
должен получить ровно то, что отправляла версия на SDKv2 в каждом случае, иначе существующие
конфигурации изменят поведение. `ImportStateVerify` и тесты обновления с пустым планом
ловят большинство, но не все такие случаи — поищи по коду `GetOk` и сравнения с нулевыми
значениями и продумай каждый.

## Что не меняется

- Ожидания `retry.StateChangeConf` и поисковики `retry.NotFoundError` — пакет
  `helper/retry` работает из кода Framework; переноси их без изменений.
- Приёмочные тесты — `terraform-plugin-testing` работает с мультиплексированным
  провайдером; существующие тесты должны проходить без изменений (переключи фабрики
  на `ProtoV6ProviderFactories`, обслуживающие мультиплексированный сервер).
- Код клиента API и вспомогательные функции expand и flatten, работающие с типами API.

## Инструменты

Некоторые провайдеры автоматизируют первый проход (у terraform-provider-aws есть
внутренний скаффолдер `tfsdk2fw`). Ни один публичный инструмент не даёт безопасного
переноса от начала до конца — считай любой сгенерированный перенос черновиком, который
надо проверить по этому справочнику, особенно по таблице null и нуля выше.
