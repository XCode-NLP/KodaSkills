# API Точка Банка — вебхуки

Доставка событий из Точки на твой сервер в реальном времени. Настоятельно предпочтительнее опроса для уведомлений о входящих платежах.

## Настройка URL вебхука

В интернет-банке → **Интеграции и API** → существующая интеграция JWT или OAuth → задай URL вебхука. URL должен:

- быть HTTPS;
- отвечать HTTP 200 примерно за 10 секунд;
- принимать `POST` с `Content-Type: text/plain` (Точка отправляет тела, подписанные JWT, в сыром виде).

`client_id`, который показан рядом с JWT, нужен для проверки подписи вебхука.

## Доступные события

| Имя события | Когда срабатывает |
|------------|------------|
| `incomingPayment` | Входящий платёж не через СБП зачислен на один из твоих счетов |
| `incomingSbpB2BPayment` | Входящий платёж СБП (B2B или C2B по QR) |
| `outgoingPayment` | Исходящий платёж исполнен банком |
| `acquiringInternetPayment` | Платёж картой через интернет-эквайринг завершён |
| `invoiceStatusChanged` | Смена статуса счёта на оплату (оплачен, истёк и т. п.) |
| `sbpInboundC2BPayment` | Платёж C2B через СБП по динамическому QR |

Задержка: обычно меньше 20 секунд от события на стороне банка до доставки вебхука.

Авторитетный список: https://developers.tochka.com/docs/tochka-api/opisanie-metodov/vebhuki

## Формат запроса

Тело — JWT, подписанный JWS (Точка называет это «нагрузкой вебхука»). После декодирования получается JSON вида:

```json
{
  "webhookType": "incomingPayment",
  "client_id": "your_client_id",
  "data": {
    "accountId": "40802810500000123456",
    "amount": 15000.00,
    "currency": "RUB",
    "counterpartyName": "ООО \"Плательщик\"",
    "counterpartyINN": "7700000000",
    "paymentPurpose": "Оплата по счёту №7",
    "paymentDate": "2026-04-20",
    "paymentId": "..."
  }
}
```

Точный набор полей зависит от типа события — залогируй первые несколько нагрузок в разработке, чтобы сверить форму с реальными сообщениями, которые приходят на твой счёт.

## Проверка подписи

Тело вебхука — JWT, подписанный Точкой. Шаги проверки:

1. Получи URL JWKS из документа обнаружения OIDC (чтобы пережить будущие смены URL): запроси `https://enter.tochka.com/connect/.well-known/openid-configuration` и перейди по `jwks_uri`.
2. Загрузи JWKS по полученному URL.
3. Декодируй заголовок JWT, чтобы получить `kid` (идентификатор ключа).
4. Найди соответствующий публичный ключ в JWKS.
5. Проверь подпись этим ключом.
6. Отклони, если claim `client_id` не совпадает с твоим зарегистрированным `client_id`.

Пример на Python (с `pyjwt[crypto]` и `requests`):

```python
import jwt, requests

# Получаем JWKS через discovery — захардкоженный /connect/jwks сломается, когда Точка сменит путь.
DISCOVERY = requests.get("https://enter.tochka.com/connect/.well-known/openid-configuration").json()
JWKS = requests.get(DISCOVERY["jwks_uri"]).json()

def verify_webhook(raw_body: bytes, expected_client_id: str) -> dict:
    token = raw_body.decode("ascii").strip()
    unverified_header = jwt.get_unverified_header(token)
    key = next(k for k in JWKS["keys"] if k["kid"] == unverified_header["kid"])
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
    payload = jwt.decode(token, public_key, algorithms=[unverified_header["alg"]],
                        audience=expected_client_id)
    return payload
```

Сверь claim audience с актуальной документацией Точки перед выпуском: URL JWKS теперь определяется динамически, но контракт `aud` может меняться.

## Идемпотентность и повторы

Точка повторяет неудачные доставки (ответы не 2xx) с экспоненциальной задержкой до примерно 24 часов. Считай события доставленными **как минимум один раз**:

- храни `paymentId` (или аналогичное уникальное поле для каждого типа события) в таблице дедупликации;
- делай обработчик фактически идемпотентным — при дубле возвращай 200, не обрабатывая повторно.

Если ты когда-нибудь вернёшь 5xx из-за настоящего бага, исправь его и **попроси ручной повтор** через поддержку Точки — собственного эндпоинта повтора нет.
