---
name: koda-bots
description: |
  Создание и сопровождение ботов для мессенджеров: Telegram, Discord, Slack, VK, WhatsApp,
  Viber, LINE, WeCom, KakaoTalk, MS Teams, Google Chat, Webex, Matrix, Rocket.Chat, Mattermost,
  Zulip, Signal, XMPP, Delta Chat и MAX. Используй, когда нужно спроектировать бота, выбрать
  платформу или SDK под язык проекта, настроить вебхук или long polling, реализовать команды,
  кнопки, диалоги, платежи, модерацию и уведомления, а также развернуть и сопровождать бота.
  Триггеры: бот в мессенджере, telegram-бот, discord-бот, slack-бот, vk-бот, whatsapp-бот,
  viber-бот, line-бот, teams-бот, google chat бот, matrix-бот, zulip-бот, signal-бот,
  bot api, webhook, long polling, inline-клавиатура, слеш-команда, callback, aiogram,
  python-telegram-bot, grammy, telegraf, discord.js, discord.py, slack bolt, vkbottle, vk-io,
  teloxide, gotgbot, serenity, discordgo, matrix-nio, botbuilder, deltabot.
  Для MAX-специфики используй отдельный навык max-messenger.
license: MIT
metadata:
  author: koda
  version: "1.1.0"
  tags: [koda, боты, мессенджеры, интеграция]
---

# Боты для мессенджеров

## Когда применять

- Нужно создать бота с нуля или добавить новую команду, кнопку, диалог или уведомление.
- Нужно выбрать платформу, библиотеку или способ доставки обновлений.
- Бот не отвечает, отвечает дважды, теряет сообщения, упирается в лимиты или падает на вебхуке.
- Нужно вывести бота в продуктивную среду: секреты, TLS, развёртывание, логи, метрики, резервные копии состояний.

Не применяй навык для MAX-специфики: там действуют отдельные правила и ограничения, см. навык `max-messenger`.

## Порядок работы

1. Определи платформу, аудиторию и сценарий: личный чат, группа, канал, сервер или рабочее пространство.
2. Проверь, что на платформе вообще можно создать бота: где-то нужна заявка или закрытый конструктор.
3. Выбери способ доставки обновлений: вебхук для продуктивной среды, long polling для локальной разработки.
4. Выбери библиотеку под язык проекта, а не под личные предпочтения.
5. Спроектируй состояния и идемпотентность до написания обработчиков.
6. Реализуй минимальный сценарий, затем добавляй кнопки, платежи и администрирование.
7. Проверь бота на повторную доставку, параллельные сообщения, неверный ввод и недоступность API.
8. Задокументируй переменные окружения и порядок запуска.

## Выбор платформы

| Платформа   | Когда выбирать                                                | Ключевое ограничение                                                            | Справочник                  |
|-------------|---------------------------------------------------------------|---------------------------------------------------------------------------------|-----------------------------|
| Telegram    | Быстрый старт, платежи, мини-приложения, глобальная аудитория | 4096 символов в сообщении, 1 сообщение в секунду в чат, файлы до 50 МБ          | `references/telegram.md`    |
| Discord     | Игровые и технические сообщества, серверы, модерация          | Обязательные intents, ответ на interaction за 3 секунды, текст до 2000 символов | `references/discord.md`     |
| Slack       | Корпоративные рабочие пространства, интеграции с процессами   | Подпись запросов HMAC, ответ за 3 секунды, scopes                               | `references/slack.md`       |
| VK          | Русскоязычная аудитория, сообщества и рассылки                | Callback API или LongPoll, лимиты сообщества                                    | `references/vk.md`          |
| WhatsApp    | Клиенты на телефоне, уведомления и поддержка                  | 24-часовое окно обслуживания, вне его только шаблоны                            | `references/whatsapp.md`    |
| Viber       | Аудитория СНГ и Восточной Европы                              | Бот создаётся только на коммерческих условиях с 02.2024                         | `references/regional.md`    |
| LINE        | Япония, Таиланд, Тайвань                                      | Только вебхук, 2000 запросов в секунду                                          | `references/regional.md`    |
| WeCom       | Корпоративная аудитория в Китае                               | Групповой вебхук умеет только отправлять                                        | `references/regional.md`    |
| KakaoTalk   | Южная Корея                                                   | Бот собирается в конструкторе Open Builder, публичного API создания нет         | `references/regional.md`    |
| MS Teams    | Организации на Microsoft 365                                  | Нужен администратор арендатора, JWT вместо HMAC                                 | `references/corporate.md`   |
| Google Chat | Организации на Google Workspace                               | Нужен Google Cloud и согласование приложения                                    | `references/corporate.md`   |
| Webex       | Организации на Cisco Webex                                    | Около 300 запросов в минуту на пользователя                                     | `references/corporate.md`   |
| Matrix      | Федерация, свой сервер, E2EE                                  | Нет вебхуков: приём через `sync`                                                | `references/open-source.md` |
| Rocket.Chat | Свой сервер, открытый код                                     | REST и Realtime — два разных интерфейса                                         | `references/open-source.md` |
| Mattermost  | Свой сервер, ChatOps                                          | Официального SDK нет, есть OpenAPI                                              | `references/open-source.md` |
| Zulip       | Обсуждения по темам                                           | Тема обязательна, приём через очередь событий                                   | `references/open-source.md` |
| Signal      | Приватные уведомления                                         | Официального API для ботов нет, риск блокировки номера                          | `references/self-hosted.md` |
| XMPP        | Своя инфраструктура, открытый протокол                        | Поддержка расширений зависит от сервера                                         | `references/self-hosted.md` |
| Delta Chat  | Мессенджер на электронной почте                               | Задержки доставки, нет массовых рассылок                                        | `references/self-hosted.md` |
| MAX         | Российский мессенджер, госуслуги и бизнес                     | TLS Минцифры, асинхронные загрузки, 30 запросов в секунду                       | Навык `max-messenger`       |

## Выбор SDK

Подробные таблицы по языкам — в `references/sdks.md`, включая Go, Rust, PHP, Java, Kotlin, C#, Ruby и Elixir.

Короткие правила:

1. **Библиотека должна знать актуальную версию API.** Иначе нужное поле просто недоступно.
2. **Проверь дату последнего релиза.** Полгода без активности для молодой платформы — тревожный признак.
3. **Не бери неподдерживаемую обёртку.** Тонкий HTTP-клиент на 200–300 строк надёжнее: он не скрывает ошибки API и не ломается при смене зависимостей.
4. **Смотри на модель асинхронности.** Синхронная библиотека в асинхронном сервисе блокирует цикл событий.
5. **Проверяй лицензию.** MIT и Apache-2.0 безопасны; AGPL требует раскрытия исходников при сетевом использовании.

Для части платформ официального SDK нет вообще: WhatsApp, Viber, WeCom, Google Chat и Teams на Go или Rust работаются напрямую по HTTP.

## Общие правила

1. **Секреты — только в переменных окружения.** Токен бота не попадает в репозиторий, логи, скриншоты и сообщения об ошибках.
2. **Вебхук проверяет подлинность запроса.** Секретный заголовок, подпись или IP-фильтр — в зависимости от платформы. Без проверки любой может отправить боту поддельное обновление.
3. **Обновления обрабатываются идемпотентно.** Платформа может доставить одно и то же обновление повторно. Храни `update_id` или собственный ключ идемпотентности.
4. **Вебхук отвечает быстро.** Сначала подтверди приём, потом выполняй работу в фоне. Долгий обработчик приводит к повторной доставке.
5. **Лимиты частоты соблюдаются на стороне бота.** Очередь, повтор с задержкой и ограничение параллелизма лучше, чем лавина ошибок `429`.
6. **Состояния диалога не живут в памяти процесса.** Перезапуск, второй экземпляр и балансировщик ломают FSM в памяти. Используй Redis или БД.
7. **Ввод пользователя — недоверенные данные.** Не подставляй его в SQL, shell, шаблоны и системные инструкции без экранирования и проверки.
8. **Ошибки логируются без секретов и персональных данных.** Полный текст сообщений и токены не нужны в логах.
9. **Бот переживает перезапуск.** Незавершённые задачи, состояния и очереди должны восстанавливаться.
10. **Есть проверка работоспособности и метрики.** Минимум: живость процесса, очередь, число ошибок, задержка ответа.

## Минимальные примеры

Telegram, aiogram 3:

```python
import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

dp = Dispatcher()


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer("Привет! Я на связи.")


@dp.message(F.text)
async def echo(message: Message) -> None:
    await message.answer(message.text[:4096])


async def main() -> None:
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

Telegram, Go с `telegram-bot-api/v5`:

```go
package main

import (
	"log"
	"os"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func main() {
	bot, err := tgbotapi.NewBotAPI(os.Getenv("TELEGRAM_BOT_TOKEN"))
	if err != nil {
		log.Fatalf("init: %v", err)
	}

	updateConfig := tgbotapi.NewUpdate(0)
	updateConfig.Timeout = 30

	for update := range bot.GetUpdatesChan(updateConfig) {
		if update.Message == nil {
			continue
		}

		reply := tgbotapi.NewMessage(update.Message.Chat.ID, update.Message.Text)
		if _, err := bot.Send(reply); err != nil {
			log.Printf("send: %v", err)
		}
	}
}
```

Telegram, Rust с `teloxide`:

```rust
use teloxide::prelude::*;

#[tokio::main]
async fn main() {
    // Bot::from_env() читает переменную TELOXIDE_TOKEN, поэтому задаём токен явно
    let token = std::env::var("TELEGRAM_BOT_TOKEN").expect("TELEGRAM_BOT_TOKEN не задан");
    let bot = Bot::new(token);

    let handler = Update::filter_message().endpoint(|bot: Bot, msg: Message| async move {
        let text = msg.text().unwrap_or_default().to_owned();
        bot.send_message(msg.chat.id, text).await?;
        respond(())
    });

    Dispatcher::builder(bot, handler)
        .enable_ctrlc_handler()
        .build()
        .dispatch()
        .await;
}
```

Discord, discord.js 14:

```js
import { Client, Events, GatewayIntentBits } from 'discord.js';

const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.once(Events.ClientReady, (readyClient) => {
  console.log(`Готов: ${readyClient.user.tag}`);
});

client.on(Events.InteractionCreate, async (interaction) => {
  if (!interaction.isChatInputCommand()) return;
  if (interaction.commandName === 'ping') {
    await interaction.reply({ content: 'pong', ephemeral: true });
  }
});

client.login(process.env.DISCORD_BOT_TOKEN);
```

Slack, Bolt for JavaScript:

```js
import bolt from '@slack/bolt';

const app = new bolt.App({
  token: process.env.SLACK_BOT_TOKEN,
  signingSecret: process.env.SLACK_SIGNING_SECRET,
  socketMode: true,
  appToken: process.env.SLACK_APP_TOKEN,
});

app.command('/ping', async ({ ack, respond }) => {
  await ack();
  await respond('pong');
});

await app.start();
```

VK, vkbottle:

```python
import os

from vkbottle.bot import Bot, Message

bot = Bot(os.environ["VK_BOT_TOKEN"])


@bot.on.message(text=["начать", "start"])
async def start(message: Message) -> str:
    return "Привет! Я на связи."


bot.run_forever()
```

## Типичные ошибки

| Неправильно                               | Правильно                                                          |
|-------------------------------------------|--------------------------------------------------------------------|
| Токен в коде или в `.env` в репозитории   | Переменные окружения и секреты CI/CD                               |
| Вебхук без проверки подписи или секрета   | Проверка подлинности каждого запроса                               |
| Долгая работа прямо в обработчике вебхука | Подтверждение приёма и фоновая очередь                             |
| Повторная обработка одного `update_id`    | Идемпотентность и дедупликация                                     |
| FSM в памяти процесса                     | Redis или БД с TTL                                                 |
| Отправка без учёта `429`                  | Очередь, повтор с задержкой и ограничение параллелизма             |
| `message.text` без проверки на `None`     | Проверка типа и наличия текста                                     |
| Ответ на callback без `answer`            | Подтверждение callback, чтобы у пользователя не крутился индикатор |
| Логирование токена и полного текста       | Маскирование секретов и персональных данных                        |
| Один экземпляр без корректного завершения | Корректная остановка и восстановление задач                        |
| Свободный текст вне окна в WhatsApp       | Утверждённый шаблон                                                |
| Перенос проверки HMAC со Slack на Teams   | Teams и Google Chat проверяют JWT                                  |

## Справочники

| Файл                         | Содержимое                                                                                                      |
|------------------------------|-----------------------------------------------------------------------------------------------------------------|
| `references/sdks.md`         | SDK по языкам: Python, JS/TS, Go, Rust, PHP, Java, Kotlin, C#, Ruby, Elixir; ссылки на официальную документацию |
| `references/telegram.md`     | Bot API, aiogram и python-telegram-bot, вебхуки, клавиатуры, платежи, мини-приложения                           |
| `references/discord.md`      | Gateway и HTTP interactions, intents, слеш-команды, компоненты, модерация                                       |
| `references/slack.md`        | Events API, Socket Mode, Bolt, Block Kit, scopes, подпись запросов                                              |
| `references/vk.md`           | Callback API и LongPoll, vkbottle и vk-io, клавиатуры, рассылки                                                 |
| `references/whatsapp.md`     | Cloud API, 24-часовое окно, шаблоны, вебхуки, подпись, лимиты                                                   |
| `references/regional.md`     | Viber, LINE, WeCom, личный WeChat, KakaoTalk                                                                    |
| `references/corporate.md`    | MS Teams, Google Chat, Webex                                                                                    |
| `references/open-source.md`  | Matrix, Rocket.Chat, Mattermost, Zulip                                                                          |
| `references/self-hosted.md`  | Signal, XMPP, Delta Chat                                                                                        |
| `references/architecture.md` | Вебхук или polling, идемпотентность, очереди, состояния, безопасность, развёртывание и тесты                    |
