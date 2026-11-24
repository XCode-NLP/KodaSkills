---
name: provider-ephemeral-resources
description: "Реализация эфемерных ресурсов провайдера Terraform на Plugin Framework: жизненный цикл Open, Renew и Close, проектирование эфемерной схемы, регистрация через EphemeralResources, продление истекающих учётных данных и то, как эфемерные значения попадают в write-only атрибуты и конфигурацию провайдера. Используй при добавлении эфемерного ресурса, при выдаче секретов, токенов и сертификатов, которые не должны сохраняться в состоянии или плане, при выборе между эфемерным ресурсом и источником данных, а также при передаче короткоживущих учётных данных из одного провайдера в другой."
license: MPL-2.0
metadata:
  author: hashicorp
  source: https://github.com/hashicorp/agent-skills
  tags: [terraform, go, провайдеры]
---

# Эфемерные ресурсы провайдера Terraform

Эфемерные ресурсы (Terraform 1.10+) дают значения, которые **никогда не
сохраняются в состоянии или плане**. У них ровно одна задача: передать
секреты — токены, сгенерированные пароли, короткоживущие сертификаты, расшифрованные
значения — тем частям конфигурации, которым они нужны, не записывая их
на диск. Любой источник данных, возвращающий чувствительное значение, — кандидат
стать (или также существовать как) эфемерным ресурсом.

Официальная документация: [Ephemeral Resources](https://developer.hashicorp.com/terraform/plugin/framework/ephemeral-resources).

## Когда его использовать

| Ситуация | Что использовать |
|---|---|
| Поиск несекретных данных только на чтение | Источник данных |
| Значение чувствительно и нужно только во время применения (пароль БД для блока провайдера, токен для write-only атрибута) | Эфемерный ресурс |
| Чувствительное значение, которое нижестоящие *управляемые ресурсы* должны хранить (например, как атрибут) | Обычный ресурс или источник данных — но по возможности вместе с write-only атрибутами |
| Учётные данные, истекающие посреди операции (токены в стиле STS, короткоживущие аренды) | Эфемерный ресурс с `Renew` |

Эфемерные результаты можно использовать в конфигурации провайдера, write-only
атрибутах, конфигурации провижинера и других эфемерных контекстах — но
не в обычных атрибутах, потому что те сохраняются в состоянии.

## Жизненный цикл

Terraform вызывает до трёх методов на операцию:

- **`Open`** (обязательный) — получить или создать значение; выполняется во время плана
  и (или) применения, когда результат нужен. Обновлять состояние не нужно,
  импортировать нечего.
- **`Renew`** (необязательный) — вызывается, когда настенные часы проходят
  `RenewAt`, возвращённое `Open` или `Renew`, для значений, которые истекают, пока
  Terraform ещё работает. Renew не может вернуть новый результат — он может
  только продлить или обновить то, что создал `Open` (например, перезаключить ту же
  аренду); если само значение при продлении меняется, API в этом смысле не
  продлеваемый, и `Open` должен возвращать более долгоживущее значение.
- **`Close`** (необязательный) — вызывается, когда Terraform закончил со значением;
  здесь отзывай аренды или удаляй временные учётные данные.

`Open` может передать байты дальше через `resp.Private`; `Renew` и `Close`
их получают — используй это для идентификаторов аренды, нужных для продления и отзыва.

## Реализация

```go
var (
    _ ephemeral.EphemeralResource              = &tokenEphemeralResource{}
    _ ephemeral.EphemeralResourceWithConfigure = &tokenEphemeralResource{}
    _ ephemeral.EphemeralResourceWithRenew     = &tokenEphemeralResource{}
    _ ephemeral.EphemeralResourceWithClose     = &tokenEphemeralResource{}
)

func NewTokenEphemeralResource() ephemeral.EphemeralResource {
    return &tokenEphemeralResource{}
}

type tokenEphemeralResource struct {
    client *examplecloud.Client
}

type tokenEphemeralResourceModel struct {
    RoleName types.String `tfsdk:"role_name"`
    Token    types.String `tfsdk:"token"`
    LeaseID  types.String `tfsdk:"lease_id"`
}

func (r *tokenEphemeralResource) Metadata(_ context.Context, req ephemeral.MetadataRequest, resp *ephemeral.MetadataResponse) {
    resp.TypeName = req.ProviderTypeName + "_token"
}

func (r *tokenEphemeralResource) Schema(_ context.Context, _ ephemeral.SchemaRequest, resp *ephemeral.SchemaResponse) {
    resp.Schema = schema.Schema{
        Attributes: map[string]schema.Attribute{
            "role_name": schema.StringAttribute{
                Required:            true,
                MarkdownDescription: "Role to obtain a token for.",
            },
            "token": schema.StringAttribute{
                Computed:            true,
                Sensitive:           true,
                MarkdownDescription: "The issued token. Never persisted to state.",
            },
            "lease_id": schema.StringAttribute{
                Computed:            true,
                MarkdownDescription: "Identifier of the token lease.",
            },
        },
    }
}

func (r *tokenEphemeralResource) Open(ctx context.Context, req ephemeral.OpenRequest, resp *ephemeral.OpenResponse) {
    var data tokenEphemeralResourceModel
    resp.Diagnostics.Append(req.Config.Get(ctx, &data)...)
    if resp.Diagnostics.HasError() {
        return
    }

    lease, err := r.client.IssueToken(ctx, data.RoleName.ValueString())
    if err != nil {
        resp.Diagnostics.AddError(
            "Error opening Token",
            fmt.Sprintf("issuing token for role (%s): %s", data.RoleName.ValueString(), err),
        )
        return
    }

    data.Token = types.StringValue(lease.Token)
    data.LeaseID = types.StringValue(lease.ID)

    resp.RenewAt = lease.ExpiresAt.Add(-2 * time.Minute) // renew with margin
    resp.Private.SetKey(ctx, "lease_id", []byte(lease.ID))
    resp.Diagnostics.Append(resp.Result.Set(ctx, &data)...)
}

func (r *tokenEphemeralResource) Renew(ctx context.Context, req ephemeral.RenewRequest, resp *ephemeral.RenewResponse) {
    leaseID, diags := req.Private.GetKey(ctx, "lease_id")
    resp.Diagnostics.Append(diags...)
    if resp.Diagnostics.HasError() {
        return
    }

    lease, err := r.client.RenewLease(ctx, string(leaseID))
    if err != nil {
        resp.Diagnostics.AddError("Error renewing Token", err.Error())
        return
    }
    resp.RenewAt = lease.ExpiresAt.Add(-2 * time.Minute)
}

func (r *tokenEphemeralResource) Close(ctx context.Context, req ephemeral.CloseRequest, resp *ephemeral.CloseResponse) {
    leaseID, diags := req.Private.GetKey(ctx, "lease_id")
    resp.Diagnostics.Append(diags...)
    if resp.Diagnostics.HasError() {
        return
    }

    if err := r.client.RevokeLease(ctx, string(leaseID)); err != nil {
        resp.Diagnostics.AddError("Error closing Token", err.Error())
    }
}
```

`Configure` следует тому же приёму приведения ProviderData, что и ресурсы (навык
`provider-resources`, если доступен, его показывает); клиент берётся из
`resp.EphemeralResourceData`, заданного в `Configure` провайдера.

## Регистрация

Провайдер подключает их через `provider.ProviderWithEphemeralResources`:

```go
var _ provider.ProviderWithEphemeralResources = &examplecloudProvider{}

func (p *examplecloudProvider) EphemeralResources(_ context.Context) []func() ephemeral.EphemeralResource {
    return []func() ephemeral.EphemeralResource{
        NewTokenEphemeralResource(),
    }
}
```

Задай `resp.EphemeralResourceData = client` в `Configure` провайдера
рядом с `ResourceData` и `DataSourceData`.

## Правила проектирования

- **Никогда не записывай значение в журнал и не вставляй его в диагностику.** Весь смысл —
  в несохранении; сообщение об ошибке с токеном его перечёркивает.
- Всё равно помечай секретный атрибут `Sensitive: true` — это защищает отрисовку
  в собственном выводе жизненного цикла эфемерного значения.
- Никаких модификаторов плана, импорта и соглашений об `id` — нет состояния,
  на которое они могли бы действовать.
- Входные данные схемы подчиняются тем же правилам, что аргументы источника данных; открывай
  идентификаторы API (`role_name`), а не выдуманные.
- Задавай `RenewAt` с запасом до реального истечения; Terraform
  продлевает лениво, а не по точному таймеру.
- Если вышестоящее значение нельзя отозвать, пропусти `Close`, а не
  реализуй пустышку, которая создаёт впечатление, что отзыв происходит.

## Тестирование

Эфемерные результаты никогда не попадают в состояние, поэтому тесты проверяют их косвенно —
стандартный приём передаёт эфемерное значение через `echoprovider` в
обычный ресурс, который тест может изучить. Минимальное покрытие: базовый
тест открытия и использования плюс тесты по каждому атрибуту рядом с обязательными полями. Используй
навык `provider-test-patterns` (если доступен) — его справочник по эфемерному
тестированию покрывает настройку echoprovider, привязку к версии
(`tfversion.SkipBelow(tfversion.Version1_10_0)`) и многошаговые приёмы.

## Документация

Документация в Registry живёт в `docs/ephemeral-resources/<name>.md` и генерируется
`tfplugindocs`, как и любой другой тип страниц. Используй навык `provider-docs`
(если доступен) для порядка работы; описывай поведение продления и отзыва
явно — пользователям нужно знать, отзывает ли учётные данные закрытие их запуска
Terraform.

## Чек-лист

- [ ] Значение действительно не должно сохраняться (иначе источник данных проще)
- [ ] Реализован `Open`; `Renew` и `Close` только там, где API их поддерживает
- [ ] Секретные атрибуты `Sensitive: true`; значение никогда не в журнале и не в диагностике
- [ ] Аренда или дескриптор передаются через `Private`, а не через результат
- [ ] `RenewAt` задано с запасом для истекающих учётных данных
- [ ] Ресурс зарегистрирован в `EphemeralResources()`; `EphemeralResourceData` задан в Configure провайдера
- [ ] Приёмочные тесты с echo-провайдером, привязанные к Terraform >= 1.10
- [ ] Страница документации объясняет время жизни, продление и отзыв
