# SDK для ботов по языкам

Здесь собраны библиотеки по платформам и языкам. Наличие библиотек сверено с реестрами пакетов (PyPI, npm, crates.io, proxy.golang.org, Packagist, Hex, RubyGems, Maven Central, NuGet) в ноябре 2026 года. Версии намеренно не указаны: они меняются быстрее, чем этот файл. Перед выбором открой репозиторий и посмотри дату последнего релиза, число открытых вопросов и поддержку актуальной версии API платформы.

## Как читать таблицы

- **Официальная** — библиотека от владельца платформы, обновляется вместе с API.
- **Сообщество** — сторонняя библиотека, качество и поддержка зависят от автора.
- **Обёртка** — тонкий клиент поверх HTTP API, без собственной логики.

Если библиотеки нет или она заброшена, платформа всё равно доступна по HTTP. Тонкий клиент на 200–300 строк обычно надёжнее неподдерживаемой обёртки: он не ломается при смене версии зависимости и не скрывает ошибки API.

## Официальная документация платформ

| Платформа      | Документация                                                                   |
|----------------|--------------------------------------------------------------------------------|
| Telegram       | <https://core.telegram.org/bots/api>                                           |
| Discord        | <https://discord.com/developers/docs>                                          |
| Slack          | <https://api.slack.com>                                                        |
| VK             | <https://dev.vk.com>                                                           |
| MAX            | <https://dev.max.ru/docs-api>                                                  |
| WhatsApp       | <https://developers.facebook.com/docs/whatsapp/cloud-api>                      |
| Viber          | <https://developers.viber.com/docs/api/rest-bot-api/>                          |
| LINE           | <https://developers.line.biz/en/reference/messaging-api/>                      |
| WeChat (WeCom) | <https://developer.work.weixin.qq.com/document/path/91770>                     |
| KakaoTalk      | <https://developers.kakao.com/docs/en/kakaotalk-message/rest-api>              |
| MS Teams       | <https://learn.microsoft.com/en-us/microsoftteams/platform/bots/what-are-bots> |
| Google Chat    | <https://developers.google.com/workspace/chat/api/reference/rest>              |
| Webex          | <https://developer.webex.com/docs/api/basics>                                  |
| Matrix         | <https://spec.matrix.org/latest/client-server-api/>                            |
| Rocket.Chat    | <https://developer.rocket.chat/apidocs/rocketchat-api>                         |
| Mattermost     | <https://developers.mattermost.com/api-documentation/>                         |
| Zulip          | <https://zulip.com/api/>                                                       |
| Signal         | <https://github.com/AsamK/signal-cli>                                          |
| XMPP           | <https://xmpp.org/standards/>                                                  |
| Delta Chat     | <https://delta.chat/en/help>                                                   |

## Сводная таблица

| Платформа      | Python                            | JavaScript / TypeScript    | Go                                  | Rust                       |
|----------------|-----------------------------------|----------------------------|-------------------------------------|----------------------------|
| Telegram       | `aiogram`, `python-telegram-bot`  | `grammy`, `telegraf`       | `gotgbot/v2`, `telegram-bot-api/v5` | `teloxide`, `frankenstein` |
| Discord        | `discord.py`, `hikari`            | `discord.js`, `oceanic.js` | `discordgo`                         | `serenity`, `twilight`     |
| Slack          | `slack-bolt`                      | `@slack/bolt`              | `slack-go/slack`                    | `slack-morphism`           |
| VK             | `vkbottle`, `vk-api`              | `vk-io`                    | `vksdk/v2`                          | —                          |
| WhatsApp       | `pywa`, `heyoo`                   | HTTP (`fetch`)             | HTTP                                | HTTP                       |
| Viber          | HTTP                              | HTTP                       | HTTP                                | HTTP                       |
| LINE           | `line-bot-sdk`                    | `@line/bot-sdk`            | `line-bot-sdk-go`                   | HTTP                       |
| WeChat (WeCom) | `wechatpy`                        | `wechaty` (неофициальная)  | HTTP                                | HTTP                       |
| MS Teams       | `botbuilder-core`                 | `botbuilder`               | HTTP                                | HTTP                       |
| Google Chat    | `google-api-python-client`        | `googleapis`               | HTTP                                | HTTP                       |
| Webex          | `webexteamssdk`                   | `webex` (браузерная)       | HTTP                                | HTTP                       |
| Matrix         | `matrix-nio`                      | `matrix-bot-sdk`           | `maunium.net/go/mautrix`            | `matrix-rust-sdk` (git)    |
| Rocket.Chat    | `rocketchat_API`                  | `@rocket.chat/sdk`         | HTTP                                | HTTP                       |
| Mattermost     | `mattermostdriver`                | `@mattermost/client`       | `mattermost/server/public`          | HTTP                       |
| Zulip          | `zulip`                           | `zulip-js`                 | HTTP                                | HTTP                       |
| Signal         | `signalbot`, `pysignalclirestapi` | `signal-rest-ts`           | HTTP                                | HTTP                       |
| XMPP           | `slixmpp`                         | `xmpp.js`                  | `gosrc.io/xmpp`                     | HTTP                       |
| Delta Chat     | `deltabot`                        | HTTP                       | HTTP                                | `deltachat-core-rust`      |

## Python

Асинхронные библиотеки предпочтительны: бот почти всегда ждёт сеть.

| Платформа   | Библиотека                                | Комментарий                                                             |
|-------------|-------------------------------------------|-------------------------------------------------------------------------|
| Telegram    | `aiogram` 3.x                             | Роутеры, фильтры, FSM, мини-приложения. Основной выбор для новых ботов  |
| Telegram    | `python-telegram-bot` 21+                 | `Application`, `ConversationHandler`, `JobQueue`                        |
| Telegram    | `pyTelegramBotAPI`                        | Синхронная, простая, для скриптов и прототипов                          |
| Discord     | `discord.py` 2.x                          | Слэш-команды через `app_commands`, расширения                           |
| Discord     | `hikari`                                  | Асинхронная, без «магии», для больших ботов                             |
| Discord     | `pycord`, `nextcord`, `disnake`           | Форки `discord.py` с расширениями                                       |
| Slack       | `slack-bolt`                              | Официальная, вместе с `slack_sdk`                                       |
| VK          | `vkbottle`                                | Правила, состояния, клавиатуры                                          |
| VK          | `vk-api`                                  | Автогенерируемый клиент по схеме API                                    |
| WhatsApp    | `pywa`                                    | Обёртка Cloud API: сообщения, шаблоны, вебхуки                          |
| WhatsApp    | `heyoo`                                   | Простая обёртка Cloud API                                               |
| LINE        | `line-bot-sdk`                            | Официальная                                                             |
| WeChat      | `wechatpy`                                | Официальные аккаунты; для WeCom — HTTP напрямую                         |
| MS Teams    | `botbuilder-core`                         | Bot Framework SDK; Microsoft переводит стек на Microsoft 365 Agents SDK |
| Google Chat | `google-api-python-client`, `google-auth` | Официального SDK именно для Chat нет, работа через REST                 |
| Webex       | `webexteamssdk`                           | Сообщество, но стабильна                                                |
| Matrix      | `matrix-nio`                              | `AsyncClient`, `sync_forever`, E2EE                                     |
| Rocket.Chat | `rocketchat_API`                          | REST-обёртка; Realtime API придётся делать самому                       |
| Mattermost  | `mattermostdriver`                        | REST и WebSocket                                                        |
| Zulip       | `zulip`                                   | Официальные привязки, event queue из коробки                            |
| Signal      | `signalbot`                               | Фреймворк поверх `signal-cli-rest-api`                                  |
| Signal      | `pysignalclirestapi`                      | Тонкий клиент к `signal-cli-rest-api`                                   |
| XMPP        | `slixmpp`                                 | Асинхронный, MUC, OMEMO через плагины                                   |
| Delta Chat  | `deltabot`                                | Официальный фреймворк ботов Delta Chat                                  |
| Delta Chat  | `deltachat`                               | Привязки к `deltachat-core-rust`                                        |

## JavaScript и TypeScript

Node.js — самый распространённый выбор для ботов после Python. Проверяй поддержку ESM и актуальной версии Node.

| Платформа   | Библиотека                | Комментарий                                                                                               |
|-------------|---------------------------|-----------------------------------------------------------------------------------------------------------|
| Telegram    | `grammy`                  | Типизированная, middleware, хорошая документация                                                          |
| Telegram    | `telegraf`                | Зрелая, много плагинов, сцены                                                                             |
| Telegram    | `node-telegram-bot-api`   | Минимальный клиент                                                                                        |
| Discord     | `discord.js` 14           | Самый популярный, богатый API                                                                             |
| Discord     | `oceanic.js`              | Легче и быстрее `discord.js`                                                                              |
| Discord     | `eris`                    | Альтернатива с другим подходом к кэшу                                                                     |
| Slack       | `@slack/bolt`             | Официальная, Socket Mode и HTTP                                                                           |
| Slack       | `@slack/web-api`          | Только вызовы методов, без приёма событий                                                                 |
| VK          | `vk-io`                   | Сцены, управление сценариями, LongPoll                                                                    |
| WhatsApp    | `@whiskeysockets/baileys` | **Неофициальная**, протокол WhatsApp Web. Нарушает условия использования Meta, возможна блокировка номера |
| WhatsApp    | `whatsapp-web.js`         | **Неофициальная**, управляет браузером. Только для личных экспериментов                                   |
| LINE        | `@line/bot-sdk`           | Официальная, Flex Message                                                                                 |
| WeChat      | `wechaty`                 | **Неофициальная**, Puppet-архитектура; для личного WeChat официального API нет                            |
| MS Teams    | `botbuilder`              | Bot Framework, Adaptive Cards                                                                             |
| Google Chat | `googleapis`              | REST-клиент, официального SDK нет                                                                         |
| Webex       | `webex`                   | Браузерный SDK; на сервере удобнее REST                                                                   |
| Matrix      | `matrix-bot-sdk`          | Бот-фреймворк, E2EE                                                                                       |
| Matrix      | `matrix-js-sdk`           | Клиентский SDK, больше для приложений                                                                     |
| Rocket.Chat | `@rocket.chat/sdk`        | Realtime API и REST                                                                                       |
| Mattermost  | `@mattermost/client`      | Официальный клиент, часть `mattermost-redux`                                                              |
| Zulip       | `zulip-js`                | Официальная                                                                                               |
| Signal      | `signal-rest-ts`          | TypeScript-клиент к `signal-cli-rest-api`                                                                 |
| XMPP        | `xmpp.js`                 | Клиентская библиотека                                                                                     |
| Twitch      | `tmi.js`                  | Чат Twitch по IRC                                                                                         |

## Go

Go хорош для ботов с высокой нагрузкой и небольшим потреблением памяти.

| Платформа  | Библиотека                                           | Комментарий                                                                                       |
|------------|------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| Telegram   | `github.com/PaulSonOfLars/gotgbot/v2`                | Типизированная, активно развивается. Учти: последние теги ветки v2 — предрелизные (`v2.0.0-rc.*`) |
| Telegram   | `github.com/go-telegram-bot-api/telegram-bot-api/v5` | Зрелая, простая, много примеров                                                                   |
| Discord    | `github.com/bwmarrin/discordgo`                      | Основной выбор, поддерживает слэш-команды                                                         |
| Discord    | `github.com/andersfylling/disgord`                   | Альтернатива с другим API                                                                         |
| Slack      | `github.com/slack-go/slack`                          | Официальная                                                                                       |
| VK         | `github.com/SevereCloud/vksdk/v2`                    | Полная обёртка, включая Callback API и LongPoll                                                   |
| MAX        | `github.com/max-messenger/max-bot-api-client-go/v2`  | Официальный клиент, см. навык `max-messenger`                                                     |
| Matrix     | `maunium.net/go/mautrix`                             | Библиотека для мостов, тяжеловесная, но полная                                                    |
| Mattermost | `github.com/mattermost/mattermost/server/public`     | Модели и клиент из основного репозитория                                                          |
| XMPP       | `gosrc.io/xmpp`                                      | Базовый клиент, MUC есть                                                                          |

## Rust

Экосистема меньше, но для Telegram, Discord, Slack и Matrix выбор достаточный. Асинхронность строится на `tokio`.

| Платформа | Библиотека        | Комментарий                                                                               |
|-----------|-------------------|-------------------------------------------------------------------------------------------|
| Telegram  | `teloxide`        | Декларативные обработчики, диалекты, FSM                                                  |
| Telegram  | `frankenstein`    | Тонкая типизированная обёртка над Bot API                                                 |
| Discord   | `serenity`        | Основной выбор, слэш-команды, шардирование                                                |
| Discord   | `twilight`        | Модульное семейство крейтов, низкоуровневое и быстрое                                     |
| Slack     | `slack-morphism`  | Асинхронная, Socket Mode и HTTP                                                           |
| Matrix    | `matrix-rust-sdk` | Официальный SDK, E2EE. **Не публикуется на crates.io** — подключается как git-зависимость |
| Twitch    | `twitch-irc`      | Чат Twitch                                                                                |

Для WhatsApp, Teams, Google Chat, Webex, Viber, LINE и WeCom готовых зрелых библиотек на Rust нет. Работай через `reqwest` и `serde`.

## PHP

| Платформа | Библиотека                   | Комментарий                                       |
|-----------|------------------------------|---------------------------------------------------|
| Telegram  | `longman/telegram-bot`       | Самый полный набор возможностей Bot API           |
| Telegram  | `irazasyed/telegram-bot-sdk` | Интеграция с Laravel                              |
| Discord   | `team-reflex/discord-php`    | Асинхронная, на ReactPHP                          |
| VK        | `vkcom/vk-php-sdk`           | Официальная, простая                              |
| LINE      | `linecorp/line-bot-sdk`      | Официальная                                       |
| WhatsApp  | `twilio/sdk`                 | Если работаешь через Twilio, а не напрямую с Meta |

Официального SDK Slack для PHP нет: официальные SDK Slack выпущены для JavaScript, Python и Java. На PHP работай с Web API через HTTP-клиент и проверяй подпись запросов сам.

PHP-бот обычно живёт за веб-сервером: вебхук — обычный маршрут, а не долгоживущий процесс. Это упрощает развёртывание, но лишает long polling и фоновых задач без очереди.

## Java и Kotlin

| Платформа | Библиотека            | Координаты                                 | Комментарий                                                      |
|-----------|-----------------------|--------------------------------------------|------------------------------------------------------------------|
| Telegram  | TelegramBots          | `org.telegram:telegrambots`                | Полная обёртка, Spring Boot starter                              |
| Telegram  | java-telegram-bot-api | `com.github.pengrad:java-telegram-bot-api` | Минималистичная, без зависимостей                                |
| Discord   | JDA                   | `net.dv8tion:JDA`                          | Основной выбор для Java                                          |
| Discord   | Discord4J             | `com.discord4j:discord4j-core`             | Реактивная, на Reactor                                           |
| Discord   | Kord                  | `dev.kord:kord-core`                       | Kotlin, корутины                                                 |
| Slack     | Bolt for Java         | `com.slack.api:bolt`                       | Официальный Java SDK                                             |
| MS Teams  | Bot Framework         | `com.microsoft.bot:bot-builder`            | Официальный Java SDK                                             |
| Matrix    | Trixnity              | вне Maven Central                          | Kotlin, корутины, E2EE; подключается из собственного репозитория |

## C# и .NET

| Платформа | Библиотека              | Комментарий                                                       |
|-----------|-------------------------|-------------------------------------------------------------------|
| Telegram  | `Telegram.Bot`          | Основная библиотека, активно поддерживается                       |
| Discord   | `DSharpPlus`            | Богатый API, слэш-команды                                         |
| Discord   | `Discord.Net`           | Зрелая, модульная                                                 |
| Slack     | `SlackNet`              | Сообщество                                                        |
| MS Teams  | `Microsoft.Bot.Builder` | Официальная; Microsoft переводит стек на Microsoft 365 Agents SDK |

## Ruby

| Платформа | Библиотека          | Комментарий                          |
|-----------|---------------------|--------------------------------------|
| Telegram  | `telegram-bot-ruby` | Простая и стабильная                 |
| Discord   | `discordrb`         | Основной выбор, есть поддержка voice |
| LINE      | `line-bot-api`      | Официальная                          |

## Elixir

| Платформа | Библиотека | Комментарий                                     |
|-----------|------------|-------------------------------------------------|
| Telegram  | `ex_gram`  | Декларативные обработчики, хорошая документация |
| Discord   | `nostrum`  | Кэш, шардирование, команды                      |
| Discord   | `cog`      | Легче `nostrum`                                 |

Erlang/OTP даёт супервизоры и распределённость бесплатно, что удобно для ботов с долгими соединениями.

## Другие языки

- **Swift** — `TelegramBotSDK` для Telegram, `SwiftDiscord` для Discord. Оба отстают от актуальных версий API.
- **Dart и Flutter** — `telegram_bot` для Telegram, остальное через HTTP.
- **Lua** — `lua-telegram-bot`, используется в игровых серверах.
- **Perl** — `Bot::BasicBot` для IRC и XMPP, для современных платформ только HTTP.
- **Shell** — для однократных уведомлений достаточно `curl` к `sendMessage` или вебхуку. Для бота не подходит: нет состояний и очередей.

## Как выбрать библиотеку

1. **Совпадение с версией API платформы.** Если библиотека не знает о поле, которое уже есть в API, ты не сможешь его использовать, не патча её.
2. **Дата последнего релиза и коммита.** Полгода без активности для молодой платформы — тревожный признак, для стабильной — норма.
3. **Поддержка нужного способа доставки.** Не всякая библиотека умеет и вебхук, и long polling.
4. **Наличие типов или схемы.** Типизированные обёртки ловят опечатки в названиях полей на этапе компиляции.
5. **Качество документации и примеров.** Если документация сводится к автосгенерированному справочнику, закладывай время на чтение исходников.
6. **Совпадение модели асинхронности с проектом.** Синхронная библиотека в асинхронном сервисе блокирует цикл событий.
7. **Лицензия.** MIT и Apache-2.0 безопасны; AGPL требует раскрытия исходников при сетевом использовании.

## Признаки заброшенной библиотеки

- Последний релиз старше года, при этом API платформы менялся.
- В вопросах висят обращения без ответа дольше нескольких месяцев.
- Pull request'ы с исправлениями не вливаются.
- В коде зашиты устаревшие версии API или домены.
- Нет поддержки актуальной версии языка (Python 3.12, Node 20, Go 1.22).

В этом случае бери HTTP-клиент и пиши обёртку сам. Для большинства платформ хватает трёх-четырёх методов: отправить сообщение, получить обновления, ответить на callback, загрузить файл.
