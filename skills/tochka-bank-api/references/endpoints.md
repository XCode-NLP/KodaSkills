# API Точка Банка — каталог эндпоинтов

Полные схемы запросов и ответов и правила валидации. Везде, где банк предлагает `v2.0`, используются пути `v2.0` (Open Banking, эквайринг, платежи, СБП). API счетов на оплату: `v1.0` и `v2.0` на продакшене, оба дают **501 с личным JWT**. Закрывающие документы — только `v1.0`.

Источник истины: **живой ReDoc https://enter.tochka.com/doc/v2/redoc** — Точка меняет пути и имена полей без semver. Схемы здесь верны на 20.04.2026.

База: `https://enter.tochka.com/uapi` (продакшен) или `https://enter.tochka.com/sandbox/v2`.

Заголовки: `Authorization: Bearer <token>`, `Content-Type: application/json` для POST и PUT.

## Счета

```
GET /open-banking/v2.0/accounts
```

Возвращает `Data.Account[]` с полями `accountId`, `customerCode`, `currency`, `accountType`, `accountSubType`, `status`. `customerCode` — внутренний идентификатор твоего юрлица или ИП в Точке, нужен почти везде; сохрани его один раз. Пример (продакшен, данные скрыты):

```json
{"Data": {"Account": [{"customerCode": "100000001",
  "accountId": "40702810900000000001/044525225",
  "status": "Enabled", "currency": "RUB",
  "accountType": "Business", "accountSubType": "CurrentAccount"}]}}
```

## Входящие платежи (эквайринг и СБП)

```
GET /acquiring/v2.0/payments?customerCode={code}
```

Платежи, полученные через мерчант-инструменты Точки (QR СБП, оплата по ссылке, интернет-эквайринг). Необязательные параметры запроса: `status`, `fromDate`, `toDate`, `page`, `perPage` (по умолчанию 1000).

Ответ — `Data.Operation[]` с полями `paymentType` (`sbp` или `card`), `paymentId`, `transactionId`, `createdAt`/`paidAt`, `purpose`, `amount` (float в рублях), `status`, `operationId`, `paymentLink`, `consumerId`.

Наблюдаемые статусы (v2.0): `APPROVED`, `REJECTED`, `PENDING`, `REFUNDED`. Полный enum `AcquiringPaymentStatus` (v1.0): `CREATED`, `APPROVED`, `ON-REFUND`, `REFUNDED`, `EXPIRED`, `REFUNDED_PARTIALLY`, `AUTHORIZED`, `WAIT_FULL_PAYMENT`. В v2.0 дополнительно встречаются `PENDING` и `REJECTED` (в enum v1.0 их нет).

**Сюда не входят** переводы на расчётный счёт из не-мерчантских источников — они видны только в полной выписке Open Banking (OAuth).

## Исходящие платёжные поручения — очередь «На подпись»

### Список черновиков

```
GET /payment/v2.0/for-sign?customerCode={code}
```

Платежи, которые сейчас в очереди «На подпись», независимо от того, созданы они через API или вручную в интернет-банке. После подписания и отправки они **пропадают из этого списка** — у личного JWT нет доступа к исполненным платежам.

Необязательный `status`. Для черновиков наблюдаются `Created` и `AwaitingSignature`.

### Создание платёжного поручения

```
POST /payment/v2.0/for-sign
```

**Форма тела — плоский `Data`** (проверено на продакшене 20.04.2026). Старые доки и примеры, сгенерированные агентами, показывают `Data.Payment: [...]` (массив) или `Data.Payment: {...}` (вложенный объект) — **оба варианта неверны**; API игнорирует эти поля и возвращает `"Field X: Field required"` по каждому обязательному полю.

```json
{
  "Data": {
    "accountCode": "40702810900000000001",
    "bankCode": "044525225",
    "counterpartyAccountNumber": "40702810400001234567",
    "counterpartyBankBic": "044525225",
    "counterpartyINN": "7707083893",
    "counterpartyKPP": "773601001",
    "counterpartyName": "ПАО Сбербанк",
    "paymentAmount": 15000.00,
    "paymentDate": "2026-04-20",
    "paymentNumber": 42,
    "paymentPriority": "5",
    "paymentPurpose": "Оплата по счёту №7 от 18.04.2026, без НДС",
    "supplierBillId": "0",
    "taxInfo": {"status":"0","kbk":"0","oktmo":"0","reasonCode":"0",
                "taxPeriod":"0","documentNumber":"0","documentDate":"0","payerStatus":"0"}
  }
}
```

Обязательны: `accountCode`, `bankCode`, `counterpartyBankBic`, `counterpartyAccountNumber`, `counterpartyName`, `paymentAmount`, `paymentDate`, `paymentPurpose`, а для контрагентов-компаний ещё `paymentNumber`, `paymentPriority`, `supplierBillId`, `taxInfo`, `counterpartyINN`, `counterpartyKPP`.

**Ограничения полей (swagger `PaymentForSignRequestModel`):**

| Поле | Ограничение |
|---|---|
| `accountCode` | ровно 20 символов |
| `bankCode` | ровно 9 символов (БИК твоего банка) |
| `counterpartyAccountNumber` | ровно 20 символов |
| `counterpartyBankBic` | ровно 9 символов |
| `counterpartyINN` | 10–12 символов (10 для юрлица, 12 для ИП) |
| `counterpartyKPP` | до 9 символов (`"0"` для ИП и физлиц) |
| `paymentNumber` | целое, 1–999999 |
| `paymentPurpose` | до 210 символов |
| `paymentDate` | формат `date` (`YYYY-MM-DD`, не дата-время) |

Необязательны (по swagger): `counterpartyBankCorrAccount` (20 символов), `email` (банк отправит PDF), `codePurpose` (поле 20 назначения платежа, строка `1–5` или пусто — для переводов физлицам на отдельных типах счетов), `payerINN` и `payerKPP` (если платишь за третье лицо).

Для неналоговых платежей блок `taxInfo` всё равно должен присутствовать со всеми значениями `"0"` (требование схемы). Для налоговых заполняй реальные КБК, ОКТМО и период.

**Проверенные правила валидации (продакшен):**

- `paymentDate` ≤ сегодня (`"Value error, should be less than today or equal"` для будущих дат).
- `paymentPurpose` не может содержать длинное тире `—` (U+2014) (`"Value error, forbidden symbols: —"`). Дефис `-` или запятая. Кириллица допустима.
- `counterpartyBankBic` и `counterpartyAccountNumber` проверяются по реестру Банка России. Выдуманные комбинации дают `"Проверьте номер счёта — в выбранном банке такого счёта нет"`.
- `accountCode` — только 20-значный номер счёта, без суффикса БИК через слэш из `accountId`. Разбери `accountId = "40702810900000000001/044525225"` → `accountCode = "40702810900000000001"`, `bankCode = "044525225"`.

### Подписание

API создаёт *черновик* в очереди «На подпись». Само подписание и отправка идут через мобильный или интернет-банк с SMS, если только в JWT нет `SignPaymentOrder` (редкость, требует аппаратного ключа, настроенного в Точке).

### Статус платежа

```
GET /payment/v2.0/status/{requestId}
```

Оговорка из документации: «Если платёж отредактировали в интернет-банке после создания через API, реальный статус этим методом определить нельзя — вернётся `Created`».

Разрешения: `CreatePaymentForSign` (черновик), `SignPaymentOrder` (автоподписание, редкость).

## Полная банковская выписка (Open Banking)

> ⚠️ **501 с личным JWT на продакшене.** Нужны OAuth и согласие ([auth.md](auth.md#поток-oauth-20-с-согласием-мультитенантный)). Песочница работает напрямую с `working_token`.

### 1. Создать выписку (асинхронно)

```
POST /open-banking/v2.0/statements
```

```json
{"Data": {"Statement": {
  "accountId": "40702810900000000001/044525225",
  "startDateTime": "2026-03-21",
  "endDateTime": "2026-04-20"}}}
```

Подводные камни:

- `startDateTime` и `endDateTime` — просто `YYYY-MM-DD`. ISO с ненулевым временем отклоняется.
- Запросы OAuth дополнительно требуют заголовок `CustomerCode: <твой customerCode>`.

Возвращает `Data.Statement.statementId` и `status: "Created"`. Обычно готово за секунды; на длинных диапазонах — до 24 часов.

Полный enum `StatementStatus`: `Created` → `Processing` → `Ready` (успех) или `Error` (терминальный). Опрашивай до `Ready` или `Error`; не зависай на `Processing` бесконечно.

### 2. Опрос через список

```
GET /open-banking/v2.0/statements
```

Возвращает ВСЕ выписки клиента. **Найди свою по `statementId`** и жди `status: "Ready"`. Эндпоинт статуса по id `GET /statements/{statementId}/status` существует, но список проще и содержит нагрузку, как только она готова.

### 3. Операции приходят внутри ответа

Когда `status == "Ready"`, массив `Transaction[]` уже вложен в объект Statement. Отдельного эндпоинта `/accounts/{id}/statements/{id}/payments` **нет** — этот путь на продакшене возвращает 501. Поле называется **`Transaction`** (в единственном числе, но это массив), а не `Payment`.

Пример операции (продакшен, данные скрыты):

```json
{"Amount": {"amount": 195.6, "currency": "RUB", "amountNat": 195.6},
 "status": "Booked",
 "paymentId": "cbs-tb-XX-0000000000",
 "transactionId": "cbs-tb;0000000000;1",
 "documentNumber": "12345",
 "documentProcessDate": "2026-04-20",
 "transactionTypeCode": "Платежное поручение",
 "creditDebitIndicator": "Credit",
 "description": "Оплата по договору. Без НДС",
 "DebtorAgent": {"name": "ООО \"Банк-Пример\"", "identification": "044525999"},
 "DebtorParty": {"inn": "7700000000", "kpp": "770001001", "name": "ООО \"Контрагент-Пример\""},
 "DebtorAccount": {"identification": "40702810000000000000"}}
```

Справочник полей (**не** в нотации OBIE, как утверждают старые руководства):

| Поле | Значение |
|---|---|
| `creditDebitIndicator` | `Credit` (приход) или `Debit` (расход) |
| `Amount.amount` | в рублях (не в копейках) |
| `description` | назначение платежа свободным текстом (НЕ `purpose` и НЕ `paymentPurpose`) |
| `documentProcessDate` | дата проводки в ISO |
| `documentNumber` | номер банковского документа |
| `transactionTypeCode` | кириллицей: `"Платежное поручение"`, `"Банковский ордер"` |
| `DebtorParty.{name,inn,kpp}` | для `Credit` — кто прислал деньги |
| `CreditorParty.{name,inn,kpp}` | для `Debit` — кто получил |
| `DebtorAccount.identification` / `CreditorAccount.identification` | номер счёта контрагента |
| `status` | `Booked` (проведено) или `Pending` (предварительно) |
| `TaxFields` | необязательно для налоговых платежей: `originatorStatus`, `kbk`, `oktmo`, `base`, `documentNumber`, `documentDate`, `type`, `field107` |
| `paymentId`, `transactionId` | внутренние идентификаторы банка |

В обёртке Statement есть `startDateBalance` и `endDateBalance` (остатки на границах периода).

## ИП против ООО — различия полей в счетах и платёжных поручениях

`SecondSide.type` (счета, закрывающие документы) и реквизиты контрагента (платёжные поручения):

| Поле | ООО и АО (`type: "company"`) | ИП (`type: "ip"`) |
|---|---|---|
| `taxCode` (ИНН) | 10 цифр | **12 цифр** |
| `KPP` | обязателен | **не передаётся** (или `"0"` в платёжном поручении) |
| `legalName` | `"ООО \"Название\""` | `"ИП Фамилия Имя Отчество"` |
| Типичный `ndsKind` | `nds_22` (общая система) или `without_nds` (УСН) | `without_nds` (УСН без льготы по НДС), `nds_5` и `nds_7` (УСН со льготой), `nds_22` (общая) |
| `taxInfo` в платёжном поручении | для платежей в бюджет | так же; ИП на УСН платит взносы и налог через те же поля (другие КБК) |

Для владельца токена — **ИП на УСН** — Точка не вводит особых ограничений на эндпоинты: клиенты-ИП используют ту же схему JWT или OAuth, что и юрлица. Типичный сценарий: выписка и счета с `ndsKind: "without_nds"`. Льготные ставки `nds_5` и `nds_7` применяются, только если ИП явно перешёл на УСН с НДС.

Старое значение `"entrepreneur"` (вместо `"ip"`) больше не принимается.

## Счета на оплату (на продакшене только OAuth)

> ⚠️ **501 с личным JWT на продакшене.** В песочнице работает (удобно для разработки и отладки схем), на продакшене нужны OAuth и согласие.

> ⚠️ **Эндпоинта списка нет.** `GET /invoice/v2.0/bills` без идентификатора не существует. Любой из путей `/bills`, `/bills-list`, `/invoices`, `/documents`, `/outgoing`, `/my` возвращает 501. Счёт доступен только по известному `documentId` (он приходит из `POST /bills` или копируется вручную из интернет-банка). Если счёт создан через веб-интерфейс и `documentId` неизвестен — **найти его через API нельзя**. Подтверждено 20.04.2026.

### Создание

```
POST /invoice/v2.0/bills
```

> **Раздвоение схем v1.0 и v2.0.** Swagger v1.90.4-stable описывает только `/invoice/v1.0/bills` с другими именами полей: `SecondSide.secondSideName` (не `legalName`), `SecondSide.kpp` (не `KPP`), `Positions[].positionName` (не `name`), а `Content.Invoice.{number,date,paymentExpiryDate}` — номер, дата и срок оплаты **вложены в `Content.Invoice`**. На продакшене работает форма v2.0 (плоские `documentNumber`, `documentDate`, `paymentExpirationDate` на верхнем уровне, заглавные `legalName` и `KPP`, `Positions[].name`) — именно её использует этот навык. Если когда-нибудь обратишься к v1.0 напрямую, переключайся на канонические имена из swagger.

Тело (точная форма — регистр важен):

```json
{
  "Data": {
    "customerCode": "100000001",
    "accountId": "40702810900000000001/044525225",
    "documentDate": "2026-04-20",
    "documentNumber": "INV-2026-001",
    "paymentExpirationDate": "2026-05-20",
    "SecondSide": {"taxCode": "7700000000", "KPP": "770001001",
                   "type": "company", "legalName": "ООО \"Покупатель\""},
    "Content": {"Invoice": {
      "number": "INV-2026-001", "totalAmount": 50000.00,
      "Positions": [{"name": "Консультационные услуги", "price": 50000.00,
        "quantity": 1, "totalAmount": 50000.00,
        "unitCode": "услуга.", "ndsKind": "without_nds"}]}}
  }
}
```

Поля:

- `SecondSide.type`: `"company"` (ООО или АО — 10-значный `taxCode` и `KPP`) либо `"ip"` (ИП — 12-значный `taxCode`, без КПП). Старое `"entrepreneur"` отклоняется.
- `Positions[].unitCode` — русская краткая форма с точкой на конце (не код ОКЕИ). Принимаются: `'шт.'`, `'тыс.шт.'`, `'компл.'`, `'пар.'`, `'усл.ед.'`, `'упак.'`, `'услуга.'`, `'пач.'`, `'мин.'`, `'ч.'`, `'сут.'`, `'г.'`, `'кг.'`, `'л.'`, `'м.'`, `'м2.'`, `'м3.'`, `'км.'`, `'га.'`, `'кВт.'`, `'кВт.ч.'`.
- `Positions[].ndsKind` (ставки НДС 2026):
  - `without_nds` — без НДС (ИП на УСН без льготы по НДС либо освобождение по ст. 145 НК);
  - `nds_0` — 0 % (экспорт, отдельные операции);
  - `nds_5` — 5 % (льгота УСН для выручки 20–272,5 млн ₽ в год, без вычета);
  - `nds_7` — 7 % (льгота УСН для выручки 272,5–490,5 млн ₽ в год, без вычета);
  - `nds_10` — 10 % (детские товары, продукты, лекарства, книги);
  - `nds_22` — 22 % (стандартная с 01.01.2026, заменила 20 %).

Старый enum (`vat_20`, `vat_10`, `without_vat`) больше не принимается.

**Ограничения позиции (swagger `PositionModel`):**

- `price`: число, `>= 0`;
- `quantity`: число, `0 < q < 10000000` (не ноль);
- `totalAmount`: число, `>= 0`;
- `totalNds` — необязательно, НДС по позиции (сервер обычно считает сам).

Необязательные поля `Content.Invoice`: `basedOn` (свободный текст «на основании»), `comment`, `totalNds`.

Ответ: `Data.documentId`.

### Получить PDF

```
GET /invoice/v1.0/bills/{customerCode}/{documentId}/file
```

Бинарный `application/pdf` (около 50 КБ). **Первый вызов может занять 30+ секунд** (сервер рендерит по требованию) — ставь таймаут не меньше 60 с.

### Проверить статус оплаты

```
GET /invoice/v1.0/bills/{customerCode}/{documentId}/payment-status
GET /invoice/v2.0/bills/{customerCode}/{documentId}/payment-status
```

```json
{"Data": {"paymentStatus": "payment_paid"}}
```

`PaymentStatusEnum` в swagger: ровно три значения — `payment_waiting`, `payment_paid`, `payment_expired`. Прежние домыслы про `payment_cancelled` — **в API его нет**. Ручное удаление счёта в интернет-банке просто удаляет его; состояния «отменён после оплаты» не существует.

### Отправить на почту

```
POST /invoice/v1.0/bills/{customerCode}/{documentId}/email
```

Тело: `{"Data": {"email": "buyer@example.com"}}`

Старый суффикс `/send-to-email` возвращает 404. В swagger используется просто `/email`. Для v2.0 эта операция не описана — оставайся на v1.0.

### Полный API счетов — ровно 5 операций

**Все принимают `customerCode` в пути** (не только в теле):

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/invoice/v2.0/bills` | Создание (возвращает `documentId`) |
| DELETE | `/invoice/v2.0/bills/{customerCode}/{documentId}` | Удаление |
| POST | `/invoice/v1.0/bills/{customerCode}/{documentId}/email` | Отправка на почту |
| GET | `/invoice/v1.0/bills/{customerCode}/{documentId}/file` | Отрендеренный PDF |
| GET | `/invoice/v1.0/bills/{customerCode}/{documentId}/payment-status` | Статус оплаты |

**Полезный приём** для поиска `documentId` счёта, созданного через веб-интерфейс: открой счёт в интернет-банке по адресу https://i.tochka.com/bank/m/document_flow/document/{documentId} — UUID в URL и есть нужный для API `documentId`.

Старые руководства и догадки агентов использовали `/invoice/v2.0/bills/{documentId}/*` (без customerCode) — **неверно**, на продакшене это 501. `customerCode` в пути обязателен для операций над конкретным счётом.

## QR-коды СБП

### Регистрация торговой точки (один раз)

```
POST /sbp/v2.0/register-retailer/account/{accountId}
```

Возвращает `merchantId`.

### Регистрация QR-кода

```
POST /sbp/v2.0/qr-code/merchant/{merchantId}/account/{accountId}
```

```json
{"Data": {"qrcType": "02", "amount": 150000, "currency": "RUB",
          "paymentPurpose": "Заказ №1234"}}
```

`qrcType`: `"01"` — статический, `"02"` — динамический.

**⚠️ `amount` в копейках, а не в рублях.** В swagger поле `RegisterQRCode` прямо названо «Сумма в копейках». 1500 ₽ → `150000`. Это отличается от эквайринга `/payments`, где `amount` — float в рублях, и перепутать легко. Кроме того, у `paymentPurpose` в QR СБП `maxLength: 140` (жёстче, чем 210 у платёжных поручений).

**СБП НСПК v9.1 (с апреля 2026):** `bankCode` (БИК) стал обязательным параметром при регистрации торговой точки и в части эндпоинтов СБП. Подпись вебхука `incomingSbpPayment` тоже изменилась — обнови JWKS перед проверкой.

### Список QR-кодов

```
GET /sbp/v2.0/qr-codes/{merchantId}
```

Разрешения: `EditSBPData` (запись), `ReadSBPData` (чтение). ReDoc: https://enter.tochka.com/doc/v2/redoc#tag/SBP-API.

## Закрывающие документы (акты / УПД / ТОРГ-12 / счёт-фактура)

Доступ только через OAuth, разрешение то же, что у счетов, — `ManageInvoiceData`. Естественное продолжение после оплаты счёта.

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/invoice/v1.0/closing-documents` | Создать акт, УПД, ТОРГ-12 или счёт-фактуру |
| GET | `/invoice/v1.0/closing-documents/{customerCode}/{documentId}/file` | Скачать PDF |
| POST | `/invoice/v1.0/closing-documents/{customerCode}/{documentId}/email` | Отправить на почту |
| DELETE | `/invoice/v1.0/closing-documents/{customerCode}/{documentId}` | Удалить |

Тело (swagger `ClosingDocumentCreateRequestModel`):

```json
{
  "Data": {
    "customerCode": "100000001",
    "accountId": "40702810900000000001/044525225",
    "SecondSide": {"taxCode": "7700000000", "kpp": "770001001", "type": "company", "secondSideName": "ООО \"Покупатель\""},
    "Content": {
      "Act": {
        "date": "2026-04-30",
        "number": "A-1",
        "totalAmount": 50000,
        "Positions": [{"name": "Услуга", "price": 50000, "quantity": 1, "totalAmount": 50000, "unitCode": "шт.", "ndsKind": "without_nds"}]
      }
    },
    "documentId": "<необязательный documentId родительского счёта>"
  }
}
```

`Content` — размеченное объединение: одно из `Act` (акт выполненных работ), `PackingList` (ТОРГ-12), `Invoicef` (счёт-фактура), `Upd` (УПД). Форма позиции совпадает с `PositionModel` счёта. Необязательный `documentId` связывает закрывающий документ с родительским счётом — интернет-банк группирует их в одну ленту.

**⚠️ Критичные различия форм v1.0 и v2.0 (проверено на продакшене 21.04.2026):**

- **`SecondSide` использует строчные `kpp` и `secondSideName`**, а НЕ форму счёта v2.0 (`KPP` и `legalName`). Если отправить здесь `KPP`, Точка молча его отбросит → в отрендеренном PDF у покупателя пропадёт КПП → подписание в ЭДО упадёт с `"Не получилось подписать документ. Проверьте ИНН или КПП контрагента."`. При создании документ всё равно получит `documentId`, поэтому баг проявляется только на подписании.
- **`Content.Act.totalAmount` обязателен** на уровне блока (не только внутри каждой позиции). Без него вернётся `400 Validation Error: Field Content-ContentAct-Act-totalAmount : Field required`.

Хелперы: `create-closing-doc`, `get-closing-doc`, `send-closing-doc`, `delete-closing-doc`.

## Балансы

```
GET /open-banking/v1.0/balances
GET /open-banking/v1.0/accounts/{accountId}/balances
```

Снимок на текущий момент. Работает с личным JWT (`ReadBalances`). Слэш в `accountId` внутри URL нужно кодировать как `%2F`.

Хелперы: `get-balance` (все счета) или `get-balance --account-id …` (один).

## Вебхуки

Типы (swagger `WebhookTypeEnum`): `incomingPayment`, `outgoingPayment`, `incomingSbpPayment`, `acquiringInternetPayment`, `incomingSbpB2BPayment`.

| Метод | Путь | Назначение |
|---|---|---|
| PUT | `/webhook/v1.0/{client_id}` | Зарегистрировать URL и события |
| POST | `/webhook/v1.0/{client_id}` | Изменить существующий |
| GET | `/webhook/v1.0/{client_id}` | Получить конфигурацию |
| DELETE | `/webhook/v1.0/{client_id}` | Удалить |
| POST | `/webhook/v1.0/{client_id}/test_send` | Тестовое событие на зарегистрированный URL |

Тело PUT: `{"webhooksList": ["incomingPayment", "incomingSbpPayment"], "url": "https://your-endpoint/hook"}`. `url` должен быть `https://`, не длиннее 2083 символов. Требуется `ManageWebhookData`.

`{client_id}` — это `client_id` OAuth-приложения (для личного JWT — тот `client_id`, что показан при генерации JWT в интернет-банке). Сразу после регистрации вызови `test_send`, чтобы убедиться, что приёмник настроен.

## Платёжные ссылки (интернет-эквайринг)

```
POST /acquiring/v1.0/payments                  # обычный
POST /acquiring/v1.0/payments_with_receipt     # с фискальным чеком (ОФД)
GET  /acquiring/v1.0/payments/{operationId}
POST /acquiring/v1.0/payments/{operationId}/capture    # двухстадийное списание
POST /acquiring/v1.0/payments/{operationId}/refund     # полный или частичный возврат
```

Обязательны (обычный): `customerCode` (9 символов), `amount` (в рублях, НЕ в копейках!), `purpose`, `paymentMode` (`["sbp", "card"]`). Необязательны: `merchantId`, `paymentLinkId` (твой внешний идентификатор), `redirectUrl`, `failRedirectUrl`, `ttl` (1–44640 минут, по умолчанию 10080, то есть 7 дней), `preAuthorization` (`true` → нужно вызвать `/capture`, чтобы списать), `saveCard`, `consumerId`.

Возвращает `Data.Operation.{operationId, paymentLink}` — передай `paymentLink` клиенту. Требуется `MakeAcquiringOperation`.

Хелпер: `create-payment-link`. Для сценариев с предварительной авторизацией навык НЕ списывает автоматически — вызывай `/capture` вручную, когда отгружаешь товар.

## Суточный реестр эквайринга

```
GET /acquiring/v1.0/registry?customerCode=...&merchantId=...&date=YYYY-MM-DD
```

Суточная сводка расчётов (реестр интернет-эквайринга): итоги, комиссии, сумма к перечислению. Полезно для сверки с банковской выпиской в конце месяца. Необязательный `paymentId` для детализации. Требуется `ReadAcquiringData`.

Хелпер: `list-registry --date YYYY-MM-DD`.

## Согласия (интроспекция OAuth)

```
GET  /consent/v1.0/consents                      # все согласия для токена приложения
GET  /consent/v1.0/consents/{consentId}          # детали одного согласия
GET  /consent/v1.0/consents/{consentId}/child    # дочерние согласия (мультиаккаунт)
POST /consent/v1.0/consents                      # создать новое (настройка)
```

Вызовы только для чтения. Полезны, когда OAuth начинает возвращать 403: проверь области действующего согласия, прежде чем предполагать истечение токена.

Хелперы: `list-consents`, `get-consent <consentId>`.

## Формат accountId — критичный подводный камень

`accountId` — не просто номер счёта. Формат: `{20-значный-счёт}/{9-значный-БИК}`, со слэшем внутри:

```
"accountId": "40702810900000000001/044525225"
```

В **телах** запросов передавай как есть. В **URL** слэш нужно кодировать как `%2F`:

```
GET /open-banking/v2.0/accounts/40702810900000000001%2F044525225/statements/{statementId}/payments
```

Забудешь закодировать — `404 HTTPNotFound: Not found statement under account`.

## Операционные подводные камни

Это не сообщения об ошибках, а архитектурные оговорки, которые надо учесть в планировании:

- **Ключей идемпотентности нет:** эндпоинты платежей не принимают `Idempotency-Key`. Веди собственные `paymentNumber` или внешние идентификаторы, чтобы не создать дубль при повторе.
- **Кириллица в ответах:** часть полей и значений enum — кириллические строки (`"Исполнен"`, `unitCode` `"услуга."`). Сравнивай с точной строкой из ReDoc, а не с переводом.
- **Песочница не равна продакшену:** песочница принимает `working_token` для всего (включая счета и Open Banking). На продакшене доступ делится по уровням авторизации. Отладка схем — песочница; проверка доступа — продакшен с токеном с малыми правами.
- **Расхождение со стандартами Open Banking Банка России:** текущее API Точки **не** соответствует утверждённым стандартам АФТ и ОБР Банка России (wiki.openbankingrussia.ru, wiki.opendatarussia.ru) — ни Accounts v2.0 и v3.0, ни Payment Initiation v1.0.0, ни FAPI Advanced v2.0. Ближайший водораздел — **01.10.2026** (дата введения пакета стандартов ЦБ v2.0): ожидай возможного перевыпуска OAuth-потока и смены имён полей в `/accounts` и `/payment`. Не копируй примеры ОБР и OBIE, рассчитывая, что они заработают в Точке.
