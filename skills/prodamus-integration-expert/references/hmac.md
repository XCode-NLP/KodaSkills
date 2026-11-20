# Канонический HMAC Prodamus

## Две схемы подписи — не перепутай

1. **JSON-канонизация** (этот файл) — входящий webhook (заголовок `Sign`)
   и `signature` в do=pay. Эталон ниже.
2. **Query-string канонизация** — опциональный `sign` в исходящих
   подписанных URL (prod-факт retailcrm): HMAC-SHA256 от
   `http_build_query(...RFC3986)` после рекурсивного `ksort(SORT_STRING)`
   (списки-массивы не сортировать!). Интеграция, применившая её к webhook,
   сломалась — для webhook только схема 1.

**Каким КЛЮЧОМ подписан webhook** — не менее важно: по платежам с выданным
интеграции sys подпись может считаться сервисным ключом (выдаётся вместе
с sys), а не доменным secret_key (`payform-protocol.md`, раздел Webhook).
«Подпись не сходится» → сначала проверь ключ, потом алгоритм.

## Схема 1: JSON-канонизация (webhook и do=pay)

Менять алгоритм нельзя — подписи разойдутся с Prodamus.

## Алгоритм (байт-в-байт)

1. Все значения payload рекурсивно привести к строкам (`strval`).
2. Рекурсивно отсортировать массивы по ключам: `ksort($data, SORT_REGULAR)`.
3. Сериализовать: `json_encode($data, JSON_UNESCAPED_UNICODE)`.
   Важно: юникод НЕ экранируется, а слэш `/` экранируется как `\/`
   (поведение PHP по умолчанию).
4. Подпись: `hash_hmac('sha256', $json, $secret)` — hex-строка.

Проверка — регистронезависимо, но constant-time:
`hash_equals(strtolower($expected), strtolower($sign))`.
Никогда: `md5`, `sha1`, сравнение через `==`/`===` для подписей.

Перед проверкой входящего webhook удали из тела поля `signature`, `sign`,
`_payform_sign` (если есть; в реальных webhook-телах полей подписи не
наблюдалось — подпись только в заголовке, удаление — перестраховка).
Заголовок `Sign` ищи регистронезависимо (`Sign` / `sign` / `HTTP_SIGN`).

Официальный vendored-класс Prodamus из документации сравнивает подписи
через `strtolower === strtolower` — в своём коде заменяй на `hash_equals`.

## Эталон на PHP

```php
final class ProdamusHmac
{
    public static function sign(array $data, string $secret): string
    {
        $data = self::stringify($data);
        self::sortRecursive($data);
        $json = json_encode($data, JSON_UNESCAPED_UNICODE);

        return hash_hmac('sha256', $json, $secret);
    }

    public static function verify(array $data, string $secret, string $sign): bool
    {
        unset($data['signature'], $data['sign'], $data['_payform_sign']);

        return hash_equals(
            strtolower(self::sign($data, $secret)),
            strtolower($sign),
        );
    }

    private static function stringify(array $data): array
    {
        foreach ($data as $key => $value) {
            $data[$key] = is_array($value) ? self::stringify($value) : strval($value);
        }

        return $data;
    }

    private static function sortRecursive(array &$data): void
    {
        ksort($data, SORT_REGULAR);
        foreach ($data as &$value) {
            if (is_array($value)) {
                self::sortRecursive($value);
            }
        }
    }
}
```

## Эквивалент на Python

```python
import hashlib, hmac, json

def _stringify(v):
    if isinstance(v, dict):
        return {str(k): _stringify(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_stringify(x) for x in v]
    if isinstance(v, bool):
        return "1" if v else ""  # как PHP strval(true/false)
    return str(v)

def _ksort(v):
    if isinstance(v, dict):
        return {k: _ksort(v[k]) for k in sorted(v)}
    if isinstance(v, list):
        return [_ksort(x) for x in v]
    return v

def prodamus_sign(data: dict, secret: str) -> str:
    prepared = _ksort(_stringify(data))
    j = json.dumps(prepared, ensure_ascii=False, separators=(",", ":"))
    j = j.replace("/", "\\/")  # PHP json_encode экранирует слэши
    return hmac.new(secret.encode(), j.encode(), hashlib.sha256).hexdigest()

def prodamus_verify(data: dict, secret: str, sign: str) -> bool:
    clean = {k: v for k, v in data.items()
             if k not in ("signature", "sign", "_payform_sign")}
    return hmac.compare_digest(prodamus_sign(clean, secret).lower(), sign.lower())
```

## Эквивалент на Node.js

```javascript
const crypto = require('crypto');

function stringify(v) {
  if (Array.isArray(v)) return v.map(stringify);
  if (v !== null && typeof v === 'object') {
    return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, stringify(x)]));
  }
  if (typeof v === 'boolean') return v ? '1' : ''; // как PHP strval
  return String(v);
}

function ksort(v) {
  if (Array.isArray(v)) return v.map(ksort);
  if (v !== null && typeof v === 'object') {
    return Object.fromEntries(
      Object.keys(v).sort().map((k) => [k, ksort(v[k])])
    );
  }
  return v;
}

function prodamusSign(data, secret) {
  const json = JSON.stringify(ksort(stringify(data))).replace(/\//g, '\\/');
  return crypto.createHmac('sha256', secret).update(json, 'utf8').digest('hex');
}

function prodamusVerify(data, secret, sign) {
  const { signature, sign: s, _payform_sign, ...clean } = data;
  const expected = prodamusSign(clean, secret);
  const actual = String(sign).toLowerCase();
  // timingSafeEqual бросает исключение при разной длине буферов —
  // подпись другой длины должна давать false, а не HTTP 500
  if (actual.length !== expected.length) return false;
  return crypto.timingSafeEqual(
    Buffer.from(expected.toLowerCase()),
    Buffer.from(actual)
  );
}
```

## Тест-вектора

Секрет во всех векторах: `test_secret_key`.

Вектор 1 — плоский payload:

```json
{"order_id": "12345", "sum": "1000.00", "customer_email": "client@example.com", "payment_status": "success"}
```

Канонический JSON:
`{"customer_email":"client@example.com","order_id":"12345","payment_status":"success","sum":"1000.00"}`

Подпись: `a0c2f61457c981288d7687765a069d5e8db5b6998706115fb0c0de0988620609`

Вектор 2 — вложенный payload, юникод, URL:

```json
{"order_id": "order-77", "sum": "2500.50",
 "products": [{"name": "Тестовый курс «Запуск»", "price": "2500.50", "quantity": "1"}],
 "urlNotification": "https://example.com/webhook/prodamus"}
```

Канонический JSON:
`{"order_id":"order-77","products":[{"name":"Тестовый курс «Запуск»","price":"2500.50","quantity":"1"}],"sum":"2500.50","urlNotification":"https:\/\/example.com\/webhook\/prodamus"}`

Подпись: `ca54bade5070ec36f00dd966aea69bd84f5bdc89632b8f3d25c93f57340628c5`

Первый шаг фазы Build — реализовать модуль подписи на стеке пользователя и
прогнать оба вектора + негативный тест (чужой секрет → verify = false).

## Типичные причины расхождения подписи

- **Не тот ключ**: сервисный ключ по sys vs доменный secret_key — проверяй
  первым (см. начало файла).
- **Не та схема**: query-string канонизация применена к webhook
  (см. «Две схемы подписи»).
- Слэши не экранированы (`https://…` вместо `https:\/\/…`). Внимание:
  боевые реализации здесь расходятся (часть разэкранирует слэши и живёт,
  потому что в их payload слэшей нет) — канон этого файла: сохранять `\/`;
  при сомнении сними captured-фикстуру (см. ниже).
- Юникод экранирован (`Т…` вместо кириллицы) — забыт JSON_UNESCAPED_UNICODE.
- Значения не приведены к строкам (числа остались числами: `1000` вместо `"1000.00"`).
- Пробелы в JSON-разделителях (в Python не заданы `separators=(",", ":")`).
- Числовые строковые ключи: PHP `SORT_REGULAR` сортирует `"9" < "10"`,
  лексикографическая сортировка — наоборот. В реальных payload таких ключей
  нет, но при отладке помни об этом.
- Поля `signature`/`sign`/`_payform_sign` не удалены перед verify.
- `null`-значения: PHP `strval(null)` даёт пустую строку `""`, а наивные
  `str(None)`/`String(null)` — `"None"`/`"null"`. Webhook приходит
  form-urlencoded (все значения уже строки), поэтому на практике это не
  стреляет, но если собираешь payload из своих структур — приводи
  null к `""`.

## Captured-фикстура — окончательный арбитр

Синтетические вектора самосогласованы, но не ловят дрейф формата Prodamus.
При первом сквозном прогоне (фаза Verify) сними реальный webhook — сырое
тело + заголовок `Sign` — и зафиксируй регрессионным тестом: твой verify
обязан проходить на живой фикстуре. Все споры об экранировании/сортировке
решает она.
