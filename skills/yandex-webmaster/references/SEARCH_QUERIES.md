# Поисковые запросы

## Популярные запросы

```bash
bash scripts/popular_queries.sh --host example.com --order-by TOTAL_CLICKS --limit 100
```

Возвращает топ-3000 запросов за последнюю неделю (макс. 500 за запрос).

Индикаторы:
- `TOTAL_SHOWS` — показы в выдаче
- `TOTAL_CLICKS` — клики
- `AVG_SHOW_POSITION` — средняя позиция показа
- `AVG_CLICK_POSITION` — средняя позиция клика

Фильтр по устройствам: `ALL`, `DESKTOP`, `MOBILE_AND_TABLET`, `MOBILE`, `TABLET`.

## История запросов

> По умолчанию запрашиваются последние 90 дней. Для другого диапазона укажите `--date-from` явно.

### Агрегат по всем запросам

```bash
bash scripts/queries_history.sh --host example.com --date-from 2025-03-01 --date-to 2025-03-15
```

### Конкретный запрос

```bash
bash scripts/queries_history.sh --host example.com --query-id <id> --date-from 2025-03-01
```

`query_id` берётся из вывода `popular_queries.sh`.

По умолчанию возвращает данные за последние 7 дней.

## Query Analytics (расширенная аналитика)

POST-endpoint с фильтрами. Данные за последние 14 дней (фиксированный период).

```bash
bash scripts/query_analytics.sh --host example.com \
    --text-indicator QUERY \
    --filter-text "купить" \
    --filter-impressions ">100" \
    --filter-position "<10" \
    --device MOBILE \
    --limit 50
```

### Типы фильтров

**Текстовые** (по `--filter-text`):
- `TEXT_CONTAINS` (по умолчанию)
- `TEXT_MATCH` — точное совпадение
- `TEXT_DOES_NOT_CONTAIN` — исключение

**Статистические** (формат: `">значение"`, `"<значение"`, `">=значение"`):
- `IMPRESSIONS` — показы
- `CLICKS` — клики
- `POSITION` — позиция
- `CTR` — кликабельность
- `DEMAND` — спрос

### text_indicator

- `QUERY` — группировка по поисковым запросам
- `URL` — группировка по URL-адресам страниц

### search_location

- `WEB_LOCATION` — обычный поиск (по умолчанию)
- `ALL_LOCATIONS` — все типы поиска
- `ALL_LOCATIONS_ORGANIC` — только органика
- `DYNAMIC_LOCATION_ALL` — все динамические блоки
- `DYNAMIC_LOCATION_BASIC` — основные динамические
- `DYNAMIC_LOCATION_ADDITIONAL` — дополнительные динамические

### Регионы

Для фильтрации по региону используйте `--region-ids`. ID регионов можно получить:

```bash
bash scripts/regions.sh --host example.com --filter "москва"
```

### Лимиты

- 10 000 запросов/час на домен
- Макс. 500 результатов за запрос
- Данные доступны за последние 14 дней

## API endpoints

| Метод | Endpoint |
|-------|----------|
| GET | `/v4/user/{uid}/hosts/{hid}/search-queries/popular` |
| GET | `/v4/user/{uid}/hosts/{hid}/search-queries/all/history` |
| GET | `/v4/user/{uid}/hosts/{hid}/search-queries/{qid}/history` |
| POST | `/v4/user/{uid}/hosts/{hid}/query-analytics/list` |
