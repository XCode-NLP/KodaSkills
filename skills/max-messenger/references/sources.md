# Источники

## Приоритет при расхождениях

1. **dev.max.ru** (DOCS, BRIDGE) — поведение, лимиты, требования, даты.
2. **api-schema** — формы запросов и ответов, имена полей, перечисления (там, где сайт молчит).
3. **Исходники клиентов** (Go, TS) — как официальные клиенты на самом деле вызывают API; могут отставать от схемы.
4. README, руководства, демо-боты.

Заметка: страницы dev.max.ru прячут часть примеров кода в неактивных вкладках (например, варианты на TypeScript, Python, Go, Java). При программном чтении страницы видимый HTML может их не содержать.

## Источники

| ID | Ссылка | Для чего | Быстрый путь |
|----|------|-----------|-----------|
| DOCS | https://dev.max.ru/docs-api | Каждый метод, объект, лимит и ошибка Bot API; список изменений API | Методы: `/docs-api/methods/<VERB>/<path>` (параметры пути как `-chatId-`), объекты: `/docs-api/objects/<Name>`, изменения: `/docs-api/changelog-api` |
| BRIDGE | https://dev.max.ru/docs/webapps/bridge | API `window.WebApp` для мини-приложений | Валидация: `/docs/webapps/validation`; настройка: `/docs/webapps/introduction`; диплинки: `/help/deeplinks` |
| SCHEMA | https://github.com/max-messenger/api-schema | OpenAPI `schema.yaml` — точные поля, перечисления, признаки обязательности | `schema.yaml` → `paths:` и `components/schemas`; `README.mdx` про базовый URL и заметки генератора |
| GO | https://github.com/max-messenger/max-bot-api-client-go (ветка `v2`) | Официальный Go-клиент (основной путь на Go) | `bot.go` (NewApi, GetHandler, ValidateInitData), `option.go`, `messages.go`, `upload.go`, `subscriptions.go`, `model/`, `docs/01–04`, `example/simple` |
| MAXBOT | https://github.com/max-messenger/maxbot | Необязательный Go-фреймворк поверх клиента (маршрутизация, контекст, middleware) | `api.go`, `context.go`, `option.go`, `example/simple` |
| DEMO | https://github.com/max-messenger/demo-bot-go | Go-бот продакшен-уровня: сценарии, клавиатуры, загрузки, администрирование чатов, тесты | `internal/app/services/bot/scenario/*.go` (фиксирует старые версии — не копируй их) |
| TS | https://github.com/max-messenger/max-bot-api-client-ts | Официальный TypeScript-клиент и фреймворк `@maxhub/max-bot-api` | `docs/01–10`, `examples/*.ts`, `src/core/context.ts`, `src/core/network/api/` |
| UI | https://github.com/max-messenger/max-ui | Библиотека React-компонентов `@maxhub/max-ui` для мини-приложений | `src/components/index.ts`, `README.md`, `docs/MIGRATION.md`, `CHANGELOG.md`; сайт `https://dev.max.ru/ui` отстаёт от репозитория |
| CERT | https://www.gosuslugi.ru/crt | Russian Trusted Root CA (Минцифры) — нужен для вызовов `platform-api2.max.ru` | PEM: `https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt` — см. `tls-trust.md` |

## Когда перепроверить источник вместо доверия навыку

- Любое утверждение с датой (миграция хоста, удалённые или ограниченные методы, правила TLS для вебхуков).
- Точные сигнатуры методов клиента, прежде чем писать против них много кода.
- Всё, что помечено «Заметка:» как расхождение DOCS и SCHEMA.
- Ошибки, противоречащие навыку (например, эндпоинт отвечает 404 или поле отклоняется).
