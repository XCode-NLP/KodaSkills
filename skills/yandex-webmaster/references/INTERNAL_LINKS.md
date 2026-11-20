# Битые внутренние ссылки

> По умолчанию history запрашивает последние 90 дней. Для полной истории укажите `--date-from` явно.

## Сэмплы битых ссылок

```bash
bash scripts/internal_links.sh --host example.com --action samples --limit 30
```

Фильтр по типу проблемы:

```bash
bash scripts/internal_links.sh --host example.com --action samples --indicator SITE_ERROR
```

Типы индикаторов:
- `SITE_ERROR` — ошибки сайта (404, 500 и т.д.)
- `DISALLOWED_BY_USER` — заблокированы пользователем (robots.txt, nofollow)
- `UNSUPPORTED_BY_ROBOT` — не поддерживается роботом

Каждая запись содержит: URL-источник, URL-назначение, дату обнаружения.

## История битых ссылок

```bash
bash scripts/internal_links.sh --host example.com --action history --date-from 2025-03-01
```

Разбивка по всем трём индикаторам за каждую дату.

## Рекомендации по исправлению

1. `SITE_ERROR` — проверить, что целевые страницы доступны (не 404/500)
2. `DISALLOWED_BY_USER` — убрать из robots.txt или убрать ссылки на заблокированные страницы
3. `UNSUPPORTED_BY_ROBOT` — проверить формат ссылок (JavaScript, фреймы)

## API endpoints

| Метод | Endpoint |
|-------|----------|
| GET | `/v4/user/{uid}/hosts/{hid}/links/internal/broken/samples` |
| GET | `/v4/user/{uid}/hosts/{hid}/links/internal/broken/history` |

Требуется OAuth scope: `webmaster:hostinfo`.
