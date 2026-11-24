---
name: provider-configuration
description: "Реализация конфигурации и аутентификации провайдера Terraform на Plugin Framework: схема провайдера для учётных данных (атрибуты Optional + Sensitive), откат на переменные окружения, цепочки источников учётных данных (статическая конфигурация, затем переменные окружения, общий файл учётных данных и удостоверение платформы), защита от неизвестных значений в Configure(), сокрытие секретов, проверка учётных данных на этапе настройки и диагностика, называющая каждый испробованный источник. Используй при реализации или проверке метода Configure либо схемы провайдера, при добавлении вариантов аутентификации (API-ключи, токены, профили, файлы учётных данных, assume-role), при решении, как провайдер должен находить учётные данные, при разборе ошибок «no valid credential sources» или отсутствующих учётных данных, а также при модульном тестировании поиска учётных данных."
license: MPL-2.0
metadata:
  author: hashicorp
  source: https://github.com/hashicorp/agent-skills
  tags: [terraform, go, провайдеры, аутентификация]
---

# Конфигурация и аутентификация провайдера Terraform

Как провайдер принимает настройки подключения и находит учётные данные. Плохое удобство аутентификации — первое, с чем сталкивается каждый пользователь провайдера; хорошо спроектированная цепочка источников учётных данных и отличает провайдер продакшн-уровня от демонстрационного. В примерах используется вымышленный провайдер `examplecloud` и [Plugin Framework](https://developer.hashicorp.com/terraform/plugin/framework/providers).

**Справочники** (загружай по необходимости):
- `references/credential-chain.md` — полная компилируемая реализация цепочки учётных данных
  (провайдеры, цепочка, профили файла, подключение в Configure, тесты);
- `references/case-studies.md` — как провайдер AWS (`aws-sdk-go-base`)
  и провайдеры поменьше строят настоящие цепочки учётных данных.

---

## Схема провайдера для аутентификации

Каждый атрибут аутентификации должен быть `Optional`, никогда `Required` — атрибут
`Required` заставляет пользователей хранить учётные данные в конфигурации и
делает невозможным поиск через переменные окружения и файл учётных данных. Помечай
секреты как `Sensitive`, чтобы Terraform скрывал их в выводе плана, и указывай
откат на переменную окружения в каждом описании, чтобы `tfplugindocs` публиковал
правила поиска.

```go
func (p *examplecloudProvider) Schema(ctx context.Context, req provider.SchemaRequest, resp *provider.SchemaResponse) {
    resp.Schema = schema.Schema{
        Attributes: map[string]schema.Attribute{
            "endpoint": schema.StringAttribute{
                Optional:            true,
                MarkdownDescription: "API endpoint. May also be set via the `EXAMPLECLOUD_ENDPOINT` environment variable.",
            },
            "api_key": schema.StringAttribute{
                Optional:            true,
                MarkdownDescription: "API key. May also be set via the `EXAMPLECLOUD_API_KEY` environment variable, or in a shared credentials file.",
            },
            "api_secret": schema.StringAttribute{
                Optional:            true,
                Sensitive:           true,
                MarkdownDescription: "API secret. May also be set via the `EXAMPLECLOUD_API_SECRET` environment variable, or in a shared credentials file.",
            },
            "profile": schema.StringAttribute{
                Optional:            true,
                MarkdownDescription: "Named profile in the shared credentials file. May also be set via the `EXAMPLECLOUD_PROFILE` environment variable. Defaults to `default`.",
            },
            "skip_credentials_validation": schema.BoolAttribute{
                Optional:            true,
                MarkdownDescription: "Skip the identity check normally performed during provider configuration.",
            },
        },
    }
}
```

Никогда не добавляй `Default` к атрибуту учётных данных и никогда не вшивай
учётные данные в код провайдера. Значения по умолчанию относятся к логике
поиска (где переменные окружения и файлы могут их переопределить), а не к схеме.

## Цепочка источников учётных данных

Ищи учётные данные, перебирая упорядоченный список источников и беря первый,
который даёт **полный** набор. Это тот же приём, что использует провайдер AWS
через [`aws-sdk-go-base`](https://github.com/hashicorp/aws-sdk-go-base), и он
обобщается на любой провайдер. Канонический приоритет, от высшего:

1. **Статическая конфигурация** — значения, заданные прямо в блоке `provider`.
   Явное всегда побеждает.
2. **Переменные окружения** — `EXAMPLECLOUD_API_KEY` и т. д. Путь, удобный для CI.
3. **Общий файл учётных данных** — именованные профили в
   `~/.examplecloud/credentials`, для людей с несколькими аккаунтами.
4. **Удостоверение платформы** — метаданные инстанса, удостоверение рабочей нагрузки или обмен
   OIDC-токеном, там где платформа это даёт. Учётные данные, которые никому не нужно
   хранить.

Цепочку предсказуемой делают два правила:

- **Ищи секреты набором, а не по полям.** Если окружение даёт API-ключ, но не даёт
  секрет, этот источник не предлагает ничего — переходи к следующему источнику
  за *обоими* значениями. Смешивание ключа из переменной окружения с секретом из
  профиля файла даёт сбои аутентификации, которые пользователю почти невозможно
  отладить.
- **Ищи несекретные настройки подключения по полям.** `endpoint`,
  `profile` или `insecure` могут независимо следовать порядку
  конфигурация > окружение > файл > значение по умолчанию, потому что несовпадение там
  видно и безвредно.

Основная абстракция — интерфейс с одним методом и сигнальной ошибкой, которая
отличает «этому источнику нечего предложить» (переход дальше) от «этот
источник настроен неверно» (показать ошибку):

```go
// ErrNoCredentials signals a source had nothing to offer. The chain falls
// through to the next source. Any other error means the source was
// configured but unusable (e.g. malformed credentials file) and is
// preserved so the final diagnostics can surface it.
var ErrNoCredentials = errors.New("no credentials found")

type Credentials struct {
    APIKey    string
    APISecret string
    Source    string // which provider supplied them, for logging
}

func (c Credentials) Complete() bool {
    return c.APIKey != "" && c.APISecret != ""
}

type Provider interface {
    Retrieve(ctx context.Context) (Credentials, error)
    Name() string
}
```

`Chain` (сам является `Provider`, поэтому цепочки композируются) обходит провайдеры
по порядку и возвращает первый полный набор учётных данных. Каждый пропущенный
источник записывается в агрегированную `ChainError`, чей `Error()` перечисляет каждый
источник с причиной пропуска, а метод `Is` делает
`errors.Is(err, ErrNoCredentials)` истинным только когда все источники чисто
завершились без результата — так `Configure` одним проверкой отличает «ничего не
предоставлено» от «предоставлено, но сломано». Полная реализация — цикл
цепочки, статический провайдер, провайдеры окружения и файла и конструктор
`NewDefaultChain`, который владеет каноническим порядком, — лежит в
`references/credential-chain.md`.

## Подключение цепочки в Configure

`Configure` выполняется один раз на операцию Terraform, до любых CRUD-операций с ресурсами.
Форма:

```go
func (p *examplecloudProvider) Configure(ctx context.Context, req provider.ConfigureRequest, resp *provider.ConfigureResponse) {
    var config examplecloudProviderModel
    resp.Diagnostics.Append(req.Config.Get(ctx, &config)...)
    if resp.Diagnostics.HasError() {
        return
    }

    // 1. Guard against unknown values (e.g. api_key = some_resource.output).
    if config.APIKey.IsUnknown() {
        resp.Diagnostics.AddAttributeError(
            path.Root("api_key"),
            "Unknown API Key",
            "The provider cannot connect because api_key depends on a value known only after apply. "+
                "Set a static value, or use the EXAMPLECLOUD_API_KEY environment variable.",
        )
    }
    // ... repeat for each auth attribute, then:
    if resp.Diagnostics.HasError() {
        return
    }

    // 2. Resolve credentials through the chain.
    chain := credentials.NewDefaultChain(
        config.APIKey.ValueString(),
        config.APISecret.ValueString(),
        credentials.Options{Profile: config.Profile.ValueString()},
    )
    creds, err := chain.Retrieve(ctx)
    if err != nil {
        if errors.Is(err, credentials.ErrNoCredentials) {
            resp.Diagnostics.AddError(
                "No Valid Credential Sources Found",
                "No examplecloud credentials were found. Sources tried, in order:\n\n"+err.Error()+
                    "\n\nSet api_key and api_secret in the provider block, export "+
                    "EXAMPLECLOUD_API_KEY and EXAMPLECLOUD_API_SECRET, or add a profile to "+
                    "~/.examplecloud/credentials. See https://example.com/docs/auth.",
            )
        } else {
            resp.Diagnostics.AddError("Failed to Resolve Credentials", err.Error())
        }
        return
    }
    tflog.Debug(ctx, "resolved credentials", map[string]any{"source": creds.Source})

    // 3. Build the client once; share it with every resource and data source.
    client := examplecloud.NewClient(endpoint, creds.APIKey, creds.APISecret)
    resp.DataSourceData = client
    resp.ResourceData = client
}
```

Почему важен каждый шаг:

- **Защита от неизвестных значений.** Во время планирования атрибут, привязанный к
  выходу другого ресурса, *неизвестен*, а не null. Без защиты провайдер молча
  считает его пустым, проходит цепочку без результата и аутентифицируется под
  чужой личностью — либо падает с вводящей в заблуждение ошибкой «missing credentials».
  Назови в сообщении защиты обходной путь через переменную окружения.
- **Сигнальная проверка выбирает правильное сообщение.** «Ты ничего не дал»
  (список вариантов, с которым можно что-то сделать) — иной сбой, чем «ты дал
  что-то сломанное» (покажи ошибку разбора). Схлопывание их в одно сообщение —
  это путь, которым провайдеры приводят пользователей к вставке секретов в
  конфигурацию ради отладки.
- **Записывай в журнал источник, никогда — секрет.** Знание того, *какой* источник
  сработал, — самый полезный факт для отладки, и его запись ничего не стоит.

## Диагностика, которая разблокирует пользователей

Сообщение об ошибке аутентификации — самая читаемая документация провайдера.
Каждая диагностика сбоя учётных данных должна называть:

- **каждый испробованный источник по порядку с причиной пропуска** — это даёт
  `ChainError`. `aws-sdk-go-base` делает то же через свою
  `NoValidCredentialSourcesError`;
- **точные имена переменных окружения**, а также путь к файлу учётных данных и
  профиль, которые проверялись, — а не «задайте соответствующие переменные
  окружения»;
- **URL документации** с руководством по аутентификации провайдера.

Используй предупреждения (а не ошибки) для условий, подозрительных, но не фатальных,
называя то, что получило приоритет: заданный `profile` при наличии учётных данных
из окружения (что победит?) или файл учётных данных с правами на чтение для группы
и всех (`chmod 0600` в подсказке).

## Гигиена секретов

- Дай типу `Credentials` методы `String()` и `GoString()`, которые
  скрывают поля-секреты, чтобы случайный `%v`, `%+v` или обёртка ошибки никогда не
  выпустили секрет в журналы или диагностику.
- Никогда не включай *значения* учётных данных в диагностику, строки журнала или
  обёрнутые ошибки — записывай только имя источника и несекретные идентификаторы.
- Предупреждай, когда файл учётных данных доступен на чтение другим пользователям
  (`info.Mode().Perm()&0o077 != 0`); пропускай эту проверку в Windows, где биты прав
  POSIX не имеют смысла.

## Проверка на этапе настройки

Находи цепочку сразу в `Configure` — никогда лениво при первом использовании
ресурса — чтобы проблема с учётными данными падала один раз, на плане, с хорошим
сообщением, а не в середине применения. Если у API есть дешёвый эндпоинт
удостоверения (эквивалент AWS `sts:GetCallerIdentity` или `/whoami`), вызывай его
после поиска учётных данных, чтобы *неверные* (не только отсутствующие) учётные
данные тоже падали на этапе настройки. Спрячь его за атрибутом
`skip_credentials_validation` для изолированных или заглушечных окружений.

## Модульное тестирование цепочки

Цепочка — чистая логика: тестируй её модульными тестами (префикс `Test`, без
`TF_ACC`), а не приёмочными. Сделай окружение внедряемым (поле
`getenv func(string) string` со значением по умолчанию `os.Getenv` или
`t.Setenv`) и направь файловый провайдер на фикстуры `t.TempDir()`. Тесты, которые
важны:

- **По источникам**: каждый провайдер возвращает свои учётные данные, когда они
  заданы, и `ErrNoCredentials`, когда набор неполон (ключ без секрета неполон).
- **Приоритет**: статика побеждает окружение; окружение побеждает файл; цепочка
  доходит до файла, когда ничего выше не даёт полного набора.
- **Агрегация сбоев**: при пустых всех источниках
  `errors.Is(err, ErrNoCredentials)` истинно, а сообщение называет каждый
  источник.
- **Жёсткие ошибки**: испорченный файл учётных данных или *явно запрошенный*
  профиль, которого нет, дают описательную ошибку, а не молчаливый переход дальше
  (профиль, взятый лишь по умолчанию, приводит к переходу дальше).
- **Сокрытие**: `fmt.Sprintf("%v")` и `%+v` значения `Credentials`
  никогда не содержат секрет.

Полные примеры тестов — в `references/credential-chain.md`.

## Чек-лист

- [ ] Все атрибуты аутентификации `Optional`; секреты помечены `Sensitive: true`
- [ ] В описаниях атрибутов названы их откаты на переменные окружения
- [ ] Защита от неизвестных значений на каждом атрибуте аутентификации в `Configure`
- [ ] Приоритет цепочки: статическая конфигурация > переменные окружения > файл учётных данных > удостоверение платформы
- [ ] Секреты ищутся полным набором; несекретные настройки — по полям
- [ ] Сигнальная ошибка `ErrNoCredentials` отличает переход дальше от жёсткого сбоя
- [ ] Диагностика отсутствующих учётных данных перечисляет все испробованные источники и URL документации
- [ ] Тип `Credentials` скрывает секреты в `String()` и `GoString()`
- [ ] Предупреждение о правах файла учётных данных (кроме Windows)
- [ ] Немедленный поиск в `Configure`; необязательная проверка удостоверения через `skip_credentials_validation`
- [ ] Модульные тесты покрывают поведение источников, приоритет, агрегацию, сокрытие
- [ ] Ни одно значение учётных данных не попадает в журнал и не встраивается в ошибку

## Связанные навыки

Используй навык `new-terraform-provider` (если доступен), чтобы создать каркас
провайдера, в котором живёт эта конфигурация, и навык `provider-resources` для
использования настроенного клиента в ресурсах и источниках данных.
