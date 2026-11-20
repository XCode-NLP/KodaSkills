> Источник: TS github.com/max-messenger/max-bot-api-client-ts@963ba4a (npm `@maxhub/max-bot-api`
> **0.3.1**) · сверено 21.09.2026. Если это выглядит устаревшим, проверяй сначала `CHANGELOG.md` и
> `docs/*.md` в репозитории — публичные страницы руководства иногда отстают от пакета.

# Клиент TypeScript и JavaScript (`@maxhub/max-bot-api`)

**Содержание:** [Установка и требования](#установка-и-требования) · [Bot — конструктор и опции](#bot--конструктор-и-опции) · [bot.start() — polling или вебхук](#botstart--polling-или-вебхук) · [Composer и API обработчиков](#composer-и-api-обработчиков) · [Context](#context) · [Клавиатуры и кнопки](#клавиатуры-и-кнопки) · [Вложения и загрузки](#вложения-и-загрузки) · [Сессии и сценарии](#сессии-и-сценарии) · [Сырой доступ к API](#сырой-доступ-к-api) · [Ошибки, повторы, ограничение частоты](#ошибки-повторы-ограничение-частоты) · [Подводные камни](#подводные-камни)

Официальный фреймворк ботов на TS и JS для MAX. В одном пакете: доступ к Bot API, обработка обновлений (`Composer`), сессии, сценарии и хостинг вебхука.

## Установка и требования

- Пакет: `@maxhub/max-bot-api`, текущая версия **0.3.1**. Игнорируй git-тег `v1.0.0` в репозитории — это устаревшая ошибочная метка (24.06.2026, `package.json` в том коммите говорит `0.2.2`); ориентируйся на версию в npm.
- Требуется **Node ≥ 20.19.0**.
- **Только ESM**: в `exports` нет условия `require`. Импортируй через `import`, а не `require`; если проект на CommonJS, переходи на ESM или используй динамический `import()`.
- Зависимости времени выполнения: `debug`, `form-data`, `vcf`. Peer-зависимостей нет.
- Установка: `npm install @maxhub/max-bot-api` (либо `yarn add` / `pnpm add`).

## `Bot` — конструктор и опции

```typescript
import { Bot } from '@maxhub/max-bot-api';

const bot = new Bot(process.env.MAX_BOT_TOKEN ?? '');
```

`new Bot(token, config?)` — `config` имеет тип `Partial<{ clientOptions, contextType }>`:

| Опция | Тип | Заметки |
|---|---|---|
| `clientOptions.baseUrl` | `string` | По умолчанию `https://platform-api2.max.ru`. Старый хост есть в исходниках только закомментированной строкой `@deprecated` — никогда его не задавай. |
| `clientOptions.fetch` | `(input, init) => Promise<Response>` | Свой fetch только для JSON-вызовов Bot API (`/me`, `/updates`, `/messages`, вызов `/uploads`, выдающий URL). **Не** покрывает сырой сокетный транспорт загрузки файлов — см. «Вложения». Используй его, чтобы подставить fetch, знающий про CA; см. `references/tls-trust.md`. |
| `contextType` | `new (...args) => Ctx` | Свой подкласс `Context`, по умолчанию `Context`. |

`Authorization` — сырой заголовок, равный строке токена: без префикса `Bearer` и без параметра запроса. Пустой токен замыкается локально на синтетический 401 без сетевого вызова.

`bot.catch((err, ctx) => void)` переопределяет обработку ошибок; обработчик по умолчанию ставит `process.exitCode = 1`, логирует и пробрасывает ошибку дальше — в продакшене всегда ставь свой, чтобы одно плохое обновление не роняло процесс.

## `bot.start()` — polling или вебхук

```typescript
type StartConfig =
  | { mode: 'polling'; options?: { allowedUpdates?: UpdateType[]; retry?: boolean } }
  | { mode: 'webhook'; options: WebhookOptions & { allowedUpdates?: UpdateType[] } };
```

`mode` — обязательный дискриминант *объекта опций*, а не отдельный аргумент: вызов вроде `bot.start({ allowedUpdates: [...] })` без ключа `mode` не соответствует этому типу и не скомпилируется при `strict` TypeScript, хотя он и встречается в собственном примере пакета `showcase-bot.ts`. Всегда указывай `mode`.

- `bot.start()` без аргумента означает `{ mode: 'polling' }`.
- Перед запуском `start()` всегда вызывает `api.getMyInfo()`, чтобы заполнить `botInfo`: плохой токен падает быстро, до запуска любого обработчика.
- **Режим polling безусловно сначала очищает все существующие подписки вебхука** (`Webhook.clearSubscriptions`, без фильтра по `activeUrl`). Переключение бота с вебхука на polling молча снимает *другие* URL вебхуков, зарегистрированные на этот токен, а не только твой.
- `retry` по умолчанию `true`: при необработанной ошибке polling весь цикл перезапускается после ровной паузы 5 с. Независимо от этого внутренний транспорт polling повторяет `429`, `5xx` и сетевые ошибки со своей задержкой (5 с с удвоением до потолка 60 с) — раньше, чем сработает внешний перезапуск.
- `bot.stop()` устарел; используй `bot.stopPolling()`.

### Режим вебхука — три способа запустить

```typescript
import { Bot } from '@maxhub/max-bot-api';
import express from 'express';

const bot = new Bot(process.env.MAX_BOT_TOKEN ?? '');

// 1. Отдать HTTP-сервер целиком SDK.
async function runOwnServer(): Promise<void> {
  await bot.start({
    mode: 'webhook',
    options: {
      domain: process.env.PUBLIC_DOMAIN ?? 'https://example.com',
      port: 3000,
      secret: process.env.MAX_WEBHOOK_SECRET,
    },
  });
}

// 2. Смонтировать колбэк на своём сервере (Express, Fastify, чистый node:http — подойдёт любая
//    сырая сигнатура (req, res)). Подписку и очистку старых подписок это НЕ делает.
function mountOnExpress(app: express.Express): void {
  const handler = bot.webhookCallback({
    domain: process.env.PUBLIC_DOMAIN ?? 'https://example.com',
    secret: process.env.MAX_WEBHOOK_SECRET,
  });
  app.post('/webhook', (req, res) => handler(req, res));
  void bot.api.subscribe(
    'https://example.com/webhook',
    process.env.MAX_WEBHOOK_SECRET,
    undefined,
  );
}

// 3. Подписку зарегистрирует SDK, но HTTP-сервер всё равно твой.
async function createThenMount(app: express.Express): Promise<void> {
  const handler = await bot.createWebhook({
    domain: process.env.PUBLIC_DOMAIN ?? 'https://example.com',
    secret: process.env.MAX_WEBHOOK_SECRET,
  });
  app.post('/webhook', (req, res) => handler(req, res));
}

void runOwnServer;
void mountOnExpress;
void createThenMount;
```

`WebhookOptions = { domain: string; port?: number /* по умолчанию 3000 */; path?: string; secret?: string }`. Если `path` не указан, он генерируется из хеша токена (`/webhook/${sha256(token)}`) — стабилен между перезапусками, но это защита лишь через незнание; всё равно задавай `secret` для настоящей проверки. `Webhook.getWebhookUrl` всегда принудительно ставит `https://`, что бы ты ни передал в `domain`.

Встроенный HTTP-обработчик принимает только `POST` на точный путь хука (`404` на всё остальное), возвращает `400 Invalid JSON` на неразбираемое тело и — что важно — отправляет **`200 OK` в MAX до запуска цепочки твоих middleware**. Ошибки, выброшенные глубоко в обработчиках, перехватываются и только пишутся в `debug()`, в MAX они не уходят; к моменту срабатывания `bot.catch()` MAX уже получил свой 200 и повторять не будет. Включи `DEBUG=max:*`, если обновления из вебхука будто молча исчезают.

Подробности проверки секрета (имя заголовка, сравнение за постоянное время, 404 при несовпадении) — в `references/webhooks-and-security.md` (все формулы проверки с проверенным кодом).

## Composer и API обработчиков

`Bot extends Composer<Ctx>`; все эти методы цепочные (меняют цепочку middleware):

| Метод | Что совпадает | Заметки |
|---|---|---|
| `use(...middlewares)` | любое обновление | Просто дописать middleware. |
| `on(filters, ...mw)` | `ctx.has(filters)` истинно | `filters` — строка `UpdateType`, функция-страж типа либо массив из них; сужает тип `ctx`. |
| `command(commands, ...mw)` | текст `message_created`, начинающийся с `/` | Триггер получает текст *после* ведущего слэша (`/name value` → `"name value"`); заполняет `ctx.match`. |
| `hears(triggers, ...mw)` | полное совпадение текста `message_created` | Триггер — строка или `RegExp`; заполняет `ctx.match`. |
| `action(triggers, ...mw)` | `message_callback`, у которого совпадает `callback.payload` | Заполняет `ctx.match`. |
| `filter(filters)` | — | Общий комбинатор, на котором построены `on`, `command`, `hears` и `action`. |
| `drop(predicate)` | останавливает цепочку, когда `predicate` истинно | |
| `fork(mw)` | выполняется параллельно остальной цепочке | Исключение в любой ветви пробрасывает его из `fork`. |
| `tap(mw)` | побочный эффект, цепочка всегда продолжается | |
| `lazy(factory)` | определяет, какое middleware запускать, на каждое обновление | |
| `branch(predicate, onTrue, onFalse)` | выполняется ровно одна ветвь | Каждая ветвь сама решает, вызывать ли `next()`. |
| `dispatch(route, handlers, fallback?)` | выбирает обработчик по ключу, который вернул `route(ctx)` | |
| `help(...mw)` / `settings(...mw)` | сокращения для `command('help', ...)` и `command('settings', ...)` | |

`anyOf(...filters)` и `allOf(...filters)` объединяют фильтры `UpdateType` и стражи с семантикой ИЛИ и И; экспортируются из корня пакета и годятся в `.on()` и `.filter()`.

```typescript
import { Bot, anyOf } from '@maxhub/max-bot-api';

const bot = new Bot(process.env.MAX_BOT_TOKEN ?? '');

bot.command('start', (ctx) => ctx.reply('Добро пожаловать!'));
bot.hears('привет', (ctx) => ctx.reply('мир'));
bot.on(anyOf('message_created', 'message_callback'), (ctx, next) => {
  ctx.state.interactive = true;
  return next();
});
bot.action(/^buy:\d+$/, async (ctx) => {
  await ctx.answerOnCallback({ message: { text: 'Добавлено в корзину' } });
});
```

## `Context`

Создаётся на каждое обновление как `new Context(update, api, botInfo?)`; все три хранятся в публичных полях только для чтения.

Ключевые поля: `match` (заполняют `command`, `hears`, `action`), `state` (черновой объект на одно обновление, после него отбрасывается), `updateType`, `myId` (собственный `user_id` бота), `startPayload` (payload диплинка в `bot_started`), `chat`, `chatId`, `message`, `messageId`, `callback`, `user`, а также лениво вычисляемые `contactInfo`, `location` и `sticker`, разобранные из вложения соответствующего типа.

Ключевые методы (каждый — тонкая обёртка над соответствующим вызовом `Api`, подставляющая `ctx.chatId` и `ctx.messageId`, где нужно): `reply(text, extra?)`, `getAllChats(extra?)` (обёртка над `GET /chats`, удалённым платформой в июне 2026, — ожидай ошибку; отслеживай чаты по обновлениям, см. `patterns.md`), `getChat(chatId?)`, `getMessage(id)`, `editMessage(extra)`, `deleteMessage(messageId?)`, `answerOnCallback(extra)`, `pinMessage(id, extra?)`, `getChatMembers(extra?)`, `addChatMembers(userIds)`, `removeChatMember(userId)`, `sendAction(action)`, `leaveChat()`, `getComments(messageId, extra?)`, `deleteComment(messageId, commentId)`. `has(filters)` — рантайм-страж типа, на котором держится `.on()`. `assert(value, method)` бросает исключение, когда метод, привязанный к чату или сообщению, вызывают на обновлении, где их нет.

## Клавиатуры и кнопки

```typescript
import { Bot, Keyboard } from '@maxhub/max-bot-api';

const bot = new Bot(process.env.MAX_BOT_TOKEN ?? '');

bot.command('menu', (ctx) =>
  ctx.reply('Выберите:', {
    attachments: [
      Keyboard.inlineKeyboard([
        [Keyboard.button.callback('Вариант A', 'opt:a'), Keyboard.button.callback('Вариант B', 'opt:b')],
        [Keyboard.button.link('Документация', 'https://dev.max.ru/docs-api')],
      ]),
    ],
  }),
);
```

Настоящие билдеры кнопок в `Keyboard.button`: `callback(text, payload)`, `clipboard(text, payload)`, `link(text, url)`, `requestContact(text)`, `requestGeoLocation(text, extra?)`, `message(text)`, `openApp(text, webApp, contactId?, payload?)` — всего 7 функций.

`Keyboard.button.clipboard` есть в исходниках, но не описан ни на публичном сайте, ни в собственном `docs/04-keyboard.md` пакета — он работает, просто не жди найти его в текстовой документации.

В `docs/04-keyboard.md` также описан помощник `button.chat(text, chatTitle, extra?)` («создаёт чат»). **В исходниках 0.3.1 его нет** (`src/helpers/buttons.ts` экспортирует ровно 7 функций выше, без `chat`) — список типов кнопок на живом публичном сайте независимо подтверждает только 6 именованных типов плюс недокументированный `clipboard`, типа `chat` там тоже нет. Не используй `button.chat`; считай это устаревшей или запланированной, но не выпущенной документацией, пока более новая версия не докажет обратное.

## Вложения и загрузки

```typescript
import { Bot } from '@maxhub/max-bot-api';

const bot = new Bot(process.env.MAX_BOT_TOKEN ?? '');

bot.command('photo', async (ctx) => {
  const image = await ctx.api.uploadImage({ url: 'https://example.com/pic.jpg' });
  await ctx.reply('', { attachments: [image.toJson()] });
});
```

- `ctx.api.uploadImage`, `uploadVideo`, `uploadAudio`, `uploadFile({source})` загружают новый файл и возвращают экземпляр `Attachment` соответствующего типа, оборачивающий полученный токен; один только `ImageAttachment` дополнительно принимает `{url}` для загрузки по URL (по документации — только изображения).
- Чтобы отправить уже загруженный файл по токену: `new ImageAttachment({token})` (и аналоги `Video`, `Audio`, `File`), затем передать `.toJson()` в `attachments`.
- Незагружаемые типы вложений собираются на клиенте: `StickerAttachment({code})`, `LocationAttachment({lon, lat})`, `ShareAttachment({url?, token?})`.
- Внутри загрузки идут через `getUploadUrl({type})`, а затем либо докачиваемой потоковой загрузкой (если `token` вернулся сразу), либо одним multipart-POST. Это детали хоста загрузки и транспорта (см. `references/bot-api.md` и `references/tls-trust.md`) — здесь важно, что **`clientOptions.fetch` ничего из этого не видит**: сами байты файла идут отдельным сырым транспортом `node:http` и `node:https` вообще без хука `fetch` и CA.
- `attachment.not.ready`: `MessagesApi.send` (его используют `ctx.reply`, `api.sendMessageToChat` и т. п.) повторяет именно эту ошибку автоматически, до 3 раз с задержками 1, 2 и 4 с, прерываясь досрочно по твоему `AbortSignal`. Любая другая ошибка пробрасывается сразу, без повтора. У самой загрузки (`Upload.image`, `video`, `audio`, `file`) встроенных повторов нет.

## Сессии и сценарии

Три уровня состояния: `ctx.state` (только это обновление), `ctx.session` (на пару пользователь плюс чат, переживает обновления через хранилище) и твоя собственная база данных приложения.

```typescript
import { Bot, Context, MemorySessionStore, session } from '@maxhub/max-bot-api';

interface CartSession {
  items: string[];
}

type CartContext = Context & { session: CartSession };

const bot = new Bot<CartContext>(process.env.MAX_BOT_TOKEN ?? '');

bot.use(
  session<CartSession, CartContext>({
    store: new MemorySessionStore<CartSession>(60 * 60 * 1000),
    defaultSession: () => ({ items: [] }),
  }),
);

bot.command('cart', (ctx) => ctx.reply(`Позиций: ${ctx.session.items.length}`));
```

Оба параметра типа у `session<S, C>` обязательны: TypeScript не может вывести `C` (твой подтип `Context`) из одного объекта опций, поэтому передавай его явно, в соответствии с `new Bot<C>(...)`, иначе вызов не скомпилируется с ошибкой «Expected 2-3 type arguments».

`session(options?)`: `property` (по умолчанию `'session'`), `getSessionKey` (по умолчанию `<user_id>:<chat_id>`; возврат nullish пропускает создание сессии), `store` (по умолчанию `MemorySessionStore`), `defaultSession`. **`MemorySessionStore` живёт только в процессе — каждая сессия и каждый незавершённый сценарий теряются при перезапуске, падении или повторном деплое.** Не советуй сессии и сценарии без этой оговорки; подставляй своё хранилище `SessionStore` (Redis, SQL и т. п.) — с `get`, `set`, `delete`, синхронными или асинхронными — для всего, что должно пережить деплой.

Сценарии (`defineScenario`, `ScenarioEngine`, `transition`) — тонкий слой маршрутизации поверх `session`, хранящий `{id, step, data, expiresAt?}`. Каждый обработчик шага получает **замороженный клонированный** снимок `state` и `data` — изменение его на месте молча ничего не даёт; возвращай `transition.goto(step, data)` или `transition.stay(data)`, чтобы сохранить изменения. `interceptMiddleware()` направляет обновление активному шагу сценария, если он идёт; истёкшие сценарии удаляются и проваливаются в остальную цепочку. Рекомендуемый порядок подключения: `session()` → `scenarios.controllerMiddleware()` → глобальные команды (`/help`, `/cancel`) → `scenarios.interceptMiddleware()` → команды запуска сценариев, чтобы глобальные команды всё ещё могли «выйти» из активного сценария.

## Сырой доступ к API

`ctx.api.raw` (и `bot.api.raw`) открывает общие HTTP-глаголы плюс геттеры модулей по ресурсам (`chats`, `bots`, `messages`, `subscriptions`, `uploads`, `comments`). **В 0.3.1 `RawApi` публично открывает только `get`, `post` и `patch`** — `put` и `delete` есть внутри базового класса, но не переэкспортированы как публичные методы `RawApi`, хотя и собственный `docs/02-listen-and-respond.md` пакета, и живой публичный сайт показывают `ctx.api.raw.put(...)` и `.delete(...)` как доступные. Не рассчитывай, что эти два скомпилируются; используй типизированные методы-обёртки `Api` (`ctx.deleteMessage()`, `ctx.editMessage()` и т. п.) либо перепроверь по более новому тегу, прежде чем полагаться на `raw.put` и `raw.delete`.

```typescript
import { Bot } from '@maxhub/max-bot-api';

const bot = new Bot(process.env.MAX_BOT_TOKEN ?? '');

bot.command('raw', async (ctx) => {
  // Общая форма: строка метода с плейсхолдерами {param} плюс query, body и path.
  const info = await ctx.api.raw.get('me', {});
  await ctx.reply(JSON.stringify(info));
});
```

## Ошибки, повторы, ограничение частоты

`MaxError extends Error` — `{status, code, message}`; бросается на **любой** не-200 ответ из `client.call`, поэтому его может бросить каждый сырой и высокоуровневый метод API.

**Общих повторов и клиентского ограничения частоты в JSON-клиенте нет нигде** — каждый вызов это один `fetch`. Встроенных поведений повтора всего два: (а) `attachment.not.ready` при отправке сообщения, 3 попытки с задержками 1, 2 и 4 с, и (б) задержка long polling `getUpdates` при `429`, `5xx` и сетевых ошибках, 5 с с удвоением до потолка 60 с. Всё остальное — чаты, комментарии, подписки, загрузки, доставка вебхука — одна попытка без повтора. Платформенный лимит 30 запросов в секунду целиком на твоей ответственности; рецепт ведра токенов в `references/patterns.md`.

## Подводные камни

| Подводный камень | Подробность |
|---|---|
| `bot.start({allowedUpdates:[...]})` без `mode` | Не соответствует `StartConfig`; не компилируется при `strict` TS, хотя встречается в собственном `showcase-bot.ts` SDK. Всегда указывай `mode: 'polling'` или `mode: 'webhook'`. |
| Один `bot.webhookCallback()` | Не подписывает и не очищает старые подписки — можно поднять сервер, который никогда не получит трафик, потому что никто не вызвал `bot.api.subscribe`. Используй `bot.createWebhook()`, если хочешь, чтобы регистрация делалась за тебя, но HTTP-сервер остался твоим. |
| `MemorySessionStore` в продакшене | Только в памяти; каждая сессия и сценарий теряются при перезапуске. Перед выпуском подключи настоящее хранилище. |
| `clientOptions.fetch` и загрузки | Покрывает только JSON-вызовы Bot API; сырой транспорт загрузки файлов не затрагивает — свой fetch, знающий про CA, загрузкам не поможет (хостам загрузки дополнительный CA и не нужен, см. `references/tls-trust.md`). |
| Уверенность, что `ctx.api.raw.put` и `.delete` компилируются | В 0.3.1 они не компилируются, хотя показаны в документации; используй типизированные методы `Api` и `Context`. |
| `button.chat` из `docs/04-keyboard.md` | Не реализован в 0.3.1 и не указан на сайте — не используй. |
| Восприятие 200 от вебхука как «успешно обработано» | SDK отвечает MAX 200 до запуска цепочки middleware; ошибки внутри неё только пишутся в debug, MAX их не повторяет. |
| `ctx.answerOnCallback({ notification: '...' })` | Собственный пример пакета `examples/showcase-bot.ts` использует поле `notification`, но выпущенный тип `AnswerOnCallbackExtra` (0.3.1) объявляет только `message?`. Сам Bot API тост `notification` поддерживает (см. тело `POST /answers` в `references/bot-api.md`), так что это пропуск в типах TS, а не отсутствующая возможность — используй `{ message: { text: '...' } }`, чтобы изменить сообщение, либо передай `notification` с утверждением типа (`{ notification: '...' } as AnswerOnCallbackExtra & { notification?: string }`), если нужен тост и ты готов обойти этот пробел. |
