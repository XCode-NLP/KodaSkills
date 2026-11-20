# API Точка Банка — авторизация

Два потока: **JWT** (простой, для одной компании) и **OAuth 2.0 + согласия** (мультитенантный). Выбирай JWT, если только не строишь SaaS, который получает доступ к чужим счетам.

## JWT (рекомендуется для автоматизации своего счёта)

### Генерация в интернет-банке

1. https://enter.tochka.com (веб-интернет-банк).
2. **Интеграции и API** → **Подключить**.
3. **Сгенерировать JWT-ключ**.
4. Задай:
   - имя токена (любая метка);
   - TTL — минимальную рабочую длительность;
   - разрешения (см. [Разрешения](#разрешения)) — сними галочки с ненужных;
   - компании — по умолчанию включены все компании пользователя.
5. Подтверди по SMS.
6. Скопируй **JWT** и **client_id** (client_id нужен для настройки вебхуков).

После закрытия страницы JWT повторно не показывается. Сразу сохрани его в менеджер секретов.

### Использование JWT

```
Authorization: Bearer <jwt>
```

Заметки:

- Изменять разрешения нельзя — любое изменение требует перевыпуска (новый JWT и новый `client_id`).
- Отзыв: удали токен в интернет-банке → последующие вызовы вернут 403.
- Напоминание о перевыпуске появляется примерно за неделю до истечения TTL.
- Источник: https://developers.tochka.com/docs/tochka-api/algoritm-raboty-s-jwt-tokenom

## Поток OAuth 2.0 с согласием (мультитенантный)

Используй его, только когда конечный пользователь (другой человек или компания, не интегратор) даёт твоему приложению доступ к своему счёту в Точке. Это стандартный OAuth 2.0 с двумя типами grant: `client_credentials` (приложение к приложению) и `authorization_code` (делегированный доступ пользователя).

### Общий порядок

1. **Зарегистрируй приложение** в Точке — получи `client_id` и `client_secret`.
2. **Получи токен приложения** через `client_credentials`:

   ```
   POST https://enter.tochka.com/connect/token
   Content-Type: application/x-www-form-urlencoded
   grant_type=client_credentials&client_id=...&client_secret=...&scope=accounts payments
   ```

3. **Создай согласие** (оно определяет, что предлагается авторизовать пользователю):

   ```
   POST https://enter.tochka.com/uapi/consent/v1.0/consents
   Authorization: Bearer <app_token>
   Content-Type: application/json
   { "Data": { "permissions": ["ReadAccountsBasic", "ReadStatements"] } }
   ```

   Ответ: `Data.consentId`. Канонический путь по swagger v1.90.4-stable — `/uapi/consent/v1.0/consents`. Устаревший псевдоним `/uapi/v1.0/consents` (без сегмента `consent/`) на 20.04.2026 ещё отвечает на продакшене, но новый код должен использовать каноническую форму.

4. **Перенаправь пользователя** авторизовать согласие:

   ```
   https://enter.tochka.com/connect/authorize?
     response_type=code&
     client_id=<your_client_id>&
     redirect_uri=<your_callback>&
     scope=accounts statements&
     consent_id=<consentId>
   ```

5. **Обменяй полученный `code` на токены**:

   ```
   POST https://enter.tochka.com/connect/token
   grant_type=authorization_code&code=...&redirect_uri=...&client_id=...&client_secret=...
   ```

6. Используй полученный `access_token` (24 ч) для вызовов API. Обновляй через `refresh_token` (30 дней).

### Время жизни токенов

| Токен | Срок |
|---|---|
| Access token | 24 часа |
| Refresh token | 30 дней |
| JWT (из интернет-банка) | задаёт пользователь |

Источник: https://developers.tochka.com/docs/tochka-api/algoritm-raboty-po-oauth-2.0

## Песочница

База: `https://enter.tochka.com/sandbox/v2`. Регистрация не нужна. Используй описанный в документации песочный JWT (обычно `Bearer working_token` — сверься с https://developers.tochka.com/docs/tochka-api/pesochnica). Песочница отдаёт мок-данные и принимает мок-записи, но не все продакшен-эндпоинты там повторены.

## Разрешения

Гранулярные разрешения, выбираемые при генерации JWT или при запросе согласия OAuth. Список ниже **авторитетен** — скопирован дословно из ответа валидации Точки 20.04.2026. Всё, чего в списке нет, отклоняется.

### Полный принимаемый набор (19 значений)

```
ReadAccountsBasic, ReadAccountsDetail, ReadBalances, ReadStatements,
ReadTransactionsBasic, ReadTransactionsCredits, ReadTransactionsDebits,
ReadTransactionsDetail, ReadCustomerData, ReadSBPData, EditSBPData,
CreatePaymentForSign, CreatePaymentOrder, ReadAcquiringData,
MakeAcquiringOperation, ManageInvoiceData, ManageWebhookData,
MakeCustomer, ManageGuarantee
```

(Источник: тело ошибки, которое возвращает `POST /uapi/v1.0/consents` при неверном разрешении — Точка услужливо перечисляет все принимаемые значения. Публичная документация на https://developers.tochka.com/docs/tochka-api/api/rabota-s-razresheniyami устарела; истина — в ответе выше.)

### По сценариям

**Счета и балансы:** `ReadAccountsBasic` (список счетов), `ReadAccountsDetail` (полные реквизиты), `ReadBalances` (балансы), `ReadCustomerData` (данные юрлица — **не** `ReadCustomers`, как пишут старые доки).

**Выписки и операции:** `ReadStatements` (полная асинхронная выписка Open Banking), `ReadTransactionsBasic` / `Credits` / `Debits` / `Detail`.

**Исходящие платежи:** `CreatePaymentForSign` (черновик в очередь «На подпись»), `CreatePaymentOrder` (прямое создание).

**Счета на оплату:** `ManageInvoiceData` — создание, чтение, изменение, удаление (покрывает всё; `ReadInvoiceData` не существует).

**СБП:** `ReadSBPData` (чтение данных мерчанта), `EditSBPData` (регистрация и правка QR-кодов, настроек мерчанта).

**Эквайринг:** `ReadAcquiringData` (чтение), `MakeAcquiringOperation` (создание и управление — **не** `EditAcquiringData`).

**Вебхуки:** `ManageWebhookData`.

**Специализированные (обычно не нужны):** `MakeCustomer` (банки-партнёры), `ManageGuarantee` (банковские гарантии).

**Принцип наименьших прав:** запрашивай только то, что действительно нужно. В OAuth изменение согласия после создания означает его пересоздание и повторную авторизацию пользователя. `scripts/tochka_client.py` использует 17 из 19 (константа `DEFAULT_OAUTH_PERMISSIONS`; пропускает `MakeCustomer` и `ManageGuarantee`).

## Жизненный цикл токена и обработка 403

При 403:

1. Проверь срок токена (у JWT — декодируй claim `exp`; у OAuth — проверь дату обновления).
2. Если истёк:
   - JWT — перегенерируй в интернет-банке;
   - OAuth — обнови через `grant_type=refresh_token`.
3. Если не истёк — неверен набор разрешений; проверь, есть ли у токена разрешение для этого эндпоинта.
4. Песочница иногда возвращает 403 на эндпоинтах, которых не реализует, — попробуй тот же вызов на продакшене с токеном с минимальными правами.

Обновление OAuth:

```bash
curl -X POST https://enter.tochka.com/connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&refresh_token=<rt>&client_id=...&client_secret=..."
```

## Мастера и регистрация OAuth-приложения

### Почему префикс `!` обязателен

`init` и `init --oauth` читают секреты через `getpass` (и `input()` для подтверждений). Им нужен настоящий TTY (`termios`); инструмент Bash в Claude Code его не даёт, поэтому запуск через агента молча зависает или падает с `EOFError`. Мастер обнаруживает это при старте и завершается с понятным сообщением.

**Схема:** агент просит пользователя выполнить команду в своём shell через префикс `!`:

```
! python3 scripts/tochka_client.py init
```

С `!` команда выполняется в живом TTY пользователя; секрет JWT или OAuth вводится прямо в его терминал и не проходит ни через канал вызова инструментов агента, ни через транскрипт разговора.

**Никогда не проси пользователя вставлять продакшен-JWT в чат** — он попадёт в резервные копии транскрипта. Если это всё же случилось, немедленно ротируй: интернет-банк → Интеграции и API → удалить токен → создать новый. Вставлять песочный `working_token` безопасно; поток с `!` нужен только для продакшен-JWT.

### Мастер `init` (личный JWT)

Мастер:

1. Объясняет, как сгенерировать JWT в интернет-банке (Интеграции и API → Сгенерировать JWT-ключ) и какие разрешения отметить.
2. Читает JWT скрытым вводом (`getpass` — не пишется в историю shell).
3. **Проверяет** его на продакшене через `GET /accounts` — сохраняет только при успехе.
4. **Кладёт JWT в хранилище учётных данных ОС** (шифрование на диске, доступ по паролю или биометрии):
   - macOS → Keychain (`security add-generic-password`);
   - Linux → `secret-tool` (GNOME Keyring или KWallet через libsecret);
   - Windows → Credential Manager;
   - WSL → запасной путь на Windows Credential Manager через `powershell.exe`.
5. Если хранилище недоступно — запасной путь `~/.config/tochka-bank-api/token` с chmod 600 (с предупреждением, что это менее безопасно).
6. Печатает `customerCode` и `accountId` (нужны для команд счетов и выписок).
7. Сохраняет умолчания в `~/.config/tochka-bank-api/config.json`.

Принудительно только файл (headless): `init --storage file`.

Песочница: префикс `TOCHKA_SANDBOX=1`. Используй общий `working_token` — проще просто `export TOCHKA_TOKEN=working_token TOCHKA_SANDBOX=1` без запуска `init`.

### Регистрация OAuth-приложения (нужна только для `init --oauth`)

Один раз на https://i.tochka.com/bank/services/m/integration/new — обязательна для API счетов на оплату, закрывающих документов и полной выписки Open Banking. Проверенные подводные камни (20.04.2026):

- **`Redirect URL` должен быть HTTPS.** Простой `http://` отклоняется.
- **`localhost` в поле Redirect URL НЕ принимается** (хотя в собственных примерах документации Точки он есть). Используй `127.0.0.1` или настоящий домен. Форма молча отклоняет `https://localhost:8443/callback`, но принимает `https://127.0.0.1:8443/callback`.
- Рекомендуемый шаблон: `https://127.0.0.1:8443/callback`. Порт может быть любым свободным; `/callback` произволен, но фиксируется после регистрации.
- `client_secret` **повторно не показывается** после закрытия формы регистрации — если потерял, придётся перегенерировать или пересоздать приложение.

`init --oauth` по умолчанию использует `https://127.0.0.1:8443/callback`. Передай `--redirect-url <полный URL>`, если у тебя зарегистрирован другой (без этого флага на этапе браузера будет `invalid_redirect_uri`, а затем молчаливый таймаут сервера колбэка на 5 минут — всегда сверяй совпадение заранее). Мастер поднимает локальный HTTPS-сервер (`mkcert`, если установлен, иначе самоподписанный — браузер предупредит, подтверди), открывает браузер на `connect/authorize`, обменивает код и кладёт `client_id`, `client_secret` и `refresh_token` в Keychain.

Срок жизни refresh-токена — 30 дней. Если за это время ни один вызов OAuth-эндпоинта не случился, токен тихо умирает: симптом — 401 на `list-statement` или `create-invoice`. Лечение — заново запустить `init --oauth`.
