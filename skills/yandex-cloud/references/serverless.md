# Serverless — функции, контейнеры, API Gateway, триггеры, очередь, YDB

Каноническая документация:
- Cloud Functions — https://github.com/yandex-cloud/docs/tree/master/ru/functions
- Serverless Containers — https://github.com/yandex-cloud/docs/tree/master/ru/serverless-containers
- API Gateway — https://github.com/yandex-cloud/docs/tree/master/ru/api-gateway
- Message Queue — https://github.com/yandex-cloud/docs/tree/master/ru/message-queue
- YDB — https://github.com/yandex-cloud/docs/tree/master/ru/ydb

## Cloud Functions

Функции без состояния. Среды выполнения: Node.js 22, Python 3.12, Go 1.23, Java 21, .NET 8, PHP 8.3, Bash, своя сборка на Docker.

```bash
# Сборка и развёртывание
zip -r fn.zip index.js package.json

yc serverless function create --name api-fn
yc serverless function version create \
  --function-name api-fn \
  --runtime nodejs22 \
  --entrypoint index.handler \
  --memory 128m --execution-timeout 10s \
  --source-path fn.zip \
  --service-account-name fn-sa \
  --environment NODE_ENV=production,LOCKBOX_SECRET_ID=$(yc lockbox secret get app --format value --jq .id)
```

Лимиты на вызов: 4 ГБ RAM, 15 минут работы, 25 МБ полезной нагрузки.

Холодный старт: около 100–500 мс для Node и Python, дольше для JVM. Если важна задержка, используй **подготовленные экземпляры** или переходи на Serverless Containers с `min-instances`.

## Serverless Containers

Та же модель, но ты приносишь образ OCI; лучше подходит для тяжёлых зависимостей и сред выполнения вне списка.

```bash
yc serverless container create --name app-svc
yc serverless container revision deploy \
  --container-name app-svc \
  --image cr.yandex/$REG/app:v1 \
  --memory 512m --cores 1 --concurrency 16 \
  --execution-timeout 30s \
  --service-account-name fn-sa \
  --min-instances 1                     # убирает холодный старт
```

Контейнер должен слушать `$PORT` (по умолчанию 8080) и отвечать по HTTP. Проверка здоровья необязательна.

## API Gateway на основе OpenAPI

Направляет HTTP-запросы в функции, контейнеры, Object Storage или внешние адреса по одной спецификации OpenAPI:

```yaml
openapi: 3.0.0
info: { title: api, version: 1.0.0 }
paths:
  /users/{id}:
    get:
      parameters: [{ name: id, in: path, required: true, schema: { type: string } }]
      x-yc-apigateway-integration:
        type: cloud_functions
        function_id: d4e...
        service_account_id: aje...
```

```bash
# Создай шлюз по спецификации
yc serverless api-gateway create --name api-gw --spec spec.yaml
# Вернёт домен по умолчанию вида d5d...apigw.yandexcloud.net
```

Для своего домена привяжи сертификат из Certificate Manager → публичный HTTPS.

## Message Queue (совместима с SQS)

Замена SQS без переделки кода. Используй `aws-sdk` с `endpoint: https://message-queue.api.cloud.yandex.net`. Авторизация — статические ключи сервисного аккаунта в стиле S3.

```bash
yc message-queue queue create --name jobs.fifo --is-fifo --content-based-deduplication
```

Таймаут видимости, очереди недоставленных сообщений, порядок FIFO, пакетная отправка и приём — всё как в SQS.

## Триггеры (вызов по событию)

Связывают события с функциями, контейнерами и очередями:

| Источник | Примеры |
|---|---|
| `yc serverless trigger create timer` | Расписание в стиле cron |
| `yc serverless trigger create message-queue` | Опустошение очереди в функцию |
| `yc serverless trigger create iot-message` | Сообщение IoT Core → функция |
| `yc serverless trigger create object-storage` | ObjectCreated в S3 → функция |
| `yc serverless trigger create logging` | Новая запись в группе Cloud Logging → функция |
| `yc serverless trigger create cloud-logs` | Событие Audit Trails → функция |
| `yc serverless trigger create container-registry` | Загружен новый образ → функция |
| `yc serverless trigger create yds` | Запись Yandex Data Streams → функция |

## YDB (Yandex Database)

Два режима:
- **Serverless**: оплата за RU/с и хранение; автомасштабирование; подходит для переменной нагрузки
- **Выделенный**: арендованные узлы; предсказуемая стоимость

Строго согласованная, распределённая, поддерживает SQL (подмножество ANSI) и ключ-значение. Драйверы: Node, Python, Go, Java, .NET.

```bash
yc ydb database create --name app-db --serverless
# Получить эндпоинт подключения
yc ydb database get app-db --format json --jq .endpoint
```

Подходит для: хранилища сессий, журнала событий, метаданных. Не подходит для: сложных JOIN (бери Managed PG), полнотекстового поиска (бери OpenSearch).

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| Функция упирается в таймаут на первом вызове после деплоя | Холодный старт и инициализация зависимостей | Больше памяти (быстрее CPU), `min-instances` или более лёгкие зависимости |
| Функция не читает Object Storage | У сервисного аккаунта нет `storage.viewer` | Добавь привязку |
| API Gateway отдаёт 401 на каждый запрос | Авторизация по умолчанию блокирует неавторизованные запросы | Добавь `x-yc-apigateway-authorizer: { type: none }` в операцию ИЛИ передавай JWT |
| Сообщения из Message Queue пропадают | Таймаут видимости меньше времени обработки | Увеличь видимость или используй FIFO с дедупликацией |
| Запрос YDB медленный | Нет сканирования по префиксу первичного ключа | Проектируй ключ под шаблон доступа; YDB упорядочена по ключу |
| Триггер не срабатывает | У сервисного аккаунта нет роли на источник (например, `storage.viewer` для триггера S3) | Добавь привязку |

## Смежные темы

- Функция или контейнер берёт секреты из Lockbox → `secrets-lockbox.md`
- Домен API Gateway через сертификат → `load-balancer.md`
- Логи функций идут в Cloud Logging → `observability.md`
