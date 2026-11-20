# Наблюдаемость — Monitoring, Cloud Logging, Audit Trails

Каноническая документация:
- Monitoring — https://github.com/yandex-cloud/docs/tree/master/ru/monitoring
- Cloud Logging — https://github.com/yandex-cloud/docs/tree/master/ru/logging
- Audit Trails — https://github.com/yandex-cloud/docs/tree/master/ru/audit-trails

## Три сигнала

| Сигнал | Сервис | Для чего |
|---|---|---|
| **Метрики** | Yandex Monitoring | Числовые временные ряды; дашборды; алерты |
| **Логи** | Cloud Logging | Структурированные логи приложений и инфраструктуры; запросы и хранение |
| **Аудит** | Audit Trails | Кто что делал через API YC (плоскость управления) |

Распределённая трассировка в YC не является штатной — используй Tempo или Jaeger на машине Compute или в Managed Kubernetes.

## Monitoring

### Метрики от сервисов

Каждый сервис YC автоматически публикует метрики в Monitoring:
- `Compute` — CPU, RAM, диск, сеть по каждой машине
- `Managed-PG`, `Managed-Redis` и другие — внутренние метрики сервера
- `ALB`, `NLB` — частота запросов, коды, задержки
- `Object Storage` — объём бакетов, запросы
- `MK8s` — метрики узлов и подов

Смотреть: console.cloud.yandex/monitoring, или:

```bash
yc monitoring metric list --service compute --resource-type compute_instance
```

### Свои метрики

Отправляй из приложения через REST API. Эндпоинт: `https://monitoring.api.cloud.yandex.net/monitoring/v2/data/write`.

```bash
TOKEN=$(yc iam create-token)
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "https://monitoring.api.cloud.yandex.net/monitoring/v2/data/write?folderId=$YC_FOLDER_ID&service=custom" \
  -d '{
    "metrics": [
      {"name": "orders_completed", "labels": {"env": "prod"}, "type": "COUNTER", "value": 142}
    ]
  }'
```

Есть клиенты SDK для Node, Python и Go.

### Алерты

```bash
yc monitoring alert create \
  --name prod-pg-cpu-high \
  --query 'cpu_utilization{folderId="...", host="c-XXX-pg-1"} > 80' \
  --window 5m \
  --notification-channel-ids ...
```

Каналы оповещений: email, SMS, Telegram, вебхук.

## Cloud Logging

### Группы логов

**Группа логов** — именованное хранилище с сроком хранения (группа по умолчанию в каталоге уже есть). Приложения пишут логи в одну или несколько групп.

```bash
yc logging group create --name app-logs --retention-period 168h
```

Хранение: от 1 часа до 31 дня (бесплатно) или до 1 года (платно).

### Запись логов

Четыре пути:

1. **Агент Cloud Logging (`yc-logging-agent`)**: ставится на машину Compute; читает файлы и journald; отправляет в группу логов. Рекомендуется для приложений на машинах.
2. **Fluent Bit или OTel Collector**: то же самое, но свой агент. Используй существующую инфраструктуру, если она есть.
3. **Прямой API**: `POST https://ingester.logging.yandexcloud.net/logging/v1/write` с пакетом `{ timestamp, level, message, json_payload }`. Используй из функций и контейнеров (агента там нет).
4. **Kubernetes — Cloud Logging Operator**: ставится чартом Helm; собирает stdout подов.

### Запросы

В веб-консоли YC есть язык запросов, похожий на Loki LogQL — фильтр по группе и меткам, полнотекстовый поиск, регулярные выражения.

```
resource_type="serverless.functions.function" AND
resource_id="d4e..." AND
level >= "WARN"
```

CLI:

```bash
yc logging read \
  --group-name app-logs \
  --filter 'level="ERROR" AND json_payload.user_id="42"' \
  --since 1h
```

### Что логировать

Всегда логируй:
- Идентификатор запроса и трассировки для корреляции
- Идентификатор пользователя для атрибуции действия (но не содержимое персональных данных)
- Исходящие вызовы API с длительностью и статусом

Никогда не логируй:
- Токены, API-ключи, JWT
- Полные тела запросов (могут содержать данные карт и пароли)
- Персональные данные, если они не вычищены у источника

## Audit Trails

Аудит плоскости управления (кто вызывал `yc * create`, `update`, `delete`):

```bash
# Настройка маршрута аудита (разово): собирает события и отправляет в Cloud Logging или Object Storage
yc audit-trails trail create \
  --name prod-trail \
  --logging-destination-log-group-id $(yc logging group get audit-logs --format value) \
  --filtering-policy management-events-filter='resource-scopes=[{type=resource-manager.folder,id='$YC_FOLDER_ID'}]'
```

События аудита ищи в Cloud Logging по `event_source`, `event_type`, `authentication.user_id`, `request_metadata.user_agent`.

**Всегда включай аудит для продакшен-каталогов.** Иначе нельзя выяснить, «кто удалил этот бакет».

## Дисциплина затрат

| Ловушка | Влияние на счёт |
|---|---|
| Хранение по умолчанию без срока | Логи накапливаются, счёт растёт линейно |
| Логирование тела каждого запроса | Взрыв объёма и утечки |
| Своя метрика на пользователя (высокая кардинальность) | Тарификация за серию наказывает за это |
| Аудит на слишком широкую область | Многословные события |

Настраивай срок хранения по каждой группе; сэмплируй шумные info-логи; агрегируй метрики по классам, а не по отдельным идентификаторам.

## Смежные темы

- Найти аномалию и причину → навык `systematic-debugging`
- Понять, кто сломал продакшен → раздел про Audit Trails выше
