> Источник: DOCS https://dev.max.ru/docs-api + SCHEMA github.com/max-messenger/api-schema@1a4a502 · сверено 21.09.2026. Если что-то здесь выглядит устаревшим, проверяй их первыми.

# Справочник Bot API

## Базовый URL и авторизация

Базовый URL: `https://platform-api2.max.ru`. Обязателен с 19 июля 2026 (был `platform-api.max.ru`). Работа старого хоста не гарантируется — дата отключения не опубликована, но новые интеграции обязаны использовать `platform-api2.max.ru`. Этому хосту нужен Russian Trusted Root CA в хранилище доверия HTTP-клиента — настройка по языкам и средам в `tls-trust.md`.

Авторизация: сырой токен бота в заголовке `Authorization`, без префикса `Bearer`. Передача токена параметром запроса не поддерживается.

```bash
curl -X GET "https://platform-api2.max.ru/me" \
  -H "Authorization: $MAX_BOT_TOKEN"
```

## Лимиты частоты

| Область | Лимит |
|---|---|
| `platform-api2.max.ru`, все эндпоинты | 30 запросов в секунду |
| `POST /answers` | ≤ 2 ответа в секунду на диалог, чат или канал |
| Long polling (`GET /updates`) | минимум 300 мс между вызовами |

Заметка: в документации указано 30 запросов в секунду без уточнения, на токен бота или на всю платформу. Проектируй из расчёта не более 30 в секунду на токен бота.

## Таблица эндпоинтов

Все пути относительны базового URL. Эндпоинта `GET /chats` (список) нет — см. «Датированные изменения».

| Метод | Путь | Параметры запроса | Тело | Ответ | Назначение |
|---|---|---|---|---|---|
| GET | `/me` | — | — | BotInfo | Информация о текущем боте |
| PATCH | `/me/commands` | — | BotCommandsPatch | BotCommandsInfo | Изменить команды бота |
| GET | `/chats/{chatId}` | — | — | Chat | Информация о чате или канале |
| PATCH | `/chats/{chatId}` | — | ChatPatch | Chat | Изменить чат или канал |
| POST | `/chats/{chatId}/actions` | — | ActionRequestBody | SimpleQueryResult | Отправить действие бота (печатает и т. п.) |
| GET | `/chats/{chatId}/pin` | — | — | GetPinnedMessageResult | Получить закреплённое сообщение |
| PUT | `/chats/{chatId}/pin` | — | PinMessageBody | SimpleQueryResult | Закрепить сообщение |
| DELETE | `/chats/{chatId}/pin` | — | — | SimpleQueryResult | Открепить сообщение |
| GET | `/chats/{chatId}/members/me` | — | — | ChatMember | Членство самого бота |
| DELETE | `/chats/{chatId}/members/me` | — | — | SimpleQueryResult | Покинуть чат |
| GET | `/chats/{chatId}/members/admins` | — | — | ChatMembersList | Получить администраторов |
| POST | `/chats/{chatId}/members/admins` | — | ChatAdminsList | SimpleQueryResult | Задать администраторов (полная замена, несмотря на POST) |
| DELETE | `/chats/{chatId}/members/admins/{userId}` | — | — | SimpleQueryResult | Снять права администратора |
| GET | `/chats/{chatId}/members` | `user_ids`, `marker`, `count` (1–100, по умолчанию 20) | — | ChatMembersList | Получить участников |
| POST | `/chats/{chatId}/members` | — | UserIdsList (≤ 100 id) | ModifyMembersResult | Добавить участников — **не использовать, см. «Датированные изменения»** |
| DELETE | `/chats/{chatId}/members` | `user_id` (обязателен), `block` (bool, по умолчанию `false`) | — | SimpleQueryResult | Удалить участника |
| GET | `/subscriptions` | — | — | GetSubscriptionsResult | Список подписок вебхука |
| POST | `/subscriptions` | — | SubscriptionRequestBody | SimpleQueryResult | Подписаться на вебхук |
| DELETE | `/subscriptions` | `url` (обязателен) | — | SimpleQueryResult | Отписаться |
| POST | `/uploads` | `type` (обязателен: `image`, `video`, `audio`, `file`) | двоичные данные (multipart или докачиваемые) | UploadEndpoint | Получить URL и токен загрузки |
| GET | `/messages` | `chat_id`, `message_ids`, `from`/`to` (устарели), `before`, `after`, `count` (1–100, по умолчанию 50) | — | MessageList | Получить сообщения (в обратном хронологическом порядке) |
| POST | `/messages` | `user_id`, `chat_id`, `disable_link_preview` (bool, по умолчанию `false`) | NewMessageBody | SendMessageResult | Отправить сообщение |
| PUT | `/messages` | `message_id` (обязателен) | NewMessageBody | SimpleQueryResult | Изменить сообщение |
| DELETE | `/messages` | `message_id` (обязателен) | — | SimpleQueryResult | Удалить сообщение |
| GET | `/messages/{messageId}` | — | — | Message | Получить одно сообщение |
| GET | `/messages/{messageId}/comments` | `comment_ids`, `before`, `after`, `count` (1–100, по умолчанию 50) | — | CommentMessageList | Комментарии к посту |
| POST | `/messages/{messageId}/comments` | `disable_link_preview` | NewCommentBody | SendCommentResult | Отправить комментарий (без вложений) |
| PUT | `/messages/{messageId}/comments` | `comment_id` (обязателен) | NewCommentBody | SimpleQueryResult | Изменить комментарий |
| DELETE | `/messages/{messageId}/comments` | `comment_id` (обязателен) | — | SimpleQueryResult | Удалить комментарий |
| GET | `/messages/{messageId}/comments/{commentId}` | — | — | CommentMessage | Получить один комментарий |
| GET | `/videos/{videoToken}` | — | — | VideoAttachmentDetails | URL воспроизведения и метаданные видео |
| POST | `/answers` | `callback_id` (обязателен, непустой), `disable_link_preview` | CallbackAnswer | SimpleQueryResult | Ответить на колбэк нажатия кнопки |
| GET | `/updates` | `limit` (1–1000, по умолчанию 100), `timeout` (0–90 с, по умолчанию 30), `marker` (nullable int64), `types` (csv) | — | UpdateList | Long polling обновлений |

### Параметры, которые идут в запрос, а не в тело, — частые ошибки

- `disable_link_preview` — **параметр запроса** только у `POST /messages`, `POST /messages/{messageId}/comments` и `POST /answers`; `PUT /messages` и `PUT .../comments` такого параметра не принимают. Это **не** поле `NewMessageBody`, `NewCommentBody` или `CallbackAnswer.message`.
- `message_id` (изменение и удаление сообщения), `comment_id` (изменение и удаление комментария), `callback_id` (`POST /answers`), `url` (`DELETE /subscriptions`), `user_id` и `block` (`DELETE /chats/{chatId}/members`) — всё это параметры запроса, а не поля тела.
- `user_id` и `chat_id` у `POST /messages` — параметры запроса, выбирающие получателя; получатель никогда не входит в `NewMessageBody`.

### Примечательное поведение отдельных эндпоинтов

- `PUT /messages` (изменение): `attachments: null` в теле сохраняет существующие вложения, `attachments: []` их очищает.
- `DELETE /messages` и `PUT`/`DELETE .../comments` требуют, чтобы у бота было административное право `delete`, `edit` или `write` (см. `objects-and-updates.md` → ChatAdminPermission), а оно само требует `read_all_messages`.
- `POST /chats/{chatId}/members/admins` ведёт себя как полная замена через `PUT`, несмотря на HTTP-глагол: повторные вызовы полностью перезаписывают набор прав администратора.
- Комментарии (`/messages/{messageId}/comments/*`) доступны только в каналах, появились в августе 2026 и никогда не несут вложений или публичного `url`.

## Поток загрузки (все типы медиавложений)

Три шага, одинаковых по форме для `image`, `video`, `audio` и `file`:

1. `POST /uploads?type={image|video|audio|file}` → `UploadEndpoint {url, token?}`.
2. Загрузи двоичные данные на полученный `url` — **не** на фиксированный хост; URL из ответа — единственный допустимый адрес для этой загрузки. Два режима передачи: **multipart** (`Content-Type: multipart/form-data`, один запрос) или **докачиваемый** (любой другой `Content-Type` или его отсутствие; поддерживает `Content-Range` для загрузки частями и возобновления — `GET` по URL загрузки возвращает текущий статус; `REQUESTED_RANGE_NOT_SATISFIABLE` или `INTERNAL_SERVER_ERROR` означают, что надо начинать заново).
3. Прикрепи получившийся объект `{type, payload}` к сообщению или комментарию.

```bash
curl -X POST "https://platform-api2.max.ru/uploads?type=video" \
  -H "Authorization: $MAX_BOT_TOKEN"
```

```json
{"url": "https://<upload-host>/upload.do?..."}
```

```bash
curl -i -X POST -H "Content-Type: multipart/form-data" \
  -F "data=@movie.mp4" "https://<upload-host>/upload.do?..."
```

```json
{"token": "<upload-token>"}
```

```json
{
  "text": "Сообщение с видео",
  "attachments": [
    {"type": "video", "payload": {"token": "<upload-token>"}}
  ]
}
```

Заметки:

- Хосты загрузки различаются по типу и не являются стабильными документированными значениями для хардкода — всегда используй `url`, который вернул `POST /uploads` для этого запроса. Не предполагай фиксированное имя хоста на тип.
- Изображения могут вообще пропустить `/uploads`: передай внешний `url` прямо в `PhotoAttachmentRequestPayload.url` запроса. У других типов медиа такого сокращения нет.
- Один файл на URL загрузки — для каждого нового файла вызывай `POST /uploads` снова. Срок жизни самого URL не оговорён, но он одноразовый.
- `type=photo` больше не принимается; используй `type=image`.
- Момент, когда становится доступен `token` (на шаге 1 или только после шага 2), в формулировках самой DOCS различается по типам и внутренне противоречив для видео и аудио против изображений и файлов, — не полагайся на наличие `token` до того, как увидел его в фактическом ответе.
- Ошибка `attachment.not.ready`: сервер ещё не закончил обработку загруженного медиа. Возвращается как `{"code": "attachment.not.ready", "message": "Key: errors.process.attachment.file.not.processed"}` на вызове *отправки сообщения* с кодом `400`. Смягчай повтором отправки с задержкой либо заранее загружай и переиспользуй токены для часто отправляемых файлов.

## Правила сочетания вложений

Авторитетен только один набор правил (DOCS; формулировка схемы «должно быть единственным вложением» для `file` перекрыта — см. `objects-and-updates.md`):

- `image` и `video`: сочетаются друг с другом и с **не более чем одним** вложением `inline_keyboard`. Всего медиавложений (image и video) в сообщении: **≤ 12**.
- `file`: сочетается **только с одним** `inline_keyboard` — никогда с `image`, `video` или другим `file`. Ровно один `file` на сообщение.
- `audio`, `contact`, `sticker`: каждое должно быть единственным вложением сообщения (ни клавиатуры, ни другого медиа) — формулировка схемы, контрпримеров в DOCS не найдено.
- `location`, `share`: в таблице сочетаний DOCS не описаны; считай их единственным вложением, пока не проверил обратное живой отправкой.

Примеры допустимых сочетаний из DOCS: 6 видео + 5 изображений + 1 inline_keyboard; 12 видео; 12 изображений; 11 видео + 1 inline_keyboard; 11 изображений + 1 inline_keyboard; 6 видео + 6 изображений; 1 file + 1 inline_keyboard.

## Лимиты

| Лимит | Значение |
|---|---|
| Длина текста сообщения или комментария | 4000 символов сырой строки `text` — считается каждый символ: любой алфавит, цифры, пробелы, переводы строк, эмодзи и символы markdown- или HTML-разметки. Символы, а не байты (кириллица в UTF-8 — 2 байта, но 1 символ) |
| Название чата | 1–200 символов |
| Текст кнопки | 1–128 символов |
| `CallbackButton.payload` и `ClipboardButton.payload` | ≤ 1024 символов |
| `LinkButton.url` | ≤ 2048 символов |
| `LinkMarkup.url` (разметка в ответе) | 1–2048 символов |
| `OpenAppButton.payload` | ≤ 512 символов, шаблон `^[\w-]*$` |
| Payload диплинка `start=` (ссылка на бота) | ≤ 128 символов — более длинный отбрасывается и до бота не доходит |
| Payload диплинка `startapp=` (ссылка на мини-приложение) | ≤ 512 символов, допустимы `A-Za-z0-9_-` |
| `BotCommand.name` | 1–64 символа |
| `BotCommand.description` | 1–128 символов |
| Количество команд бота | ≤ 32 |
| `UserIdsList` (добавление участников) | ≤ 100 id на запрос |
| `count` у `GET /messages` и `.../comments` | 1–100, по умолчанию 50 |
| `count` у `GET /chats/{chatId}/members` | 1–100, по умолчанию 20 |
| `limit` у `GET /updates` | 1–1000, по умолчанию 100 |
| `timeout` у `GET /updates` | 0–90 с, по умолчанию 30 |
| Минимальный интервал long polling | 300 мс |
| Секрет вебхука | 5–256 символов, `^[\w-]+$` (A–Z, a–z, 0–9, `_`, `-`) |
| Таймаут ответа вебхука | HTTP 200 за 30 с |
| Число повторов вебхука | до 10, экспонента ×2,5 (60 с, 150 с, 375 с, …) |
| Автоотписка вебхука | после 8 часов без успешной доставки (200) |
| Порт вебхука | только 443 |
| Частота `POST /answers` | ≤ 2 в секунду на диалог, чат или канал |
| Общая частота API | 30 запросов в секунду на `platform-api2.max.ru` |
| Размер изображения | ≤ 50 МБ **и** ≤ 7680×7680 px (нужно и то и другое) |
| Размер видео | ≤ 250 МБ |
| Размер аудио | ≤ 256 МБ **и** ≤ 60 мин (нужно и то и другое) |
| Размер файла | ≤ 4 ГБ |
| Клавиатура | ≤ 210 кнопок всего, ≤ 30 рядов, ≤ 7 в ряду (≤ 3 для `link`, `open_app`, `request_geo_location`, `request_contact`) — только по DOCS, схемой не проверяется (у `Keyboard.buttons` нет `maxItems`); сервер отклоняет нарушения, хотя валидатор по одной схеме их пропустил бы |
| Потолок сочетания медиа | ≤ 12 вложений image и video на сообщение; `file` сочетается только с одной клавиатурой (см. выше) |
| `InlineKeyboardAttachmentRequestPayload.buttons` | `minItems: 1` (проверяется схемой) |
| Ботов на профиль юрлица или ИП | 5 |
| Ботов на профиль самозанятого | 2 |
| Длина никнейма бота | 11–60 символов |
| Публичных каналов (у верифицированных юрлиц и ИП) | 10 |

Заметка: `start=` (бот) и `startapp=` (мини-приложение) — разные ссылки с разными потолками: 128 и 512. Поле схемы `BotStartedUpdate.payload` допускает до 512 символов, но это лишь ширина поля; ссылки бота с `start=` по-прежнему ограничены 128.

## Ошибки

### Коды состояния HTTP

`200` — успех, `400` — неверный запрос, `401` — ошибка авторизации, `403` — запрещено, `404` — не найдено, `405` — метод не разрешён, `429` — превышен лимит частоты, `500` — внутренняя ошибка, `503` — сервис недоступен.

Заметка: обзорная страница DOCS не указывает 403 в сводном списке, но страницы отдельных методов (например, `PATCH /chats/{chatId}`, `POST /chats/{chatId}/members`) и схема его используют — считай 403 реальным и обрабатывай.

### Общая форма ошибки

```json
{"code": "chat.denied", "message": "Forwarding messages from this chat or channel is prohibited"}
```

`code` и `message` обязательны; иногда появляется необязательное поле `error`.

### Именованные коды ошибок, которые действительно документированы

Единого канонического списка кодов нет ни в SCHEMA, ни в DOCS — документированы только эти; не подавай список как исчерпывающий:

| Код | Значение |
|---|---|
| `chat.denied` | Пересылка из этого чата или канала запрещена (403 на `POST /messages`) |
| `attachment.not.ready` | Медиа ещё не обработано на сервере (см. «Поток загрузки») |
| `add.participant.privacy` | Настройки приватности не дали добавить участника |
| `add.participant.not.found` | Пользователи для добавления не найдены |
| `File extension is forbidden` | Расширение загружаемого файла не поддерживается (сырая строка сообщения, а не формальный `code`) |
