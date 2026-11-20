# Внешние ссылки

> По умолчанию history запрашивает последние 90 дней. Для полной истории укажите `--date-from` явно.

## Сэмплы внешних ссылок

```bash
bash scripts/external_links.sh --host example.com --action samples --limit 30
```

Каждая запись: URL-источник (внешний сайт), URL-назначение (ваш сайт), дата обнаружения.

## История количества внешних ссылок

```bash
bash scripts/external_links.sh --host example.com --action history --date-from 2025-03-01
```

Единственный доступный индикатор: `LINKS_TOTAL_COUNT`.

## Анализ ссылочного профиля

Рекомендуемый сценарий:
1. Получить сэмплы для понимания источников
2. Проверить историю на аномалии (резкий рост/падение)
3. Сопоставить с SQI историей (`sqi_history.sh`) для корреляции

## API endpoints

| Метод | Endpoint |
|-------|----------|
| GET | `/v4/user/{uid}/hosts/{hid}/links/external/samples` |
| GET | `/v4/user/{uid}/hosts/{hid}/links/external/history` |

Требуется OAuth scope: `webmaster:hostinfo`.
