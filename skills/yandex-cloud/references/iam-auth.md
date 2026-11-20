# IAM и авторизация

Каноническая документация: https://github.com/yandex-cloud/docs/tree/master/ru/iam · Публичная: https://yandex.cloud/ru/docs/iam/

## Иерархия

```
Организация                    ← корень, здесь живёт федерация
└── Облако(а)                   ← единица биллинга
    └── Каталог(и)              ← область IAM, квоты, большинство ресурсов
        └── Ресурсы             ← машины, бакеты, кластеры и т. д.
```

Привязки IAM можно делать на любом уровне. **Побеждает самый широкий** — `viewer` на каталоге и `editor` на ресурсе дают `editor` для этого ресурса.

## Типы идентичностей

| Тип | Для чего | Способ авторизации |
|---|---|---|
| **Федеративный пользователь** | Реальные люди через корпоративный IdP (SAML/OIDC) | Поток в браузере, `yc init --federation-id` |
| **Пользователь Яндекс Паспорта** | Личный аккаунт Яндекса (только для разработки) | OAuth через `yc init` |
| **Сервисный аккаунт** | Автоматизация, машины, CI, Kubernetes | Статический ключ (JSON) или токен сервера метаданных (на машине) |

## Роли

Два вида:

| | Примеры | Для чего |
|---|---|---|
| **Примитивные** | `viewer`, `editor`, `admin` | Быстрый старт; слишком широкие для продакшена |
| **По сервисам** | `storage.uploader`, `compute.operator`, `managed-postgresql.editor` | Продакшен — минимальные права |

Все роли: `yc iam role list | grep <service>`. Посмотреть одну: `yc iam role get storage.uploader`.

## Быстрый старт с сервисным аккаунтом

```bash
# Создать сервисный аккаунт
yc iam service-account create --name app-prod --description "Prod app SA"

# Привязать роли с минимальными правами (на уровне каталога)
yc resource-manager folder add-access-binding $YC_FOLDER_ID \
  --role storage.uploader \
  --service-account-id $(yc iam service-account get app-prod --format value)

yc resource-manager folder add-access-binding $YC_FOLDER_ID \
  --role lockbox.payloadViewer \
  --service-account-id $(yc iam service-account get app-prod --format value)

# Привязать к машине (статические ключи не нужны)
yc compute instance create --service-account-name app-prod ...

# Внутри машины:
TOKEN=$(curl -s -H 'Metadata-Flavor: Google' \
  169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token | jq -r .access_token)
# Используй $TOKEN как Bearer для *.api.cloud.yandex.net
```

Это **тот самый** рекомендуемый шаблон для машин, подов Kubernetes и serverless — никаких файлов ключей, которые можно утечь или забыть ротировать.

## Когда нужен файл ключа (нет сервера метаданных)

Для внешнего CI (GitHub Actions, GitLab Runner вне YC):

```bash
yc iam key create --service-account-name ci-runner -o ci-key.json
# ci-key.json содержит: id, service_account_id, created_at, key_algorithm, public_key, private_key (PEM)
# Используй так: yc config set service-account-key ci-key.json
```

**Ротируй раз в год.** Учёт ключей: `yc iam key list --service-account-name ci-runner`.

## OAuth-токены — ограниченное применение

Интерактивный поток `yc init` создаёт долгоживущий OAuth-токен в `~/.config/yandex-cloud/config.yaml`. Он привязан к **твоей личности пользователя**.

- ✅ Личное использование в CLI
- ❌ Никогда не вшивай в скрипты (уйдёт человек — уйдёт доступ)
- ❌ Никогда не делись между людьми
- ❌ Никогда не кладёшь в CI

## Федерация (корпоративный SSO)

Для организаций с Active Directory, Keycloak или Okta:

1. Настрой федерацию в администраторе организации YC
2. Сопоставь группы IdP с группами YC
3. Пользователи входят по SAML → получают сессию Яндекс Облака
4. `yc init --federation-id <id>` для CLI

Токены федерации истекают — `yc` сам предлагает повторить авторизацию.

## Шпаргалка по частым ролям

| Роль | Что даёт |
|---|---|
| `viewer` | Чтение всего (список ресурсов, свойства) |
| `editor` | Создание и изменение большинства ресурсов, но не IAM |
| `admin` | Включая IAM — выдавай осторожно |
| `resource-manager.viewer/editor/admin` | Управление каталогами и облаками |
| `iam.serviceAccounts.user` | Использовать сервисный аккаунт (привязать к машине); НЕ даёт его ролей |
| `iam.serviceAccounts.tokenCreator` | Выпускать IAM-токены для сервисного аккаунта |
| `compute.operator` | Запуск и остановка машин, без создания и удаления |
| `storage.uploader` | Запись объектов, без списка и удаления бакета |
| `storage.editor` | Полный доступ к бакету |
| `managed-postgresql.editor` | Управление кластером, базами и пользователями |
| `lockbox.payloadViewer` | Чтение содержимого секретов (НЕ версий и метаданных) |
| `lockbox.editor` | Полный Lockbox |
| `k8s.cluster-api.viewer/editor` | Управление кластерами Managed Kubernetes |
| `monitoring.editor` | Запись метрик и дашбордов |
| `logging.writer/reader` | Cloud Logging |
| `dns.editor` | Зоны Cloud DNS |

## Жизненный цикл IAM-токена

И токен из метаданных, и `iam create-token` выпускают **bearer-токены на 12 часов**. Кэшируй и обновляй; никогда не вставляй в адреса.

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| `Permission denied` для сервисного аккаунта несмотря на роль | Роль привязана к другому каталогу | Проверь через `yc resource-manager folder list-access-bindings $FOLDER_ID` |
| Токен истёк в середине деплоя | 12-часовой IAM-токен в длинном скрипте | Обновляй перед каждым крупным шагом |
| Удалённый пользователь всё ещё авторизован | OAuth-токен закэширован локально | Принудительная повторная авторизация: `yc config profile activate <p>` |
| Сервисному аккаунту случайно дали `admin` | Слишком широкие права | Замени на роли по сервисам; аудит через `yc audit-trails` |
| Под Kubernetes не видит Object Storage | Не привязана рабочая идентичность | Привяжи сервисный аккаунт к группе узлов ИЛИ используй привязку рабочей идентичности |
