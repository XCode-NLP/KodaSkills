# Go-клиент: `max-bot-api-client-go`

**Содержание:** [Установка](#установка) · [Конструктор и опции](#конструктор-и-опции) · [Группы сервисов (точные сигнатуры)](#группы-сервисов-точные-сигнатуры) · [Билдер сообщений (`maxbot.NewMessage()`)](#билдер-сообщений-maxbotnewmessage) · [Билдер клавиатур (`model.NewKeyboard()`)](#билдер-клавиатур-modelnewkeyboard) · [Загрузки](#загрузки) · [Long polling](#long-polling) · [Вебхук](#вебхук) · [Ответы на колбэки](#ответы-на-колбэки) · [API комментариев](#api-комментариев) · [ValidateInitData (initData мини-приложения)](#validateinitdata-initdata-мини-приложения) · [Ошибки, повторы — и отсутствие ограничения частоты](#ошибки-повторы--и-отсутствие-ограничения-частоты) · [Подводные камни (не упомянутые выше)](#подводные-камни-не-упомянутые-выше)

> Источник: GO github.com/max-messenger/max-bot-api-client-go/v2 v2.4.0 (sha c832c5b, 08.09.2026) · сверено 21.09.2026. Если это выглядит устаревшим, проверяй репозиторий.

Это **основной** путь на Go для ботов MAX: тонкая низкоуровневая обёртка над Bot API. Про слой с маршрутизацией, контекстом и middleware «всё включено» поверх него — в [`go-maxbot.md`](./go-maxbot.md); он необязателен.

## Установка

```bash
go mod init your-bot
go get github.com/max-messenger/max-bot-api-client-go/v2
```

Имя корневого пакета — `maxbot` (путь импорта заканчивается на `/v2`, но сам пакет Go называется `maxbot`). Типы моделей живут в подпакете `model`. И сырой клиент, и отдельный репозиторий фреймворка `maxbot` (`go-maxbot.md`) называются `maxbot` — если файл импортирует оба, задай одному явный псевдоним, например `rawclient "github.com/max-messenger/max-bot-api-client-go/v2"`.

```go
import (
	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)
```

## Конструктор и опции

```go
func NewApi(token string, opt ...Opt) (*Api, error)
```

`Api` открывает шесть групп сервисов, все заполняются внутри `NewApi`:

```go
type Api struct {
	Bots          BotsAPI
	Upload        UploadAPI
	Chats         ChatsAPI
	Messages      MessagesAPI
	Comments      CommentsAPI
	Subscriptions SubscriptionsAPI
}
```

Хост по умолчанию — `platform-api2.max.ru` (`DefaultHostV2`); константа старого `platform-api.max.ru` существует только как `// Deprecated: not allowed` и не используется никогда, если ты сам не передал её в `WithBaseURL`. Авторизация — сырой заголовок `Authorization: <token>`, **без** префикса `Bearer`.

Функциональные опции (`Opt func(cli *client) error`):

| Опция | Эффект |
|---|---|
| `WithHTTPClient(cli HttpClient)` | подменить транспорт — сюда подставляется своё хранилище доверия CA; настройка корневого CA Минцифры, обязательного для исходящих вызовов `platform-api2.max.ru`, в [`tls-trust.md`](./tls-trust.md) |
| `WithBaseURL(baseURL string)` | переопределить схему и хост |
| `WithPollingPause(d time.Duration)` | пауза между повторами long polling (по умолчанию 1 с) |
| `WithPollingTimeout(d time.Duration)` | параметр запроса `timeout` для long polling (по умолчанию 30 с) |

```go
import (
	"net/http"
	"os"
	"time"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
)

func newClient() (*maxbot.Api, error) {
	httpClient := &http.Client{Timeout: 25 * time.Second}
	return maxbot.NewApi(
		os.Getenv("MAX_BOT_TOKEN"),
		maxbot.WithHTTPClient(httpClient),
		maxbot.WithPollingTimeout(30*time.Second),
	)
}
```

Никогда не ставь `InsecureSkipVerify` в `Transport` клиента `http.Client` — правильный способ доверять корневому CA Минцифры описан в `tls-trust.md`.

## Группы сервисов (точные сигнатуры)

Все методы принимают `ctx context.Context` первым аргументом (ниже для краткости опущен). Типы — в подпакете `model`, если не указано иное; `*maxbot.Message` и `*maxbot.Comment` — типы билдеров, описанные ниже.

| Группа | Метод | Возвращает |
|---|---|---|
| `Bots` | `GetMyInfo()` | `BotInfo` |
| | `EditMyInfo(patch BotPatch)` — устарел, для команд используй `PatchCommands` | `BotInfo` |
| | `PatchCommands(botPatch BotPatchCommands)` | `BotPatchCommands` |
| `Chats` | `GetChat(chatID int64)` | `Chat` |
| | `EditChat(chatID int64, patch ChatPatch)` | `Chat` |
| | `DeleteChat(chatID int64)` | `SimpleQueryResult` |
| | `SendAction(chatID int64, action SenderAction)` | `SimpleQueryResult` |
| | `GetPinnedMessage(chatID int64)` | `GetPinnedMessageResult` |
| | `PinMessage(chatID int64, messageID string, notify bool)` | `SimpleQueryResult` |
| | `UnpinMessage(chatID int64)` | `SimpleQueryResult` |
| | `GetMembership(chatID int64)` | `ChatMember` |
| | `LeaveChat(chatID int64)` | `SimpleQueryResult` |
| | `GetAdmins(chatID int64)` | `ChatMembersList` |
| | `SetAdmins(chatID int64, admins []ChatAdmin)` | `SimpleQueryResult` |
| | `DeleteAdmins(chatID, userID int64)` | `SimpleQueryResult` |
| | `GetMembers(chatID, marker, count int64, userIDs []int64)` — пагинация по marker | `ChatMembersList` |
| | `AddMembers(chatID int64, userIDs []int64)` | `SimpleQueryResult` |
| | `RemoveMember(chatID, userID int64, block bool)` | `SimpleQueryResult` |
| `Messages` | `GetMessages(chatID, from, to, count int64, messageIDs []string)` | `MessageList` |
| | `GetMessageByID(messageID string)` | `Message` |
| | `Send(msg *maxbot.Message)` | `SendMessageResult` |
| | `EditMessage(messageID string, body NewMessageBody)` | `SimpleQueryResult` |
| | `DeleteMessage(messageID string)` | `SimpleQueryResult` |
| | `AnswerOnCallback(callbackID string, answer CallbackAnswer)` | `SimpleQueryResult` |
| | `GetVideoAttachmentDetails(videoToken string)` | `VideoAttachmentDetails` |
| `Subscriptions` | `GetSubscriptions()` | `GetSubscriptionsResult` |
| | `Subscribe(url, secret string, updateTypes []string, version string)` | `SimpleQueryResult` |
| | `Unsubscribe(url string)` | `SimpleQueryResult` |
| | `GetUpdates(marker int64)` | `([]Update, int64, error)` |
| `Comments` | `GetComments(postID string, before, after, count int64, commentIds []string)` | `CommentList` |
| | `GetCommentByID(postID, commentID string)` | `Comment` |
| | `Send(postID string, comment *maxbot.Comment)` | `SendMessageResult` |
| | `Edit(postID, commentID string, comment *maxbot.Comment)` | `SendMessageResult` |
| | `Delete(postID, commentID string)` | `SendMessageResult` |
| `Upload` | `Upload(uploadType UploadType, reader io.Reader, name string, size int64)` | `(string, error)` |

Метода списка **`GET /chats` нет** — у `Chats` есть только `GetChat(chatID)` (один чат по числовому id). Эндпоинт удалён из API в июне 2026; отслеживай чаты сам по событиям `bot_added`, `bot_removed` и `bot_started` (см. `patterns.md`).

## Билдер сообщений (`maxbot.NewMessage()`)

Текучий, все сеттеры возвращают `*Message`: `SetUser`, `SetChat`, `SetText`, `SetFormat` (`model.FormatMarkdown` или `model.FormatHTML`), `SetDisableLinkPreview`, `AddImageUrl`, `AddSticker`, `AddContact`, `AddLocation(lat, lot float64)`, `AddShare`, `WithoutNotify`, `SetReply(text, id)`, `AddKeyboard`, `AddAttachByToken(token, model.AttachmentType)`, `AddAttachments([]model.Attachment)`.

- **Подводный камень:** `AddAttachments` **заменяет** весь срез вложений; все остальные методы `Add*` дописывают. Вызов `AddSticker(...)`, а затем `AddAttachments(...)` молча выбрасывает стикер.
- **Подводный камень:** сокращения `Reply(text, msg)` нет, хотя в `docs/02-listen-and-respond.md` оно показано, — используй `SetReply(text, id string)`.
- Id отправленного сообщения лежит в `result.Message.Body.Mid`, а не в поле верхнего уровня `MessageID`.

```go
import (
	"context"
	"fmt"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

func sendGreeting(ctx context.Context, api *maxbot.Api, chatID int64) error {
	msg := maxbot.NewMessage().
		SetChat(chatID).
		SetText("**Привет** от бота").
		SetFormat(model.FormatMarkdown)

	result, err := api.Messages.Send(ctx, msg)
	if err != nil {
		return fmt.Errorf("send message: %w", err)
	}
	_ = result.Message.Body.Mid // сохрани для последующего изменения, ответа или удаления
	return nil
}
```

## Билдер клавиатур (`model.NewKeyboard()`)

```go
func NewKeyboard() *Keyboard
func (k *Keyboard) AddRow() *KeyboardRow
func (k *Keyboard) Build() Attachment
```

Методы строки (цепочкой, вызываются на строке): `AddCallBack(text, payload)`, `AddLink(text, url)`, `AddGeoLocation(text string, quick bool)`, `AddContact(text)`, `AddMessage(text)`, `AddOpenApp(text string, botID int64)`, `AddClipboard(text, payload)`.

- **Подводный камень:** `AddOpenApp` кладёт *подпись* кнопки в поле `WebApp` (комментарий в исходнике: `// ignored, required`), а id бота — в `ContactID`; это не универсальная кнопка «открыть любой URL». Сам адрес мини-приложения настраивается на сервере для бота (настройки masterBot), а не передаётся здесь.
- **Подводный камень:** `AddCallback(text, intent, payload)` (со строчной `b`) помечен `// Deprecated: use AddCallBack`; аргумент `Intent` игнорируется.
- Числовые лимиты (≤ 210 кнопок, ≤ 30 рядов, ≤ 7 в ряду, ≤ 3 в ряду для link, open_app, request_geo_location, request_contact) в этом клиенте **не** проверяются — лимиты из DOCS см. в `bot-api.md`; их нарушение отклоняет сервер.

```go
import (
	"context"
	"fmt"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

func sendMenu(ctx context.Context, api *maxbot.Api, chatID int64) error {
	kb := model.NewKeyboard()
	kb.AddRow().
		AddLink("Открыть MAX", "https://max.ru").
		AddCallBack("Аудио", "audio").
		AddCallBack("Видео", "video")

	msg := maxbot.NewMessage().SetChat(chatID).SetText("Выберите:").AddKeyboard(kb)
	if _, err := api.Messages.Send(ctx, msg); err != nil {
		return fmt.Errorf("send menu: %w", err)
	}
	return nil
}
```

## Загрузки

`Upload.Upload(ctx, uploadType, reader, name, size) (token string, err error)`. Порядок:

1. Клиент вызывает `POST /uploads?type=<image|video|audio|file>` и получает **одноразовый, выданный сервером** `{token?, url}` — фиксированного хоста на тип в клиенте нет (и сам не хардкодь `iu.oneme.ru`, `fu.oneme.ru` и прочие; решает сервер).
2. Клиент отправляет файл потоком как `multipart/form-data` на этот `url`.
3. Токен приходит из ответа шага 1 для `UploadAudio` и `UploadVideo`, из тела ответа POST — для `UploadImage` и `UploadFile`.

- **Подводный камень:** у самого `Upload.Upload` **нет повторов** — одна попытка. Повтор на `attachment.not.ready` (см. «Ошибки» ниже) происходит в *следующем* вызове `Messages.Send` или `Comments.*`, который ссылается на токен, а не в вызове загрузки.
- **Подводный камень:** для `UploadImage`, если сервер вдруг вернёт больше одной записи размера фото, клиент берёт тот ключ карты Go, который переберёт первым, — результат недетерминирован.

```go
import (
	"context"
	"fmt"
	"os"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

func sendDocument(ctx context.Context, api *maxbot.Api, userID int64, path string) error {
	f, err := os.Open(path)
	if err != nil {
		return fmt.Errorf("open file: %w", err)
	}
	defer f.Close()

	info, err := f.Stat()
	if err != nil {
		return fmt.Errorf("stat file: %w", err)
	}

	token, err := api.Upload.Upload(ctx, model.UploadFile, f, info.Name(), info.Size())
	if err != nil {
		return fmt.Errorf("upload file: %w", err)
	}

	msg := maxbot.NewMessage().SetUser(userID).AddAttachByToken(token, model.AttachFile)
	if _, err := api.Messages.Send(ctx, msg); err != nil { // внутри повторяет на attachment.not.ready
		return fmt.Errorf("send document: %w", err)
	}
	return nil
}
```

## Long polling

`Subscriptions.GetUpdates(ctx, marker int64) ([]model.Update, int64, error)` → `GET /updates?limit=50&timeout=<pollTimeout>&marker=<marker>`. `limit` зафиксирован на 50 и не настраивается. Сохраняй возвращённый marker и передавай его в следующем вызове.

- **Подводный камень:** шаблон из вышестоящего `docs/01-your-first-bot.md` — `select { case <-ctx.Done(): default: ... }` с **пустым** блоком `ctx.Done()` — не выходит из цикла; он крутится вхолостую, пока `GetUpdates` сам не вернёт ошибку. Добавь явный `return`, как ниже.

```go
import (
	"context"
	"log"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

func pollUpdates(ctx context.Context, api *maxbot.Api, handle func(context.Context, model.Update)) {
	var marker int64
	for {
		select {
		case <-ctx.Done():
			return
		default:
		}

		updates, next, err := api.Subscriptions.GetUpdates(ctx, marker)
		if err != nil {
			log.Println("GetUpdates:", err)
			return
		}
		marker = next
		for _, update := range updates {
			handle(ctx, update)
		}
	}
}
```

## Вебхук

Подписка: `Subscriptions.Subscribe(ctx, url, secret, updateTypes, version)` → `POST /subscriptions`. Приём: `Api.GetHandler(handler UpdateHandler, secret string) http.HandlerFunc`, где `type UpdateHandler func(context.Context, model.Update)`. Монтируй его на любой путь через `net/http`. Требования к TLS, порту и расписанию повторов (только 443, HTTPS, автоотписка через 8 часов, ответ 200 за 30 секунд) действуют на стороне сервера — см. `bot-api.md`. Про корневой CA Минцифры для **исходящих** вызовов (не для входящего вебхука) — в `tls-trust.md`.

```go
import (
	"context"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
)

func subscribeWebhook(ctx context.Context, api *maxbot.Api, url, secret string) error {
	types := []string{"message_created", "message_callback", "bot_started"}
	_, err := api.Subscriptions.Subscribe(ctx, url, secret, types, "1")
	return err
}
```

**Замечание о безопасности:** собственная проверка секрета в `GetHandler` — это простое сравнение `secret != r.Header.Get(...)`, **не** за постоянное время (в отличие от `ValidateInitData` ниже, где используется `subtle.ConstantTimeCompare`). Если считаешь секрет вебхука границей безопасности, оберни его своей проверкой за постоянное время спереди:

```go
import (
	"crypto/subtle"
	"net/http"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
)

func secureWebhook(api *maxbot.Api, handler maxbot.UpdateHandler, secret string) http.HandlerFunc {
	inner := api.GetHandler(handler, secret)
	return func(w http.ResponseWriter, r *http.Request) {
		got := r.Header.Get("X-Max-Bot-Api-Secret")
		if subtle.ConstantTimeCompare([]byte(got), []byte(secret)) != 1 {
			http.Error(w, "forbidden", http.StatusForbidden)
			return
		}
		inner(w, r) // собственная (не постоянная по времени) проверка GetHandler теперь проходит тривиально
	}
}
```

`GetHandler` вызывает твой обработчик синхронно и при успехе не пишет тело ответа — `net/http` в Go отправит пустой `200 OK`. Держи обработчик быстрым; медленную работу отправляй в горутину сам (шаблон быстрого ответа с идемпотентностью — в `patterns.md`).

## Ответы на колбэки

`Messages.AnswerOnCallback(ctx, callbackID string, answer model.CallbackAnswer) (model.SimpleQueryResult, error)` → `POST /answers?callback_id=<id>`. `CallbackAnswer{Message *model.NewMessageBody, Notification *string}` — оба необязательны; задай `Message`, чтобы изменить сообщение, `Notification` — для тоста, или оба. DOCS ограничивает это ≤ 2 в секунду на чат — на стороне клиента не проверяется, поэтому ограничивай сам (см. `patterns.md`).

```go
import (
	"context"
	"fmt"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

func toast(ctx context.Context, api *maxbot.Api, callbackID, text string) error {
	answer := model.CallbackAnswer{Notification: &text}
	if _, err := api.Messages.AnswerOnCallback(ctx, callbackID, answer); err != nil {
		return fmt.Errorf("answer callback: %w", err)
	}
	return nil
}
```

## API комментариев

Живёт под `/messages/{postID}/comments[/{commentID}]` — `postID` это id сообщения. Билдер: `maxbot.NewComment(text string) *Comment` (по умолчанию `model.FormatMarkdown`), `SetFormat`, `SetLink(CommentLink{Type, Mid})`. `Send`, `Edit` и `Delete` повторяют на `attachment.not.ready` так же, как `Messages.Send`; `GetComments` и `GetCommentByID` — нет. Комментарии никогда не допускают `attachments` в теле запроса.

```go
import (
	"context"
	"fmt"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

func replyAsComment(ctx context.Context, api *maxbot.Api, postID string) error {
	comment := maxbot.NewComment("Спасибо за пост!").SetFormat(model.FormatMarkdown)
	if _, err := api.Comments.Send(ctx, postID, comment); err != nil {
		return fmt.Errorf("send comment: %w", err)
	}
	return nil
}
```

## `ValidateInitData` (initData мини-приложения)

```go
func ValidateInitData(initData string, botToken string) (res model.InitData, err error)
```

Встроено в клиент. Внутри выводит `secretKey = HMAC_SHA256(key="WebAppData", msg=botToken)`, затем сравнивает `HMAC_SHA256(key=secretKey, msg=dataCheckString)` через `subtle.ConstantTimeCompare` (за постоянное время, в отличие от проверки секрета вебхука выше) — эта часть проверки корректна. Полный алгоритм и формула хеша телефона мини-приложения описаны один раз в `webhooks-and-security.md`; здесь только точка входа на Go.

- **Подводный камень (проверено, v2.4.0):** `ValidateInitData` делает **двойное URL-декодирование** — сначала вызывает `url.QueryUnescape` по всей сырой строке `initData`, затем `url.ParseQuery` по результату, что процентно декодирует каждый ключ и значение *ещё раз*. Любое значение, которое законно содержит закодированные `&`, `=` или `%` (например, имя пользователя `Tom&Jerry`, закодированное как `Tom%2526Jerry` на внешнем слое), искажается до того, как проверочная строка собрана заново, поэтому пересчитанный хеш больше не совпадает и **корректный initData отклоняется**. Не считай эту функцию безопасным значением по умолчанию для недоверенных реальных пользовательских данных (имена, описания и т. п. могут содержать эти символы); используй отдельный валидатор с одним декодированием из `webhooks-and-security.md` либо перепроверь, что баг исправлен, прежде чем на неё полагаться.

```go
import (
	"fmt"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
)

func verifyInitData(initData, botToken string) error {
	data, err := maxbot.ValidateInitData(initData, botToken)
	if err != nil {
		return fmt.Errorf("invalid init data: %w", err)
	}
	_ = data.User // model.UserApp{ID, FirstName, LastName, LanguageCode, PhotoURL}
	return nil
}
```

## Ошибки, повторы — и отсутствие ограничения частоты

```go
type Error struct {
	Code    string `json:"code"`
	Err     string `json:"error,omitempty"`
	Message string `json:"message"`
}
func (e Error) IsAttachmentNotReady() bool // e.Code == "attachment.not.ready"

type TimeoutError struct{ Op, Reason string }
type NetworkError struct{ Op string; Err error }
```

Встроенные повторы узкие, это не общая устойчивость:

- `Messages.Send` и `Comments.{Send,Edit,Delete}` повторяют **только** при `Code == "attachment.not.ready"` (до 3 попыток, задержки 1 и 2 с). Любая другая ошибка API прерывает вызов сразу.
- `Subscriptions.GetUpdates` повторяет при любой ошибке, кроме `context.Canceled` и `context.DeadlineExceeded` (то же расписание).
- **Никакой другой метод не повторяет.** `Upload.Upload`, `Bots.*`, `Chats.*`, обычные `Messages.{Get*,Edit,Delete}`, `Subscriptions.{Subscribe,Unsubscribe,GetSubscriptions}` вызывают API один раз.
- **Клиент нигде не ограничивает себя по частоте.** Потолок 30 запросов в секунду из DOCS и потолок 2 в секунду на чат для ответов на колбэки — целиком твоя ответственность; рецепт ограничителя в `patterns.md`.

```go
import (
	"errors"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
)

func isRetryable(err error) bool {
	var apiErr *maxbot.Error
	if errors.As(err, &apiErr) {
		return apiErr.IsAttachmentNotReady()
	}
	var timeout *maxbot.TimeoutError
	return errors.As(err, &timeout)
}
```

## Подводные камни (не упомянутые выше)

1. `EditMyInfo` помечен `// Deprecated: use PatchCommands`, но `PatchCommands` патчит только `/me/commands` — для остальных полей профиля (например, описания) используй `EditMyInfo` и `model.BotPatch`, пока не появится не устаревшая альтернатива.
2. Публичное руководство `dev.max.ru/docs/chatbots/bots-coding/go` описывает API до v2 (`maxbot.New`, `GetBot`, `GetUpdates` на каналах), которого в исходниках v2.4.0 нет, — не следуй ему; используй сигнатуры с этой страницы.

Остальные подводные камни названы по месту, где они важны: перезапись в `AddAttachments` (билдер сообщений), переиспользование полей и числовые лимиты в `AddOpenApp` (билдер клавиатур), недетерминированный выбор токена изображения и отсутствие повторов загрузки (загрузки), проверка секрета вебхука не за постоянное время (вебхук), а также узкая область повторов только на `attachment.not.ready` и отсутствие встроенного ограничения частоты (ошибки).
