# Страницы в поиске

> По умолчанию history-скрипты запрашивают последние 90 дней. Для полной истории укажите `--date-from` явно.

## История количества страниц в поиске

```bash
bash scripts/insearch.sh --host example.com --action history --date-from 2025-03-01
```

Показывает, сколько страниц сайта находится в поисковой выдаче Яндекса на каждую дату.

## Сэмплы страниц в поиске

```bash
bash scripts/insearch.sh --host example.com --action samples --limit 50
```

Список URL, находящихся в поиске, с заголовками и датой последнего обращения. Макс. 50 000 URL через API.

## События поиска

### История появлений/исчезновений

```bash
bash scripts/search_events.sh --host example.com --action history --date-from 2025-03-01
```

Два индикатора:
- `APPEARED_IN_SEARCH` — новые страницы в поиске
- `REMOVED_FROM_SEARCH` — удалённые из поиска

### Сэмплы событий

```bash
bash scripts/search_events.sh --host example.com --action samples --limit 50
```

Для каждого URL показывает тип события, дату и причину исключения (для удалённых).

Причины исключения (`excluded_url_status`):
- `DUPLICATE` — дубликат
- `LOW_QUALITY` — низкое качество
- `REDIRECT_NOTSEARCHABLE` — редирект
- `ROBOTS_URL_ERROR` — заблокирован robots.txt
- `NO_INDEX` — noindex
- `HTTP_ERROR` — HTTP ошибка
- `HOST_ERROR` — ошибка хоста
- `NOT_CANONICAL` — не каноничный URL
- `CLEAN_PARAMS` — очистка параметров

## API endpoints

| Метод | Endpoint |
|-------|----------|
| GET | `/v4/user/{uid}/hosts/{hid}/search-urls/in-search/history` |
| GET | `/v4/user/{uid}/hosts/{hid}/search-urls/in-search/samples` |
| GET | `/v4/user/{uid}/hosts/{hid}/search-urls/events/history` |
| GET | `/v4/user/{uid}/hosts/{hid}/search-urls/events/samples` |
