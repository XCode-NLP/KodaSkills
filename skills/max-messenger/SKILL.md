---
name: max-messenger
description: "Разработка ботов и мини-приложений для мессенджера MAX (max.ru, МАКС): Bot API на platform-api2.max.ru, официальный Go-клиент (max-bot-api-client-go), Go-фреймворк maxbot, TypeScript-клиент @maxhub/max-bot-api, MAX Bridge (window.WebApp) и React-набор @maxhub/max-ui. Используй для любого кода, который отправляет и принимает сообщения MAX, работает через вебхуки или long polling, загружает медиа, строит inline-клавиатуры и обрабатывает колбэки, форматирует сообщения, администрирует чаты и каналы, работает с комментариями, проверяет initData и телефон в мини-приложении, а также при ошибках TLS из-за корневого сертификата Минцифры. Триггеры: MAX bot, MAX Bot API, platform-api.max.ru, platform-api2.max.ru, max.ru bot, бот для МАКС, бот в MAX, мини-приложение MAX, MAX Bridge, window.WebApp в MAX, max-ui, maxbot, @maxhub. Не для вопросов о продуктовой или рыночной стратегии MAX без кода."
license: Apache-2.0
metadata:
  author: max-messenger
  source: https://github.com/max-messenger/max-agents-skill
  tags: [max, мессенджеры, боты, api]
---

# Разработка под мессенджер MAX

Сверено с официальными источниками **21.09.2026** (см. `references/sources.md`). MAX меняется быстро: если деталь здесь расходится с живой документацией или исходниками клиента, верь источнику.

## Краткая справка

| Что | Значение |
|------|-------|
| Базовый URL | `https://platform-api2.max.ru` (обязателен с 19.07.2026; старый `platform-api.max.ru` устарел) |
| TLS | Хост API подписан **Russian Trusted Root CA (Минцифры)** — добавь его в хранилище доверенных сертификатов, никогда не отключай проверку → `references/tls-trust.md` |
| Авторизация | Заголовок `Authorization: <token>` (без `Bearer`; токен в параметре запроса больше не поддерживается) |
| Где взять токен | business.max.ru → Чат-боты → бот → ⋮ → Настройки |
| Лимит частоты | 30 запросов в секунду к API; ответы на колбэки ≤ 2 в секунду на чат |
| Текст сообщения | ≤ 4000 символов, `format`: `markdown` или `html` |
| Обновления | Вебхук (`POST /subscriptions`, только HTTPS на порту 443) для продакшена; long polling (`GET /updates`) для разработки. Они взаимоисключающие |
| Go | `github.com/max-messenger/max-bot-api-client-go/v2` v2.4.0 (основной); `github.com/max-messenger/maxbot` v1.1.0 (необязательный фреймворк, **требует Go ≥ 1.26**, хотя в его go.mod написано 1.24) |
| TypeScript | `@maxhub/max-bot-api` 0.3.1, Node ≥ 20.19, только ESM |
| Мини-приложения | `<script src="https://st.max.ru/js/max-web-app.js">` → `window.WebApp`; набор компонентов `@maxhub/max-ui` 0.5.0 (React 19.2.8) |

## Жёсткие ограничения — их нарушение приводит к багам

1. **Хост и CA.** Обращайся к `platform-api2.max.ru`. Стандартные образы Docker, CI и Node не доверяют его CA и падают с `x509: certificate signed by unknown authority` или `unable to get local issuer certificate`. Исправляй хранилище доверенных сертификатов (`references/tls-trust.md`); никогда не используй `InsecureSkipVerify`, `NODE_TLS_REJECT_UNAUTHORIZED=0` или `verify=False`.
2. **Медиа не встраивается в текст.** Сообщение — это `text` плюс отдельный массив `attachments[]` без поля позиции или порядка, поэтому медиа нельзя поставить между абзацами. Чтобы чередовать текст и картинки, отправляй несколько сообщений.
3. **4000 символов, кнопки «показать ещё» нет.** Считается каждый символ сырого `text` (разметка, пробелы и эмодзи включительно); считай символы, а не байты. Длинный контент дели на несколько сообщений (`references/patterns.md`).
4. **Отложенной отправки нет.** Поля `send_at` не существует. Планировщик запускай свой.
5. **`GET /chats` удалён (июнь 2026).** Отслеживай чаты сам по обновлениям `bot_added`, `bot_removed` и `bot_started`. Один чат: `GET /chats/{chatId}`.
6. **`POST /chats/{chatId}/members` выведен из эксплуатации** (ограничен 09.09.2026, удалён 30.09.2026). Не строй на нём.
7. **Загрузки асинхронные.** Если отправить слишком рано, вернётся `attachment.not.ready` — повтори с задержкой. Загружай на `url`, который вернул `POST /uploads`; хосты различаются по типу, никогда не хардкодь их.
8. **Правила вебхука.** HTTPS, порт 443, сертификат от доверенного CA или Минцифры (самоподписанные и простой HTTP отклоняются с 25.05.2026), полная цепочка, ответ `200` за 30 секунд. Проверяй `X-Max-Bot-Api-Secret` сравнением за постоянное время. После 8 часов неудачных доставок подписка снимается.
9. **Подмножество разметки.** Списков, таблиц и горизонтальных линеек нет — они приходят простым текстом. Блоки кода отрисовываются моноширинным шрифтом, но переводы строк схлопываются в пробелы. Заголовки, жирный, курсив, подчёркивание, зачёркивание, инлайн-код, ссылки, цитаты, упоминания и выделение работают (`references/formatting.md`).
10. **Авторизация мини-приложения — на сервере.** Проверяй `initData` на своём бэкенде двухшаговым HMAC, начинающимся с ключа `"WebAppData"`; никогда не доверяй `initDataUnsafe`. Формула и проверенный код на Go и TS: `references/webhooks-and-security.md`.

## Выбери стек

| Что строишь | Что читать |
|------------------|------|
| Go-бот (путь по умолчанию) | `references/go-client.md` → сырой клиент `NewApi`, polling и вебхуки, билдеры |
| Go-бот с маршрутизацией и middleware | `references/go-maxbot.md` (необязательный слой поверх клиента) |
| Бот на TypeScript и Node | `references/ts-client.md` |
| Любой другой язык или сырой HTTP | `references/bot-api.md` + `references/objects-and-updates.md` |
| Фронтенд мини-приложения | `references/mini-apps-bridge.md`, интерфейс — `references/max-ui.md` |
| Авторизация на бэкенде мини-приложения | `references/webhooks-and-security.md` |
| Сервер вебхуков | `references/webhooks-and-security.md` + `references/tls-trust.md` |
| Лимиты, повторы, отслеживание чатов, планирование, длинный текст | `references/patterns.md` |

Оба пакета Go называются `maxbot`. Всегда импортируй по полному пути; если используешь оба, задай одному из них псевдоним.

## Минимальные боты

Go — long polling с официальным клиентом:

```go
package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"time"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()

	api, err := maxbot.NewApi(os.Getenv("MAX_BOT_TOKEN"))
	if err != nil {
		log.Fatalf("init: %v", err)
	}

	var marker int64
	for ctx.Err() == nil {
		updates, next, err := api.Subscriptions.GetUpdates(ctx, marker)
		if err != nil {
			log.Printf("get updates: %v", err)
			select { // ждём, но не игнорируем завершение
			case <-ctx.Done():
			case <-time.After(time.Second):
			}
			continue
		}
		marker = next
		for _, u := range updates {
			if u.UpdateType != model.UpdateMessageCreated {
				continue
			}
			msg := maxbot.NewMessage().
				SetChat(u.ChatID).
				SetFormat(model.FormatMarkdown).
				SetText("**Привет!** Документация: [dev.max.ru](https://dev.max.ru/docs-api)")
			if _, err := api.Messages.Send(ctx, msg); err != nil {
				log.Printf("send: %v", err)
			}
		}
	}
}
```

Если это падает с ошибкой x509, передай HTTP-клиент, доверяющий корневому сертификату Минцифры, через `maxbot.WithHTTPClient(...)` — см. `references/tls-trust.md`.

TypeScript:

```ts
import { Bot } from '@maxhub/max-bot-api';

const bot = new Bot(process.env.MAX_BOT_TOKEN!);

bot.command('start', (ctx) =>
  ctx.reply('**Привет!** Документация: [dev.max.ru](https://dev.max.ru/docs-api)', { format: 'markdown' }),
);

bot.start();
```

Node по умолчанию не доверяет корневому сертификату Минцифры: запускай с `NODE_EXTRA_CA_CERTS=/path/russian_trusted_root_ca.pem` (подробности в `references/tls-trust.md`).

## Частые ошибки

| Неправильно | Правильно |
|-------|-------|
| `https://api.max.ru`, `https://platform-api.max.ru` | `https://platform-api2.max.ru` |
| Отключение проверки TLS, чтобы «починить» ошибки x509 | Доверие Russian Trusted Root CA |
| `POST /webhook` | `POST /subscriptions` |
| Проверка вебхука по HMAC тела | Заголовок `X-Max-Bot-Api-Secret` равен твоему секрету (сравнение за постоянное время) |
| HMAC по initData с ключом прямо из токена бота | Сначала получи `secret = HMAC_SHA256("WebAppData", token)` |
| `type=photo` | `type=image` |
| `disable_link_preview` в теле JSON | Это параметр запроса у `POST /messages`, `POST /messages/{messageId}/comments` и `POST /answers` — в `PUT` его нет |
| `GET /chats` или `GET /chats/{link}` | Отслеживай чаты по обновлениям; `GET /chats/{chatId}` для одного чата |
| Захардкоженные хосты загрузки | `url` из `POST /uploads` |
| Списки и таблицы Markdown в сообщениях | Простые строки, заголовки, цитаты |
| `log.Fatal` и необработанные ошибки в обработчиках обновлений | Логируй и продолжай; одно плохое обновление не должно останавливать бота |
| Игнорирование нажатий на колбэки | Отвечай через `POST /answers` (≤ 2 в секунду на чат) |

## Справочники

| Файл | Содержимое |
|------|----------|
| `references/sources.md` | Все официальные источники, приоритет при расхождениях, версии, как проверить актуальность |
| `references/bot-api.md` | Эндпоинты, параметры, загрузки, лимиты, ошибки, датированные изменения платформы |
| `references/objects-and-updates.md` | Сообщение, вложения, кнопки, типы обновлений, чат, пользователь, колбэки, комментарии |
| `references/formatting.md` | Подмножества Markdown и HTML, упоминания, что не поддерживается |
| `references/tls-trust.md` | Корневой CA Минцифры для Go, Node, Docker, curl и Python; диагностика |
| `references/webhooks-and-security.md` | Подписки, правила доставки, секретный заголовок, initData, хеши телефона и контактов |
| `references/go-client.md` | Официальный Go-клиент v2: поверхность API, билдеры, polling, вебхуки, загрузки |
| `references/go-maxbot.md` | Фреймворк maxbot: обработчики, контекст, middleware; когда его брать |
| `references/ts-client.md` | `@maxhub/max-bot-api`: Bot, обработчики, контекст, клавиатуры, сессии, вебхук |
| `references/mini-apps-bridge.md` | API `window.WebApp`, initData, диплинки, настройка |
| `references/max-ui.md` | Компоненты `@maxhub/max-ui` и настройка |
| `references/patterns.md` | Лимиты частоты, повторы, отслеживание чатов, планирование, разбиение, идемпотентность |
