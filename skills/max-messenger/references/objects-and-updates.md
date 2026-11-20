> Источник: DOCS https://dev.max.ru/docs-api + SCHEMA github.com/max-messenger/api-schema@1a4a502 · сверено 21.09.2026. Если что-то здесь выглядит устаревшим, проверяй их первыми.

# Справочник объектов и обновлений

Списки полей ниже взяты из `schema.yaml`. Поля с пометкой `nullable` или «необязательно» отмечены; неотмеченные обязательны.

## Тела сообщений (запрос)

### NewMessageBody (тело `POST` и `PUT /messages`)

| Поле | Тип | Заметки |
|---|---|---|
| `text` | string, nullable | не более 4000 символов |
| `attachments` | AttachmentRequest[], nullable | см. ниже; правила сочетания в `bot-api.md` |
| `link` | NewMessageLink, nullable | пересылка или ответ |
| `notify` | bool | по умолчанию `true` |
| `format` | `markdown` или `html`, nullable | см. `formatting.md` |

`NewMessageLink`: `type` (`forward` или `reply`, обязателен) плюс `mid` (id сообщения, обязателен).

### NewCommentBody (тело `POST` и `PUT .../comments`)

Та же форма без `attachments` и `notify`: `text` (nullable, не более 4000), `link` (NewMessageLink, nullable), `format`. Вложения в комментариях не допускаются никогда.

## Объекты сообщений (ответ)

### Message

| Поле | Тип | Заметки |
|---|---|---|
| `sender` | User, nullable | `null`, если опубликовано как канал |
| `recipient` | Recipient | обязательно |
| `timestamp` | int64 | обязательно |
| `link` | LinkedMessage, nullable | |
| `body` | MessageBody | обязательно |
| `stat` | MessageStat, nullable | только для каналов, `{views}` |
| `url` | string, nullable | |

### MessageBody

`mid` (string, обязательно), `seq` (int64, обязательно), `text` (string, nullable), `attachments` (Attachment[], nullable), `markup` (MarkupElement[], nullable).

### Recipient

`chat_id` (nullable), `chat_type` (ChatType, обязательно), `user_id` (nullable), `post_id` (nullable — только для комментариев).

### CommentMessage и CommentMessageBody

Повторяют `Message` и `MessageBody`, но без `attachments` и публичного `url`. `recipient` у комментария есть только в каналах. `stat` — просмотры, только в контексте `GET /messages`.

### MessageStat

`{views: int}`, обязательно.

## Вложения — ответ (`Attachment`, дискриминатор `type`)

| `type` | Схема | Поля payload |
|---|---|---|
| `image` | PhotoAttachment | `photo_id` (int64), `token`, `url` — все обязательны |
| `video` | VideoAttachment | `url` и `token` (MediaAttachmentPayload) плюс `thumbnail`, `width`, `height`, `duration` (секунды), все nullable |
| `audio` | AudioAttachment | MediaAttachmentPayload плюс `transcription` (nullable) |
| `file` | FileAttachment | FileAttachmentPayload (`url` и `token`) плюс `filename` и `size` (байты) — все обязательны |
| `sticker` | StickerAttachment | `code`, `width`, `height` — все обязательны |
| `contact` | ContactAttachment | `vcf_info` (nullable), `hash` (nullable), `max_info` (User, nullable) |
| `inline_keyboard` | InlineKeyboardAttachment | `Keyboard{buttons}` |
| `share` | ShareAttachment | `url` и `token` (nullable) плюс `title`, `description`, `image_url` (все nullable) |
| `location` | LocationAttachment | `latitude`, `longitude` (double, оба обязательны) — без обёртки payload |

`GET /videos/{videoToken}` → `VideoAttachmentDetails`: `token`, `urls` (nullable — `mp4_1080/720/480/360/240/144` и `hls`), `thumbnail` (nullable), `width`, `height`, `duration` (все обязательны, кроме `urls` и `thumbnail`).

## Вложения — запрос (`AttachmentRequest`, дискриминатор `type`)

Типы: `image`, `video`, `audio`, `file`, `sticker`, `contact`, `inline_keyboard`, `location`, `share`.

- `PhotoAttachmentRequestPayload`: **взаимоисключающие** поля — `url` (внешний адрес изображения), `token` (токен существующего вложения), `photos` (карта `PhotoToken{token}` из загрузки).
- `video`, `audio`, `file`: только payload `UploadedInfo{token}`.
- `ContactAttachmentRequestPayload`: `name`, `contact_id` (UserId), `vcf_info`, `vcf_phone` — все необязательны.
- `InlineKeyboardAttachmentRequestPayload.buttons`: `minItems: 1` (проверяется схемой — минимум один ряд).
- В описании схемы сказано, что запросы `audio`, `file`, `contact` и `sticker` «ДОЛЖНЫ быть единственным вложением в сообщении». Таблица сочетаний в DOCS противоречит этому для `file` (file плюс один inline_keyboard — допустимое документированное сочетание). Для `file` следуй правилам сочетания из `bot-api.md`, а не этой формулировке схемы; для `audio`, `contact` и `sticker` считай «единственное вложение» по-прежнему верным, поскольку контрпримеров в DOCS нет.
- Перечисление `UploadType` (для `POST /uploads?type=`): `image | video | audio | file` — без `photo` (удалён, см. `bot-api.md`).

## Кнопки (`Button`, дискриминатор `type`)

Базовый `Button`: `type` плюс `text` (string, 1–128 символов) — оба обязательны.

| `type` | Схема | Дополнительные поля |
|---|---|---|
| `callback` | CallbackButton | `payload` (string, ≤ 1024, обязательно) |
| `link` | LinkButton | `url` (string, ≤ 2048, обязательно) |
| `message` | MessageButton | ничего сверх базового |
| `request_contact` | RequestContactButton | ничего сверх базового |
| `request_geo_location` | RequestGeoLocationButton | `quick` (bool, по умолчанию `false` — пропустить подтверждение пользователя) |
| `open_app` | OpenAppButton | `payload` (nullable, шаблон `^[\w-]*$`, ≤ 512), `web_app` (string, **обязательно** — публичное имя бота, связанного с мини-приложением), `contact_id` (UserId, nullable) |
| `clipboard` | ClipboardButton | `payload` (string, ≤ 1024, обязательно) |

`Keyboard`: `{buttons: Button[][]}` — двумерный массив (ряды кнопок), обязателен. Потолки на ряды и кнопки (210, 30, 7, 3) есть только в DOCS и схемой не проверяются — см. таблицу лимитов в `bot-api.md`.

```json
{
  "type": "inline_keyboard",
  "payload": {
    "buttons": [
      [{"type": "callback", "text": "Подтвердить", "payload": "confirm"}]
    ]
  }
}
```

## Обновление (19 значений `update_type`, дискриминатор `update_type`)

| `update_type` | Схема | Ключевые поля |
|---|---|---|
| `message_created` | MessageCreatedUpdate | `message` (обязательно), `user_locale` (nullable, только диалоги) |
| `message_callback` | MessageCallbackUpdate | `callback` (обязательно), `message` (nullable — может отсутствовать, если удалено), `user_locale` (nullable) |
| `message_edited` | MessageEditedUpdate | `message` (обязательно) |
| `message_removed` | MessageRemovedUpdate | `message_id`, `chat_id`, `user_id` (все обязательны) |
| `comment_created` | CommentCreatedUpdate | `message` (обязательно — в схеме типизировано как `Message`, а не `CommentMessage`) |
| `comment_edited` | CommentEditedUpdate | `message` (обязательно) |
| `comment_removed` | CommentRemovedUpdate | `message_id`, `chat_id`, `user_id`, `post_id` (все обязательны) |
| `bot_added` | BotAddedToChatUpdate | `chat_id`, `user`, `is_channel` (все обязательны) |
| `bot_removed` | BotRemovedFromChatUpdate | `chat_id`, `user`, `is_channel` (все обязательны) |
| `user_added` | UserAddedToChatUpdate | `chat_id`, `user`, `is_channel` (обязательны), `inviter_id` (nullable) |
| `user_removed` | UserRemovedFromChatUpdate | `chat_id`, `user`, `is_channel` (обязательны), `admin_id` (необязательно) |
| `bot_started` | BotStartedUpdate | `chat_id`, `user` (обязательны), `payload` (nullable, не более 512 — payload диплинка `start`), `user_locale` |
| `bot_stopped` | BotStoppedUpdate | `chat_id`, `user` (обязательны), `user_locale` |
| `dialog_cleared` | DialogClearedUpdate | `chat_id`, `user` (обязательны), `user_locale` |
| `dialog_removed` | DialogRemovedUpdate | `chat_id`, `user` (обязательны), `user_locale` |
| `dialog_muted` | DialogMutedUpdate | `chat_id`, `user`, `muted_until` (int64, обязательно), `user_locale` |
| `dialog_unmuted` | DialogUnmutedUpdate | `chat_id`, `user` (обязательны), `user_locale` |
| `chat_title_changed` | ChatTitleChangedUpdate | `chat_id`, `user`, `title` (все обязательны) |
| `bot_admin_permissions_changed` | BotAdminPermissionsChangedUpdate | `chat_id`, `user_id`, `bot_id`, `is_channel`, `is_admin` (все обязательны), `permissions` (nullable массив) |

Заметка: типы обновлений, связанные с комментариями (`comment_created`, `comment_edited`, `comment_removed`), появились в августе 2026 вместе с API комментариев.

### Callback и CallbackAnswer

- `Callback` (payload обновления `message_callback`): `timestamp`, `callback_id`, `user` (все обязательны), `payload` (string, по схеме обязателен — может быть пустым для кнопок `message` и `request_contact`, которые payload не несут).
- `CallbackAnswer` (тело `POST /answers`): `message` (NewMessageBody, nullable — заполни, чтобы изменить исходное сообщение), `notification` (string, nullable — одноразовый тост). Оба необязательны, можно сочетать.

## Chat, ChatMember, User

### Chat

`chat_id`, `type` (ChatType: `dialog`, `chat` или `channel`), `status` (ChatStatus: `active`, `removed`, `left`, `closed`, `suspended` — `suspended` только для диалогов), `title` (nullable), `icon` (`{url}`, nullable), `last_event_time`, `participants_count` (для диалогов всегда 2), `owner_id` (nullable, видно только администраторам), `participants` (карта user_id → последняя активность, только для администраторов, nullable), `is_public` (для диалогов всегда `false`), `link` (nullable), `description` (nullable), `dialog_with_user` (UserWithPhoto, только диалоги, nullable), `messages_count` (nullable, недоступно для диалогов), `pinned_message` (Message, nullable, только в `GET` одного чата).

### ChatPatch (тело `PATCH /chats/{chatId}`)

`icon` (PhotoAttachmentRequestPayload, nullable), `title` (1–200 символов, nullable), `description` (≤ 16000 символов, nullable — пустая строка удаляет описание, появилось в августе 2026), `pin` (id сообщения, nullable — чтобы открепить, используй `DELETE /pin`), `notify` (bool, по умолчанию `true`).

### User

`user_id`, `first_name`, `is_bot` (обязательны); `last_name`, `username`, `last_activity_time` (nullable).

### UserWithPhoto (расширяет User)

Добавляет `description` (≤ 16000, nullable), `avatar_url`, `full_avatar_url` (nullable).

### ChatMember (расширяет UserWithPhoto)

Добавляет `last_access_time`, `is_owner`, `is_admin`, `join_time` (все обязательны), `permissions` (ChatAdminPermission[], nullable), `alias` (nullable).

### ChatAdminPermission (11 значений)

`read_all_messages`, `add_remove_members`, `add_admins`, `change_chat_info`, `pin_message`, `edit_link`, `write`, `edit`, `delete`, `can_call`, `view_stats`.

Заметка: `edit`, `delete`, `write` и `pin_message` требуют, чтобы `read_all_messages` был выдан вместе или уже присутствовал, иначе сервер вернёт ошибку. Устаревшие синонимы в ответах: `edit_message` → `edit`, `delete_message` → `delete`, `post_edit_delete_message` → `write` (при назначении прав используй новые имена). `add_remove_members` работает для ботов только в чатах, не в каналах. `can_call` и `view_stats` вручную назначить нельзя (автоматические или только для владельца). Этот текст про семантику прав есть только в DOCS, в схеме его нет.

## Объекты комментариев

`NewCommentBody`, `CommentMessage`, `CommentMessageBody` — см. выше. `SendCommentResult`: `{message: CommentMessage}`, обязательно. `CommentMessageList`: `{messages: CommentMessage[]}`, обязательно.

## MarkupElement (разметка текста в ответе, 10 типов)

База: `type`, `from` (int32, начальный индекс), `length` (int32) — все обязательны. Типы: `strong`, `emphasized`, `monospaced`, `link`, `strikethrough`, `underline`, `user_mention`, `heading`, `highlighted`, `quote`.

- `LinkMarkup` добавляет `url` (1–2048 символов).
- `UserMentionMarkup` добавляет `user_link` (nullable `@username`) и `user_id` (nullable UserId).
- Все остальные типы (`strong`, `emphasized`, `monospaced`, `strikethrough`, `underline`, `heading`, `highlighted`, `quote`) дополнительных полей сверх базы не несут.

Заметка: свободное описание дискриминатора в схеме перечисляет значение «header», но фактический ключ отображения и объект — `heading` и `HeadingMarkup`; используй `heading`, именно его присылает API.
