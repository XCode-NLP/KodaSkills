---
name: yandex-cloud
description: "Работа с Яндекс Облаком в продакшене: `yc` CLI, Compute Cloud, Managed PostgreSQL, MySQL, Redis, ClickHouse, MongoDB, Kafka, Object Storage, VPC, Managed Kubernetes, IAM, Lockbox, Cloud Functions, балансировщики, Container Registry, Cloud DNS и мониторинг. Используй при создании инфраструктуры и работе с нагрузкой в Яндекс Облаке, настройке профилей и федераций, сервисных аккаунтов, групп безопасности, секретов, автоскейлинга и миграции с самостоятельного хостинга на управляемые сервисы."
license: MIT
metadata:
  author: VKirill
  source: https://github.com/VKirill/claude-lane-stack
---

## 🎯 Требования к версиям (май 2026)

**Канонические источники:**
- **Репозиторий документации**: https://github.com/yandex-cloud/docs (markdown-источник для yandex.cloud/ru/docs)
- **Публичное зеркало**: https://yandex.cloud/ru/docs · https://yandex.cloud/en/docs
- **`yc` CLI**: последняя стабильная версия из https://storage.yandexcloud.net/yandexcloud-yc/install.sh (rolling release)
- **Провайдер Terraform**: `yandex-cloud/yandex` v0.115.x+
- **Эндпоинт S3**: `https://storage.yandexcloud.net` (подпись S3 v4)
- **gRPC-эндпоинт Cloud API**: `*.api.cloud.yandex.net:443`

**Версии управляемых сервисов (май 2026):**
- Managed PostgreSQL: 14/15/16/**17** (по умолчанию для новых кластеров)
- Managed MySQL: 5.7/8.0/**8.4**
- Managed Redis: 6.2/7.0/**7.2**
- Managed ClickHouse: последняя LTS
- Managed Kubernetes: 1.27 → **1.31** (по умолчанию)
- Managed Kafka: 3.x

**Всегда уточняй закреплённые версии через** `yc managed-postgresql cluster list-hosts` и подобные команды — никогда не предполагай.

## Как пользоваться навыком

Навык загружается автоматически, когда его описание совпадает с текущей задачей. Читай только нужный раздел справочника — полная документация живёт в каноническом репозитории выше (этот навык — навигатор, а не копия).

## Когда использовать

- Создание, миграция и эксплуатация нагрузок в **Яндекс Облаке**
- Работа с `yc` CLI: профили, федерации, сервисные аккаунты, IAM-токены
- Настройка Managed Service for PostgreSQL, MySQL, Redis, ClickHouse, MongoDB, Kafka, Greenplum
- Object Storage: политика бакетов, жизненный цикл, presigned-ссылки, CORS
- Проектирование VPC: каталоги и облака, сети, подсети, группы безопасности, NAT-шлюзы, пиринг
- Managed Service for Kubernetes: группы узлов, автоскейлинг, сетевые политики, ALB Ingress
- Проектирование IAM: сервисные аккаунты, роли, федерации SAML и OIDC, OAuth-токены
- Хранение учётных данных в Lockbox и выдача секретов машинам, Kubernetes и serverless через метаданные
- Cloud Functions, Serverless Containers, API Gateway, триггеры
- Оптимизация затрат, оповещения по биллингу, скидки за обязательства
- Миграция с самостоятельного хостинга (Ubuntu, PostgreSQL и Redis на одной машине) на управляемые сервисы YC

## Когда не использовать

- Целевое облако — AWS, GCP, Azure, DigitalOcean или Hetzner: бери подходящий навык
- Задача — код приложения, который просто работает в YC: бери навык по фреймворку (`nodejs`, `fastapi` и т. п.)
- Задача только про использование `aws-sdk` против Object Storage YC: бери навык по SDK и считай YC обычным S3-эндпоинтом
- Задача — самостоятельно администрируемый PostgreSQL или Redis на машине Compute Cloud: бери `postgresql`, `redis`, `linux-sysadmin` (этот навык про управляемые сервисы)

## Назначение

Навык — это **карта работы** с Яндекс Облаком: к какой поверхности обращаться, какие канонические команды управления (`yc ...`) использовать и куда смотреть в документации https://github.com/yandex-cloud/docs. Он намеренно НЕ дублирует документацию — он направляет агента к нужному справочнику и к нужному вызову `yc`.

Навык не покрывает логику приложений, языковые SDK (это к навыку по языку) и другие облака. Для сырой семантики протокола S3 обращайся к документации S3; здесь только особенности YC.

## Рабочие правила

1. **Всегда уточняй каталог и облако** перед любой разрушительной командой `yc` — `yc config list` и `yc config get folder-id`
2. **Сначала `--dry-run` или `--format yaml`** для любых `yc * create`, `update`, `delete` — предпросмотр до изменения
3. **Сервисные аккаунты лучше OAuth-токенов** для автоматизации: никогда не вшивай `--token <OAuth>` в скрипты, используй сервисный аккаунт и `iam create-token`
4. **Удаление в продакшене требует подтверждения** — `yc compute instance delete`, `yc managed-* cluster delete`, `yc storage bucket remove` необратимы; спроси перед запуском
5. **Резервные копии до обновления схемы и версии** — `yc managed-postgresql backup list` и создание копии по требованию перед любым `cluster update --postgresql-version`
6. **Сетевые изменения вне окна обслуживания дают простой** — правки групп безопасности и перенос подсетей; делай в согласованное окно
7. **Читай репозиторий документации, а не устаревшую память** — пути в https://github.com/yandex-cloud/docs/tree/master/ru меняются; сверяйся перед цитированием

## Карта сервисов

| Слой | Сервис | Пространство `yc` | Путь в `yandex-cloud/docs` |
|---|---|---|---|
| **IaaS: вычисления** | Compute Cloud | `yc compute` | `ru/compute/` |
| **IaaS: сеть** | Virtual Private Cloud | `yc vpc` | `ru/vpc/` |
| **PaaS: БД** | Managed PostgreSQL | `yc managed-postgresql` | `ru/managed-postgresql/` |
| **PaaS: БД** | Managed MySQL | `yc managed-mysql` | `ru/managed-mysql/` |
| **PaaS: БД** | Managed Redis | `yc managed-redis` | `ru/managed-redis/` |
| **PaaS: БД** | Managed ClickHouse | `yc managed-clickhouse` | `ru/managed-clickhouse/` |
| **PaaS: БД** | Managed MongoDB | `yc managed-mongodb` | `ru/managed-mongodb/` |
| **PaaS: БД** | Managed Kafka | `yc managed-kafka` | `ru/managed-kafka/` |
| **PaaS: БД** | Managed Greenplum | `yc managed-greenplum` | `ru/managed-greenplum/` |
| **PaaS: БД** | Managed OpenSearch | `yc managed-opensearch` | `ru/managed-opensearch/` |
| **Serverless** | YDB (Document и Distributed) | `yc ydb` | `ru/ydb/` |
| **Serverless** | Cloud Functions | `yc serverless function` | `ru/functions/` |
| **Serverless** | Serverless Containers | `yc serverless container` | `ru/serverless-containers/` |
| **Serverless** | API Gateway | `yc serverless api-gateway` | `ru/api-gateway/` |
| **Serverless** | Message Queue (совместим с SQS) | `yc message-queue` | `ru/message-queue/` |
| **Хранилище** | Object Storage (S3) | `yc storage` | `ru/storage/` |
| **K8s** | Managed Kubernetes | `yc managed-kubernetes` | `ru/managed-kubernetes/` |
| **Реестр** | Container Registry | `yc container registry` | `ru/container-registry/` |
| **Балансировка** | Application LB (L7) | `yc alb` | `ru/application-load-balancer/` |
| **Балансировка** | Network LB (L4) | `yc load-balancer` | `ru/network-load-balancer/` |
| **DNS** | Cloud DNS | `yc dns` | `ru/dns/` |
| **CDN** | CDN | `yc cdn` | `ru/cdn/` |
| **IAM** | IAM | `yc iam` | `ru/iam/` |
| **Секреты** | Lockbox | `yc lockbox` | `ru/lockbox/` |
| **Секреты** | KMS | `yc kms` | `ru/kms/` |
| **Наблюдаемость** | Monitoring | `yc monitoring` | `ru/monitoring/` |
| **Наблюдаемость** | Cloud Logging | `yc logging` | `ru/logging/` |
| **Аудит** | Audit Trails | `yc audit-trails` | `ru/audit-trails/` |
| **Резервные копии** | Cloud Backup | `yc backup` | `ru/backup/` |
| **Организация** | Organization Manager | `yc organization-manager` | `ru/organization/` |

## Форма ответа

Три раздела в каждом операционном ответе:

- **План**: какие вызовы `yc` и в каком порядке будут выполнены
- **Что сделано**: маркированный список выполненных действий (с выводом `yc`)
- **Текущее состояние**: вывод проверочной команды (например, `yc compute instance get`)
- **Откат**: как отменить изменения, если применимо (например, снимок и `yc compute instance create` из снимка)

## Справочники

Справочники по областям — загружай только нужное. **Весь глубокий материал живёт в https://github.com/yandex-cloud/docs** — эти файлы обобщают специфику YC и указывают канонические пути.

| Тема | Файл |
|---|---|
| `yc` CLI — установка, профили, федерации, авторизация сервисного аккаунта, скрипты | [references/yc-cli.md](references/yc-cli.md) |
| Compute Cloud — машины, диски, снимки, группы размещения, прерываемые машины, GPU | [references/compute.md](references/compute.md) |
| Управляемые базы — PG, MySQL, Redis, ClickHouse, MongoDB, Kafka, Greenplum, OpenSearch | [references/managed-databases.md](references/managed-databases.md) |
| Object Storage — особенности S3-эндпоинта, политика бакета, жизненный цикл, presigned-ссылки, статический хостинг | [references/object-storage.md](references/object-storage.md) |
| VPC — иерархия каталогов и облаков, сети, подсети, группы безопасности, NAT-шлюз, пиринг, VPN | [references/vpc-network.md](references/vpc-network.md) |
| IAM и авторизация — сервисные аккаунты, роли, OAuth, федерации, жизненный цикл IAM-токена, примитивные и пользовательские роли | [references/iam-auth.md](references/iam-auth.md) |
| Managed Kubernetes — кластер и группы узлов, автоскейлинг, ALB Ingress, сетевые политики, загрузка из Container Registry | [references/kubernetes.md](references/kubernetes.md) |
| Балансировщики — ALB (L7, HTTP/2, gRPC) против NLB (L4, внешний и внутренний), группы бэкендов, проверки здоровья | [references/load-balancer.md](references/load-balancer.md) |
| Serverless — Cloud Functions, Serverless Containers, API Gateway, триггеры, Message Queue, serverless YDB | [references/serverless.md](references/serverless.md) |
| Lockbox и KMS — содержимое секретов, версии, доступ по IAM, монтирование в машины, Kubernetes и serverless | [references/secrets-lockbox.md](references/secrets-lockbox.md) |
| Наблюдаемость — Cloud Logging, пользовательские метрики Monitoring, Audit Trails, группы логов, язык запросов | [references/observability.md](references/observability.md) |
| Миграция — с самостоятельного хостинга (Ubuntu, PG и Redis на машине Compute) на управляемые сервисы | [references/migration.md](references/migration.md) |

**Как пользоваться**: ищешь параметр `yc compute instance create` → `compute.md` и каноническая документация. Проектируешь модель IAM для нового проекта → `iam-auth.md`. Выбираешь между ALB и NLB → `load-balancer.md`. Переносишь продакшен-PG на управляемый → `migration.md`.
