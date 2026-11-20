# Добавление и верификация сайтов

## Добавление сайта

```bash
bash scripts/add_site.sh --url https://example.com
```

API создаёт запись и возвращает `host_id` (формат: `http:example.com:80`). После добавления сайт не верифицирован — данные недоступны до прохождения верификации.

Лимит: 1703 сайта на аккаунт.

## Верификация

### Шаг 1: Получить код верификации

```bash
bash scripts/verify.sh --host example.com --action get
```

Вернёт `verification_uin` (код) и доступные методы.

### Шаг 2: Разместить подтверждение

Три метода:

| Метод | Что делать |
|-------|-----------|
| `DNS` | Добавить TXT-запись: `yandex-verification: <код>` |
| `HTML_FILE` | Создать файл `yandex_<код>.html` в корне сайта |
| `META_TAG` | Добавить `<meta name="yandex-verification" content="<код>" />` в `<head>` |

### Шаг 3: Запустить проверку

```bash
bash scripts/verify.sh --host example.com --action start --method DNS
```

Возможные состояния:
- `VERIFIED` — сайт подтверждён
- `IN_PROGRESS` — проверка идёт
- `VERIFICATION_FAILED` — запись не найдена
- `INTERNAL_ERROR` — ошибка на стороне Яндекса

При `VERIFICATION_FAILED` проверьте, что DNS-запись распространилась (DNS propagation может занять до 72 часов).

## Владельцы сайта

```bash
bash scripts/host_info.sh --host example.com
```

Показывает всех владельцев с типом верификации и датой.

## Информация о сайте

Поле `host_data_status`:
- `OK` — данные загружены, всё доступно
- `NOT_LOADED` — данные ещё загружаются
- `NOT_INDEXED` — сайт не проиндексирован

## API endpoints

| Метод | Endpoint |
|-------|----------|
| POST | `/v4/user/{uid}/hosts` — добавить сайт |
| GET | `/v4/user/{uid}/hosts/{hid}` — инфо о сайте |
| GET | `/v4/user/{uid}/hosts/{hid}/verification` — код верификации |
| POST | `/v4/user/{uid}/hosts/{hid}/verification?verification_type=DNS` — начать проверку |
| GET | `/v4/user/{uid}/hosts/{hid}/owners` — владельцы |
