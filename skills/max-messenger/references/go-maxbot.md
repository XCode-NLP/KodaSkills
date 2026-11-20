# Go-фреймворк `maxbot` (необязательный слой)

> Источник: MAXBOT github.com/max-messenger/maxbot v1.1.0 (sha 83efd1c, 11.09.2026) · зависит от `max-bot-api-client-go/v2` v2.4.0 · сверено 21.09.2026. Если это выглядит устаревшим, проверяй репозиторий.

`maxbot` — слой маршрутизации, контекста и middleware, построенный **поверх** сырого клиента, описанного в [`go-client.md`](./go-client.md) (основной путь на Go). Бери его, когда нужны регистрация обработчиков, фасад `Context` и цикл запуска polling или вебхука из коробки; бери сырой клиент напрямую, когда нужен полный контроль над диспетчеризацией, повторами или хранением состояния — сам `maxbot` ничего из этого не добавляет.

**Требует Go 1.26+.** `maxbot` v1.1.0 объявляет `go 1.24.0` в своём `go.mod`, но `api.go` вызывает `errors.AsType`, добавленный в стандартную библиотеку в Go 1.26. На Go 1.24 и 1.25 импорт падает с `undefined: errors.AsType`. Поставь `go 1.26` (или `toolchain go1.26.x`) в своём `go.mod`. Проверено 21.09.2026: собирается на go1.26.0, падает на go1.25.6. Сырой клиент (`go-client.md`) работает на Go 1.24+.

И сырой клиент, и этот фреймворк используют имя пакета Go `maxbot`. Импортируй в файле только фреймворк (плюс подпакет `model` сырого клиента, у которого другое имя пакета), чтобы избежать псевдонимов:

```go
import (
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
	"github.com/max-messenger/maxbot"
)
```

## Установка

```bash
go get github.com/max-messenger/maxbot
```

## Что он добавляет к сырому клиенту

- Плоский роутер `map[string]HandlerFunc`: точные строки команд (`/help`), константы типов событий (`message_created`) и payload колбэков (ищутся с внутренним префиксом `"callback_"`) — всё в одной карте.
- Порядок диспетчеризации на обновление: сначала совпадение колбэка, затем команды, затем сырого типа обновления — побеждает первое найденное.
- Фасад `Context` над сборкой сообщений (`Send`, `Answer`, `Reply`, `Edit`, `Delete`).
- Onion-middleware (`Use`, middleware на маршрут, `middleware.Recover`).
- Склейка режимов запуска: `Start` и `Stop`, цикл polling, подписка на вебхук и обработчик — так что код приложения никогда не трогает `Subscriptions.GetUpdates` и `Subscribe` напрямую.
- Обработчики выполняются в **горутинах** (`go f()` внутри диспетчеризации) — и путь вебхука, и путь polling работают по принципу «выстрелил и забыл»; HTTP-ответ вебхука не ждёт твоего обработчика.

Он **не** добавляет ограничение частоты, повторы сверх того, что уже делает сырой клиент, и хранение состояния — `demo-bot-go` строит свой слой состояния и блокировок на Redis поверх (см. ниже).

## Точный API

```go
func NewApi(token string, opt ...Opt) (*Api, error)
func (a *Api) Use(middleware ...MiddlewareFunc)
func (a *Api) Handle(endpoint string, h HandlerFunc, m ...MiddlewareFunc)
func (a *Api) HandleCallback(endpoint string, h HandlerFunc, m ...MiddlewareFunc)
func (a *Api) Start()
func (a *Api) Stop()
func (a *Api) WebhookHandler() http.HandlerFunc
func (a *Api) Client() *maxbot.Api // сырой клиент, для вызовов, которые maxbot не оборачивает
func (a *Api) OnError(err error, c Context)
```

`Start()` ничего не делает, если URL вебхука задан через `WithWebhook`; иначе запускает long polling. `Stop()` отменяет внутренний контекст, прерывая цикл polling. Сопоставление команд сверяет `BotName` обновления с собственным именем бота (из `GetMyInfo`, полученного один раз при создании) — если оно пустое, бот отвечает всегда, считая себя единственным ботом в чате.

## Минимальный бот

Адаптировано из `example/simple/main.go`. Здесь `bot.Start()` использует режим по умолчанию (polling); раскомментируй `WithWebhook` и подставь `bot.WebhookHandler()` для режима вебхука. Требует Go 1.26+.

```go
package main

import (
	"log"
	"net/http"
	"os"
	"time"

	"github.com/max-messenger/max-bot-api-client-go/v2/model"
	"github.com/max-messenger/maxbot"
)

func main() {
	opts := []maxbot.Opt{
		maxbot.WithHTTPClient(&http.Client{Timeout: 25 * time.Second}),
	}

	bot, err := maxbot.NewApi(os.Getenv("MAX_BOT_TOKEN"), opts...)
	if err != nil {
		log.Fatal(err)
	}

	bot.Handle("/help", func(c maxbot.Context) error {
		kb := model.NewKeyboard()
		kb.AddRow().
			AddLink("Документация", "https://dev.max.ru/docs").
			AddCallBack("Нажми меня", "pushBtn")
		return c.Send("Меню:", maxbot.WithKeyboard(kb))
	})

	bot.HandleCallback("pushBtn", func(c maxbot.Context) error {
		return c.Answer("Принято", maxbot.WithMessageID(c.Update().MessageID))
	})

	bot.Handle(maxbot.OnChatTitleChangedEvent, func(c maxbot.Context) error {
		return c.Send("Название чата изменено")
	})

	bot.Start()
}
```

- `/start` и другие команды **не** обрабатываются в `maxbot` особо — это обычные строковые ключи, которые ты регистрируешь через `Handle`.
- Чтобы подписаться на настоящий вебхук, нужно явно перечислить нужные константы событий в `WithWebhook` (например, `maxbot.OnBotAdded`, `maxbot.OnMessageCreated`, `maxbot.OnMessageCallback`).

## Обработчики, `Context`, middleware

```go
type HandlerFunc func(Context) error
type MiddlewareFunc func(HandlerFunc) HandlerFunc

type Context interface {
	Update() model.Update
	Context() context.Context
	WithValue(ctx context.Context, key, value any)
	API() *maxbot.Api // запасной путь к сырому клиенту

	Send(text string, opts ...Option) error
	Answer(text string, opts ...Option) error
	Reply(text string, opts ...Option) error
	Edit(text string, opts ...Option) error
	Delete(opts ...Option) error
}
```

- `Send` адресует новое сообщение пользователю или чату обновления.
- `Answer` отвечает на **колбэк** текущего обновления (`Messages.AnswerOnCallback(..., c.u.GetCallback().CallbackID, ...)`). На обычном обновлении сообщения колбэка нет: `GetCallback()` вернёт нулевое значение, так что вызов не паникует, но отправляет пустой `callback_id` и падает уже на API. Используй `Answer` только в обработчиках колбэков.
- `Reply` цитирует сообщение, вызвавшее обновление (`SetReply`).
- `Edit` и `Answer` **по умолчанию стирают существующие кнопки и вложения** — передай `maxbot.WithAttachments(...)`, чтобы перенести их.
- `Delete` удаляет сообщение текущего обновления.

Middleware стандартный, в стиле луковицы Go: `Api.Use(...)` дописывает в глобальную цепочку, применяемую к обработчикам, зарегистрированным **после** (вызывай `Use` до `Handle`, обратной силы нет); `Handle` и `HandleCallback` дополнительно принимают middleware на маршрут, дописываемое после глобальной цепочки.

`middleware.Recover(onError ...RecoverFunc) maxbot.MiddlewareFunc` оборачивает обработчик в `defer/recover`. Подводный камень: он молча отбрасывает значение паники, которое не является ни `error`, ни `string` (ветви `default:` нет), поэтому `panic(42)` или `panic(struct{}{})` проглатывается без строки в журнале.

```go
import (
	"log"

	"github.com/max-messenger/maxbot"
	"github.com/max-messenger/maxbot/middleware"
)

func withRecovery(bot *maxbot.Api) {
	bot.Use(middleware.Recover(func(err error, c maxbot.Context) {
		log.Println("recovered:", err)
	}))
}
```

## Опции

`Opt` (создание бота, передаётся в `NewApi`):

| Имя | Эффект |
|---|---|
| `WithHTTPClient(cli maxbot.HttpClient)` | передаётся в опцию сырого клиента |
| `WithBaseURL(baseURL string)` | передаётся в сырой клиент |
| `WithPollingPause(d time.Duration)` | передаётся в сырой клиент |
| `WithPollingTimeout(d time.Duration)` | передаётся в сырой клиент |
| `WithErrorHandle(f func(error, Context))` | задаёт собственный `onError` фреймворка (по умолчанию `log.Println`) |
| `WithWebhook(webhookUrl, secret string, types []string)` | переключает `Start()` в режим вебхука; **требует все 3 аргумента** — быстрый старт в самом README вызывает его с одним аргументом, и это не компилируется |

`Option` (на сообщение, передаётся в `Context.Send`, `Answer`, `Reply`, `Edit`, `Delete`):

`WithKeyboard(*model.Keyboard)`, `WithFormat(model.TextFormat)`, `WithChat(id int64)`, `WithUser(id int64)`, `WithAttachByToken(fileToken string, at model.AttachmentType)`, `WithAttachments([]model.Attachment)` (перенести вложения, которые `Edit` или `Answer` иначе сотрут), `WithMessageID(messageID string)`.

## Режимы запуска

- **Polling** (по умолчанию): `Start()` крутит `Subscriptions.GetUpdates` без собственной явной паузы (темп задают `WithPollingPause` и `WithPollingTimeout`, передаваемые в сырой клиент). `*maxbot.TimeoutError` считается пустой страницей и проглатывается; **любая другая ошибка останавливает цикл навсегда** — без перезапуска и задержки, и без вызова `OnError`, так что сетевой сбой может молча прекратить доставку обновлений. В продакшене следи за горутиной сам.
- **Вебхук**: задай `WithWebhook(url, secret, types)`; `Start()` становится пустышкой (подписка уже выполнена во время `NewApi`), а `bot.WebhookHandler()` монтируешь сам через `net/http`. Проверка секрета целиком делегирована `GetHandler` сырого клиента (обычное `!=`, не за постоянное время — шаблон обёртки за постоянное время см. в разделе «Вебхук» файла `go-client.md`; он применим и здесь, поскольку `WebhookHandler()` — тонкий проброс).

## Когда брать его, а когда сырой клиент

Бери **maxbot**, когда нужен быстрый однопроцессный бот и устраивают его порядок диспетчеризации, модель «горутина на обновление» и отсутствие встроенного хранения состояния и ограничения частоты. Бери **сырой клиент** напрямую (`go-client.md`), когда нужен другой роутер или фреймворк (chi, свои деревья команд), явный контроль над параллелизмом и задержками либо ты уже строишь окружающий сервис (хранилище состояния, метрики, корректное завершение) сам — тогда роутер `maxbot` мало что добавляет, а его решения (диспетчеризация в горутину, отсутствие задержек при ошибках polling) могут мешать.

## Ориентиры по архитектуре `demo-bot-go`

`demo-bot-go` — собственный эталонный бот MAX, построенный на `maxbot`. Полезные шаблоны, которые стоит позаимствовать (не копируй его зафиксированные версии — он фиксирует `maxbot v0.0.2` и клиент `v2.1.0`, оба устарели; используй проверенные здесь v1.1.0 и v2.4.0):

- **Дерево модулей fx** (`uber-go/fx`): модуль `pkg/connections/maxbot` собирает один `maxbot.Api` на каждого настроенного бота из YAML, безусловно добавляет `middleware.Recover(...)` плюс middleware OpenTelemetry и Prometheus, затем запускает `go api.Start()`.
- **Роутер**: `go-chi/chi/v5`; путь вебхука регистрирует сам пул соединений maxbot (`r.Handle(cfg.Path, mw.WebhookHandler(pool.WebhookHandler(), log))`), а не написанный руками контроллер. Дополнительной проверки секрета вебхука на этом слое нет — это по-прежнему работа сырого клиента.
- **Состояние и сессии**: `ScenarioState{Scenario, Step, Data}` в Redis на пользователя, по умолчанию TTL 30 минут, под распределённой блокировкой Redis по id пользователя, чтобы сериализовать одновременные обновления одного пользователя.
- **Реестр сценариев**: обычная `map[string]Scenario`; `Registry.Add` паникует на дублирующемся имени — это падение при старте, а не восстановимая ошибка.
- **Пробел с ограничением частоты**: в демо есть общий переиспользуемый модуль `pkg/ratelimiter`, но он нигде не подключён к сервису бота — эталонный бот сам не ограничивает исходящие запросы к API MAX. Не делай из его чтения вывод, что «собственный бот MAX ограничивает частоту».
- **Проверка прав в группах**: перед сценарием, которому нужны права администратора чата, демо вызывает `Chats.GetMembership`, сверяет выданные боту права с тем, что объявляет сценарий, и предупреждает, вместо того чтобы молча падать.
