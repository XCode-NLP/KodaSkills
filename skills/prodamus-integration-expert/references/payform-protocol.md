# Протокол Prodamus Payform

Первоисточник — живая документация: https://help.prodamus.ru/ (карта разделов —
`help-prodamus-map.md`). Этот файл — выжимка, выверенная по шести боевым
интеграциям Prodamus (июль 2026); при расхождении с живой документацией
приоритет у неё, но пометки «prod-факт» проверены работающим кодом.

У каждого клиента Prodamus есть своя платёжная страница (payform) с адресом
вида `https://<name>.payform.ru`. Мерчантский домен может редиректить на
`a.payform.ru` — не завязывайся на host ответа.

## Валидация payform-домена

Белый список: `*.payform.ru`, `*.prodamus.ru`, `*.prodamus.tech`
(prod-факт: списки в разных интеграциях различаются — актуальный набор
уточняй у Prodamus). Боевой алгоритм нормализации: trim → срезать протокол →
rtrim `/` → regex `([\w\-]+\.)*[\w\-]+\.(payform\.ru|prodamus\.ru|prodamus\.tech)`
(регистронезависимо) → добавить `https://`. Текст ошибки пользователю:
«URL должен быть вида имя.payform.ru, у вас: …».

Негативные кейсы, которые обязан отсекать валидатор (из боевых тестов):
`evil.com/payform.ru` (домен в path), `evil.com@demo.payform.ru` (userinfo),
`demo.payform.ru:8080` (порт), `demo.payform.ru.evil.com` (суффикс),
`evilpayform.ru` (без точки).

Телефон покупателя: форма prefill'ит только формат `^\+7\d{10}$` —
`79…` без плюса молча игнорируется. Нормализуй 8→+7 (prod-факт).

## Способы создания оплаты

1. `do=link` — серверная генерация ссылки (middleware: ссылку сохранить
   и доставить).
2. `do=pay` — прямой redirect покупателя (CMS/сайты), payload подписывается.
3. Платёжный виджет — оплата на странице сайта (живая документация).

### do=link

```
GET https://{payform}?do=link&sys={sys}&order_id={id}
    &products[0][name]=...&products[0][price]=...&products[0][quantity]=...
    &urlNotification={webhook-URL}
```

Ответ — тело с готовым (коротким) URL. Боевой парсинг: `trim(body)` →
`FILTER_VALIDATE_URL`; если не URL — распарсить JSON и взять
`payment_link ?? link` (prod-факт: Prodamus может вернуть JSON-обёртку).
Проверяй HTTP 200 и `str_starts_with(body, 'http')`.

Подпись у do=link опциональна (три боевые интеграции работают без неё).
Если передаёшь `sign` — он считается по query-канонизации, а не JSON
(см. `hmac.md`, «Две схемы подписи»).

Probe-валидация реквизитов (альтернатива validateSecretKey, prod-паттерн):
подписанная ссылка `do=link&order_id=__probe__&sum=1.00`, GET, timeout 5 c:
200/302 → ключ верный; 400/401/403 → неверный; 5xx/timeout → повторить позже.

### do=pay

```
https://{payform}?do=pay&sys=...&order_id=...&products[...]
    &urlSuccess=...&urlReturn=...&urlNotification=...&signature={hmac}
```

Payload подписывается полем `signature` (JSON-канонизация, `hmac.md`).
Query-string собирать строго RFC3986: в PHP —
`http_build_query($data, '', '&', PHP_QUERY_RFC3986)`. Для do=link сервер
терпим к кодированию, для do=pay — нет (подпись по значениям).

## Параметры payload

| Параметр | Назначение |
|---|---|
| `sys` | Идентификатор интеграции (фаза SYS). Примеры боевых: `moysklad`, `yclients`, `retailcrm`, `wordpress-woo`, `bitrix24payment` |
| `order_id` | Номер заказа интеграции. Паттерн: самоописывающий `{тип}:{id}` или детерминированный hash — см. `architecture-patterns.md` |
| `order_sum` | Сумма без номенклатуры (или свободная сумма — ссылка вовсе без products) |
| `products[i][name/price/quantity]` | Номенклатура; деньги — строки с точкой; name ≤ 128 символов |
| `products[i][sku]`, `products[i][type]` | Артикул и тип (`goods` / `service` / `good`) — недокументированы, но живут в проде |
| `customer_phone`, `customer_email` | Покупатель (телефон — `+7…`) |
| `customer_extra` | Произвольная сквозная строка — вернётся в webhook (боевой приём: метка `b24deal:<id>`) |
| `urlNotification` | Куда придёт webhook. Query-string сохраняется — зашей свой ID вторым каналом: `...?order_id={id}` |
| `urlSuccess`, `urlReturn` | Возврат браузера (успех / отмена) |
| `demo_mode=1` | Тестовый режим |
| `payment_method` | Предвыбор метода |
| `available_payment_methods` | Коды методов через `\|`: `AC`, `SBP`, `sbol`, `card`, `ACeuruk`, `ACkz`, `installment`, `installment_0_0_3/6`, `invoice`, `PC`, `QW` |
| `available_payment_method_groups` | Группы через `\|`: `ru_payments`, `world_payments`, `bank`, `ru_recurring`, `others`, `ru_installment_1.5…36_months` |
| `installments_disabled=1` | Отключить рассрочку |
| `discount_value` | Скидка |
| `link_expired` | Срок действия ссылки (`Y-m-d H:i`, без TZ — Москва) |
| `payments_limit` | Лимит числа оплат по ссылке |
| `npd_income_type` и `paid_content` | См. живую документацию при необходимости |
| `subscription`, `subscription_limit_autopayments`, `subscription_date_start` | Подписки, см. ниже |
| `_param_*`, `utm_*` | Сквозные параметры — вернутся в webhook как есть |
| `signature` | Подпись (обязательна для do=pay) |

## Подписки (автоплатежи)

- В ссылке: `subscription={id подписного листа}` (перекрывает `products`),
  `subscription_limit_autopayments`, `subscription_date_start`
  (`Y-m-d H:i:s`). Для подписочной ссылки `order_sum=0` допустим — сумму
  диктует план.
- Отмена: `POST https://{payform}/rest/setActivity/` с полями `subscription`,
  `customer_email` (или `tg_user_id`), `active_user=0` / `active_manager=0`,
  `signature` (доменный ключ). Ответ `400 subscriptions not found` при
  валидной подписи означает «подпись верна, подписка не найдена».
- В webhook блок `subscription[…]`: ключевая семантика —
  `subscription[id]` это ТАРИФ (общий для всех покупателей!),
  `subscription[profile_id]` — подписка конкретного клиента; маршрутизируй
  только по `profile_id`. Ключ идемпотентности: `profile_id + payment_num`.
- Жизненный цикл по полям webhook: первый платёж (`payment_num=1`),
  рекуррент успех/отказ, деактивация (`active_user=0 || active_manager=0`),
  завершение (`date_completion != ''`).
- Прочее управление подпиской (официальный REST): скидка на следующие
  списания — `POST /rest/setSubscriptionDiscount/` (`discount_value`,
  опционально `num` платежей), перенос даты списания —
  `POST /rest/setSubscriptionPaymentDate/` (`date` в `Y-m-d H:i`).
- Методов чтения подписчиков/подписок в официальном API нет — данные о
  подписчиках интеграция получает только из webhook.

## 54-ФЗ (фискализация)

Чеки формирует Prodamus, номенклатуру передаёт интеграция. Осознанно решай
`tax`, `payment_object`, `payment_method` (для предоплаты —
`full_prepayment`). Боевые паттерны: доставка — отдельная позиция с
`payment_object='service'`; если позиций нет, а сумма есть — синтетическая
позиция «Оплата заказа N»; перед отправкой сверяй `sum == Σ(price×qty)`
точной арифметикой (bcmath/decimal). Ссылка на чек возвращается в webhook
(`receipt_url`) — покажи её клиенту или запиши в CRM.

## Служебные REST-эндпоинты

- Валидация ключа: `GET https://{payform}/rest/validateSecretKey?secret_key={rawurlencode(md5(secret))}`
  → `{"success": true}`; таймаут 10 c; успех = HTTP ok И `success === true`.
  Вызывай синхронно при вводе реквизитов; при провале настройки не сохранять.
- Маркировка: `POST https://{payform}/rest/mark/addMarks/`,
  заголовок `Authorization: Bearer base64(timestamp . md5(secret))`.
- Подписки: `POST https://{payform}/rest/setActivity/`,
  `POST .../rest/setSubscriptionDiscount/`,
  `POST .../rest/setSubscriptionPaymentDate/` (см. выше).

## Webhook об оплате

`POST` на `urlNotification`; Content-Type бывает и `form-urlencoded`,
и `multipart/form-data` — парсер должен принимать оба.

### Подпись

- Подпись — в HTTP-заголовке `Sign` (hex-64; в PHP читается как
  `HTTP_SIGN`). В теле полей подписи обычно нет; перед verify всё равно
  удаляй `signature`, `sign`, `_payform_sign` — перестраховка.
- **Каким ключом подписано — зависит от sys** (prod-факт, критично):
  webhook по платежам с выданным интеграции `sys` может подписываться
  СЕРВИСНЫМ ключом (выдаётся вместе с sys), а не доменным secret_key
  payform. Предусмотри отдельную настройку `WEBHOOK_SECRET` с фолбэком на
  доменный ключ. Подпись не сходится → первым делом меняй ключ, а не
  алгоритм.
- Мультитенантность: тенанта нужно найти ДО проверки подписи. Стандарт —
  секретный токен в пути webhook-URL: `/webhook/prodamus/{random48}`
  (см. `architecture-patterns.md`).

### Поля тела (эталон по боевым фикстурам)

| Поле | Смысл |
|---|---|
| `date` | Время оплаты, ISO 8601 с `+03:00` |
| `order_id` | ВНУТРЕННИЙ номер Prodamus |
| `order_num` | Эхо твоего order_id (маппься по нему!) |
| `domain` | Домен payform |
| `sum` | Сумма, строка `1000.00` (fallback: `amount`) |
| `currency` | `rub` (нижний регистр) |
| `customer_phone`, `customer_email`, `customer_extra` | Эхо покупателя и сквозной строки |
| `payment_type` | Человекочитаемая строка метода («Visa/MasterCard/МИР, RUB») |
| `commission`, `commission_sum` | Комиссия (%, сумма) |
| `attempt` | Счётчик попыток доставки этого webhook |
| `callbackType` | Напр. `json` |
| `link_expired` | `Y-m-d H:i` без TZ (Москва) |
| `payment_status` | См. ниже |
| `payment_status_description` | Текстовое описание |
| `payment_init` | `api` / `auto` (рекуррент) / `manual` |
| `products[i][name/price/quantity/sum]` | Номенклатура (+`sum` позиции) |
| `receipt_url` (fallback `link_to_receipt`) | Ссылка на чек 54-ФЗ |
| `is_test` | `1` — тестовый платёж: в prod ответь 200 и НЕ обрабатывай |
| `subscription[…]` | Блок подписки (см. «Подписки») |

Названия товаров приходят с HTML-сущностями (`&quot;`) — декодируй только
при использовании (матчинг/вывод), сырой payload не трогай: по нему подпись.

### payment_status

- `success` — оплата прошла.
- `order_canceled` — отменил покупатель; `order_denied` — отказ банка
  (рассрочка/BNPL). Реакция — продуктовое решение: перевести заказ в
  «не оплачен/ошибка» (так делают плагины) или игнорировать.
- Неизвестное значение → подпись всё равно проверить → ответить 200 +
  WARN-лог + статус `skipped` (НЕ 400 — иначе бесконечные ретраи).

### Возвраты (refund)

Отдельное refund-событие в webhook НЕ подтверждено ни одной боевой
интеграцией; формат и Refund API — открытый вопрос (уточняй в поддержке
Prodamus: MAX https://max.ru/id1215156909_2_bot или ВКонтакте https://vk.ru/prodamuspay). Проектируй forward-compatible no-op: неизвестный
статус логируется и подтверждается 200. Если планируешь обрабатывать смену
статусов по одному платежу — включи `payment_status` в ключ идемпотентности
(unique по одному `payment_id` проглотит второе событие).

### Ответ на webhook

- Доставлен = строго **HTTP 200** (prod-факт: даже 202 Prodamus считает
  недоставкой и ретраит). Тело — любое; рекомендация `{"message":"OK"}`,
  боевые варианты: `ok`, `{"status":"accepted"}`.
- Не-200 → Prodamus ретраит (политика не документирована; диагностируй по
  полю `attempt`). Этим можно пользоваться намеренно: «заказ не найден» →
  4xx/5xx, чтобы получить повтор, когда заказ появится.
- Ошибка подписи → 400 или 403 + запись `rejected` в журнал.

## Паттерн подтверждения оплаты

Заказ считается оплаченным только по подписанному webhook, никогда — по
возврату покупателя на urlSuccess. Боевой образец waiting page: в
success-URL — ID заказа + секретный ключ доступа (order_key) против
подбора; таймер ожидания 300 с (кламп 30–3600), опрос статуса каждые 4 с
скоупленным эндпоинтом, мгновенный redirect если уже оплачен, по таймауту —
кнопки «проверить ещё раз / вернуться».
