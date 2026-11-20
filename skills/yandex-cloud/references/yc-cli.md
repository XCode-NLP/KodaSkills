# `yc` CLI

Каноническая документация: https://github.com/yandex-cloud/docs/tree/master/ru/cli · Публичная: https://yandex.cloud/ru/docs/cli/

## Установка

```bash
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
exec -l $SHELL              # перезагрузить PATH
yc version                  # проверить
yc components update        # rolling release; обновляй регулярно
```

Системная установка для CI и автоматизации: скачай статический бинарник с `https://storage.yandexcloud.net/yandexcloud-yc/release/<version>/linux/amd64/yc` и положи в `/usr/local/bin/yc`. Закрепляй версию в CI; не запускай `components update` в контейнерах CI.

## Режимы авторизации

| Режим | Когда | Как |
|---|---|---|
| **Интерактивный OAuth** | Разовая настройка для разработки | `yc init` → откроется браузер → токен сохраняется в `~/.config/yandex-cloud/config.yaml` |
| **Ключ сервисного аккаунта** | CI/CD, скрипты, продакшен | `yc iam key create --service-account-id <id> -o sa-key.json` → `yc config set service-account-key sa-key.json` |
| **IAM-токен** (короткоживущий) | Прямой API, gRPC-клиенты | `yc iam create-token` → Bearer на 12 часов, обновляй до истечения |
| **Федеративная авторизация (SAML/OIDC)** | Организация с корпоративным IdP | `yc init` с `--federation-id` |
| **Сервер метаданных** (внутри машины) | Машина с привязанным сервисным аккаунтом | Без ключей: `curl 169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token` |

Правило продакшена: **никогда** не вставляй OAuth-токены в скрипты. Всегда ключ сервисного аккаунта или метаданные машины. OAuth-токен живёт по сроку пользователя, ключ сервисного аккаунта отзывается отдельно.

## Профили

```bash
yc config profile list
yc config profile create prod
yc config profile activate prod
yc config set cloud-id b1g…  folder-id b1g…  service-account-key ./sa.json
yc config list                            # текущий профиль
```

Совет: профили на каталог (`profile-staging`, `profile-prod`) предотвращают ошибки между каталогами — самую частую причину аварий в YC.

## Форматы вывода

| Флаг | Вывод |
|---|---|
| (по умолчанию) | Красивая таблица |
| `--format json` | JSON для машинного разбора |
| `--format yaml` | YAML для цикла `yc * update --file` |
| `--format value` | Голое значение (одно поле, без заголовков) — для `$(yc … --format value)` |

`--jq '.id'` применяет jq к JSON-выводу — встроено, без конвейера.

## Частые шаблоны

```bash
# Получить ID каталога в переменную окружения
export YC_FOLDER_ID=$(yc config get folder-id)

# Получить одно поле через jq
INSTANCE_ID=$(yc compute instance get my-vm --format json --jq '.id')

# Редактирование через цикл
yc compute instance get my-vm --format yaml > /tmp/i.yaml
$EDITOR /tmp/i.yaml
yc compute instance update my-vm --file /tmp/i.yaml      # поддерживаются только некоторые поля — сверься с документацией

# Дождаться асинхронной операции
OP=$(yc compute instance create … --async --format value)
yc operation get "$OP"            # опрашивай, пока done=true
yc wait "$OP"                     # блокируется до завершения
```

## Гигиена скриптов

- Всегда `--async` для долгих операций в CI, затем `yc wait` — это спасает от таймаута по умолчанию в 5 минут
- Закрепляй версию `yc`: `yc components update --version=<x.y.z>` в образе раннера
- Для скриптов администрирования нескольких каталогов: передавай `--folder-id <id>` явно в каждом вызове, не полагайся на активный профиль
- Ошибки печатаются в stderr; проверяй `$?` — `yc` возвращает ненулевой код при сбое

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| `permission denied: resource-manager.clouds.list` | Активный профиль указывает на чужое облако | `yc config profile activate <правильный>` |
| `Cannot perform request: Federation token expired` | Истекла cookie SAML | Повторная авторизация `yc init --federation-id … --no-browser` |
| `tcp dial tcp [...]:443: i/o timeout` | UFW или прокси блокирует `*.api.cloud.yandex.net` | Разреши исходящий трафик на 443 к этому хосту |
| Медленный первый вызов после простоя | Разрешение DNS | Ничего не кэшируй — это нормально |
| Скрипт работает не с тем каталогом | Забыл активировать профиль | Передавай `--folder-id` в каждом вызове ИЛИ активируй профиль в начале скрипта |
