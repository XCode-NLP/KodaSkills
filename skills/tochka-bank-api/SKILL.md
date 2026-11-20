---
name: tochka-bank-api
description: "REST API Точка Банка (developers.tochka.com) для расчётных счетов ИП и ООО — выписки, платежи, счета на оплату, закрывающие документы (акты, УПД), СБП, эквайринг, вебхуки. Не для Тинькофф, Сбера и ВТБ, не для личных счетов, не для бухгалтерии 1С и не для налоговых вопросов."
license: MIT
metadata:
  author: rodion-m
  source: https://github.com/rodion-m/tochka-bank-skill
---

# API Точка Банка

Практическое руководство по REST API Точки (developers.tochka.com). Авторизация, платежи и выписки, платёжные поручения, счета на оплату, закрывающие документы, эквайринг СБП, вебхуки.

## Быстрый старт

| Цель | Авторизация | Настройка |
|------|------|------|
| Песочница и эксперименты | общий токен | `export TOCHKA_TOKEN=working_token TOCHKA_SANDBOX=1` |
| Свой счёт и черновики платежей | личный JWT | `! python3 scripts/tochka_client.py init` |
| Счета, закрывающие документы, полная выписка | OAuth + согласие | `! python3 scripts/tochka_client.py init --oauth` |

Префикс `!` **обязателен** — мастера читают секреты через `getpass`, а ему нужен настоящий TTY, которого инструмент Bash у агента не даёт. После `init` токен, `customerCode` и `accountId` по умолчанию попадают в хранилище учётных данных ОС и в `~/.config/tochka-bank-api/config.json` — дальше большинство подкоманд работают без флагов.

JWT покрывает: список счетов, баланс, входящие платежи СБП и по картам, черновики платежей в очереди «На подпись», QR СБП, платёжные ссылки. OAuth нужен для полной выписки Open Banking, API счетов на оплату и закрывающих документов — на них JWT возвращает **501**.

Полный протокол JWT и OAuth, 19 разрешений и подводные камни OAuth-приложений (включая `localhost` против `127.0.0.1`): [references/auth.md](references/auth.md).

| Окружение | URL |
|---|---|
| Продакшен | `https://enter.tochka.com/uapi` |
| Песочница | `https://enter.tochka.com/sandbox/v2` |

## Задача → подкоманда

| Цель | Подкоманда | Авторизация | Безопасность |
|------|------------|:---:|:---:|
| Список счетов | `list-accounts` | JWT | чтение |
| Текущий баланс | `get-balance` | JWT | чтение |
| Входящие платежи СБП и по картам | `list-incoming` | JWT | чтение |
| Черновики платежей «На подпись» | `list-for-sign` | JWT | чтение |
| Создать платёжное поручение | `curl POST /payment/v2.0/for-sign` (без хелпера) | JWT | 🛑 |
| Полная выписка | `list-statement --from … --to …` | OAuth | чтение |
| Создать счёт на оплату | `create-invoice --format id` | OAuth | 🛑 |
| Отправить или удалить счёт | `send-invoice` / `curl DELETE /invoice/v2.0/bills/{cc}/{id}` | OAuth | 🛑 |
| Закрывающий документ (акт, УПД, ТОРГ-12, счёт-фактура) | `create-closing-doc --kind …` | OAuth | 🛑 |
| Отправить, скачать или удалить закрывающий документ | `get-/send-/delete-closing-doc` | OAuth | чтение / 🛑 |
| Платёжная ссылка эквайринга | `create-payment-link --format url` | JWT* | 🛑 |
| Приём платежей по QR СБП | `curl POST /sbp/v2.0/…` (без хелпера) | JWT* | 🛑 |
| Вебхук: зарегистрировать, перечислить, проверить, удалить | `register-/list-/test-/delete-webhook` | JWT или OAuth | чтение / 🛑 |
| Суточный реестр эквайринга (сверка) | `list-registry --date …` | JWT | чтение |
| Диагностика OAuth 403 | `list-consents` / `get-consent --consent-id …` | OAuth | чтение |
| Показать сохранённые умолчания | `config` | — | чтение |

<sub>JWT* — JWT с нужным разрешением (`MakeAcquiringOperation` или `EditSBPData`). 🛑 — меняет состояние, блокируется хуком (см. ниже).</sub>

`create-invoice`, `create-closing-doc` и `create-payment-link` поддерживают `--format {json,id,url}`: `--format id|url` пишет в stdout одно значение (конверт уходит в stderr), поэтому в shell-конвейерах не нужен `jq`.

Полные схемы, формы запросов, валидация и различия ИП и ООО: [references/endpoints.md](references/endpoints.md). Подпись и повторы вебхуков: [references/webhooks.md](references/webhooks.md). **Перед выпуском продакшен-кода** сверяйся с живым ReDoc — Точка меняет пути и имена полей без semver: https://enter.tochka.com/doc/v2/redoc.

## Критичные подводные камни

Они бьют почти каждый раз:

- **В `accountId` есть слэш** `{20-значный-счёт}/{9-значный-БИК}`: в URL кодируй как `%2F`, в телах передавай как есть. Иначе получишь `404 Not found statement under account`.
- **`paymentPurpose` не может содержать длинное тире `—` (U+2014)** — банк отклоняет. Используй дефис `-` или запятую.
- **`paymentDate` должна быть не позже сегодняшней даты** — будущие отклоняются.
- **Даты выписки — это чистые даты**, а не дата-время: `"2026-04-01"`, а не `"2026-04-01T00:00:00+03:00"`.
- **`amount` в QR СБП — в копейках**, а в `create-payment-link` — в рублях (float). 1500 ₽ = `150000` для QR СБП и `1500.00` для платёжной ссылки.
- **В теле счёта важен точный регистр**: `SecondSide` (заглавная S), `Content.Invoice.Positions`, `taxCode` (не `INN`), `quantity` (не `count`), `totalAmount` (не `amount`), `unitCode` с точкой на конце (`"шт."`, а не код ОКЕИ), `ndsKind` ∈ `without_nds`/`nds_0`/`nds_5`/`nds_7`/`nds_10`/`nds_22` (**`nds_22` заменил `vat_20` с 2026 года**). В ответе — `Data.documentId` (не `documentUid`, он удалён).
- **`unitCode` — закрытый белый список**: `шт. тыс.шт. компл. пар. усл.ед. упак. услуга. пач. мин. ч. сут. г. кг. л. м. м2. м3. км. га. кВт. кВт.ч.` (точка на конце входит в значение). **Нет `мес.` и `год.`** — для подписок используй `услуга.` или `шт.`, а период укажи в названии позиции. `tochka_client.py` проверяет это через `choices` в argparse.
- **В закрывающих документах `SecondSide` использует строчные поля v1.0** — `kpp` и `secondSideName`, а НЕ форму v2.0 `KPP` и `legalName`. Точка молча отбрасывает форму v2.0 в закрывающих документах → в PDF у покупателя пропадает КПП → ЭДО отклоняет подписание. Кроме того, `Content.Act.totalAmount` обязателен на уровне блока, а не только на каждой позиции. См. [endpoints.md#closing-documents](references/endpoints.md#закрывающие-документы-акты--упд--торг-12--счёт-фактура).
- **Тело платёжного поручения — плоский `{"Data": {…поля…}}`**, а не `Data.Payment: [...]` — иначе API вернёт `"Field X: Field required"` по каждому полю.

Ошибка → как исправить (HTTP 501, 403, 401, таймауты колбэка OAuth, Keychain, рендер PDF): [references/errors.md](references/errors.md). Стратегические оговорки (нет ключей идемпотентности, кириллица в значениях enum, расхождения со стандартами Open Banking Банка России): [references/endpoints.md#operational-pitfalls](references/endpoints.md#операционные-подводные-камни).

## Скрипт-помощник

`scripts/tochka_client.py` — Python, только стандартная библиотека, 19 подкоманд. После `init` токен и умолчания подхватываются автоматически.

Порядок поиска токена: `$TOCHKA_TOKEN` → `access_token` OAuth из Keychain (с автообновлением) → хранилище учётных данных ОС → `~/.config/tochka-bank-api/token` (запасной путь с chmod 600).

У каждой подкоманды `--help` перечисляет точные флаги. Полный пример работы со счётом:

```bash
python3 scripts/tochka_client.py create-invoice \
  --document-number 7 --amount 10000 --purpose "Услуги" \
  --buyer-inn 7700000000 --buyer-name "ООО Покупатель" --buyer-kpp 770001001 \
  --save-pdf ru/customers/acme/payments/ --format id
```

`--document-number` **обязателен** в `create-invoice` и `create-closing-doc` — автоматического умолчания нет. Используй сквозной счётчик по клиенту (`max N + 1`). `--save-pdf DIR` сам скачивает отрендеренный PDF **и пишет JSON-сайдкар с тем же базовым именем** (`<filename>.json` рядом с `<filename>.pdf`) с полями `documentId`, `customerCode`, номер и дата документа, сумма, покупатель, id родительского счёта. Это единственный долговечный кэш `documentId` — у Точки нет эндпоинта списка, поэтому без сайдкара UUID придётся вручную копировать из интернет-банка при каждой следующей операции. **Коммить сайдкар вместе с PDF.** Для более сложных сценариев импортируй нужную функцию `cmd_*` из скрипта.

## Хук на уровне репозитория (только Claude Code)

`hooks/tochka-require-confirmation.sh` блокирует вызовы, меняющие состояние (`curl -X POST|PUT|PATCH|DELETE` к `enter.tochka.com`, а также подкоманды `create-*`, `send-*`, `delete-*`, `register-webhook`, `test-webhook`) и поднимает запрос разрешения с меткой `[PROD]` или `[SANDBOX]` и именем подкоманды. Вызовы только для чтения (`list-*`, `get-*`, `config`) проходят молча. Обхода через переменную окружения нет — встроенный запрос остаётся единственным путём подтверждения.

Установка и регистрация в `.claude/settings.json`: см. README исходного репозитория `rodion-m/tochka-bank-skill`.

## Офлайн-OpenAPI

[schemas/swagger.json](schemas/swagger.json) — OpenAPI 3.1.0, Tochka.API v1.90.4-stable (скачано 20.04.2026). Содержит только пути `v1.0` (59 операций); эндпоинтов `v2.0`, которыми пользуется клиент (`/open-banking/v2.0/statements`, `/payment/v2.0/for-sign`, `/acquiring/v2.0/payments`, `/invoice/v2.0/bills`), там **нет** — для них используй [endpoints.md](references/endpoints.md) и живой ReDoc.

Схемы ищи через `jq` (не читай файл целиком — он 440 КБ):

```bash
jq '.paths."/payment/v1.0/for-sign".post' schemas/swagger.json
jq '.components.schemas.PositionModel' schemas/swagger.json
jq '.paths | keys' schemas/swagger.json | head -20
```

Обновление: `curl https://enter.tochka.com/doc/openapi/swagger.json -o schemas/swagger.json`.

## Источники

- Документация: https://developers.tochka.com/docs/tochka-api/
- Живой ReDoc (источник истины по формам запросов и ответов): https://enter.tochka.com/doc/v2/redoc
