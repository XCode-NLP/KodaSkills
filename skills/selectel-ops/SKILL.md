---
name: selectel-ops
description: "Операции только для чтения в Selectel через OpenStack API: явный выбор региона, разрешённые команды `openstack` CLI и правила безопасности для настроенной учётной записи с правами чтения. Используй, когда нужно посмотреть серверы, сети, подсети, порты, группы безопасности, тома, образы, проекты, плавающие IP, роутеры или flavor в Selectel."
license: MIT
metadata:
  author: dekhtyarev
  source: https://github.com/dekhtyarev/devoops-paperclip
  tags: [selectel, облако, openstack, инфраструктура]
---

# Операции в Selectel (только чтение)

Доступ только для чтения через OpenStack API. Оператор выдаёт служебную учётную запись с ролью `reader` только на разрешённые проекты. Идентификаторы учётной записи и проектов, а также настоящая карта регионов задаются приватно.

Аутентификация: `OS_USERNAME`, `OS_PASSWORD`, `OS_AUTH_URL`, `OS_USER_DOMAIN_NAME`, `OS_PROJECT_DOMAIN_NAME`, `OS_IDENTITY_API_VERSION`. Значения выдаёт менеджер секретов; наличие переменных проверяй до команд.

## Выбор региона

Регион выбирается для каждой команды через `$OS_REGION_NAME`, проект — через `$OS_PROJECT_ID`. Не подставляй регион по памяти. Сверяйся с приватной инвентаризацией и каталогом провайдера; облачные и bare-metal пулы могут использовать разные API.

## Разрешённые команды (только чтение)

Всегда добавляй регион в начало:

```bash
OS_REGION_NAME="$OS_REGION_NAME" openstack server list
OS_REGION_NAME="$OS_REGION_NAME" openstack server show <id>
OS_REGION_NAME="$OS_REGION_NAME" openstack network list
OS_REGION_NAME="$OS_REGION_NAME" openstack subnet list
OS_REGION_NAME="$OS_REGION_NAME" openstack port list
OS_REGION_NAME="$OS_REGION_NAME" openstack security group list
OS_REGION_NAME="$OS_REGION_NAME" openstack security group rule list
OS_REGION_NAME="$OS_REGION_NAME" openstack volume list
OS_REGION_NAME="$OS_REGION_NAME" openstack image list
OS_REGION_NAME="$OS_REGION_NAME" openstack project list
OS_REGION_NAME="$OS_REGION_NAME" openstack floating ip list
OS_REGION_NAME="$OS_REGION_NAME" openstack router list
OS_REGION_NAME="$OS_REGION_NAME" openstack flavor list
```

Для отдельно выбранного проекта используй IAM в рамках проекта:

```bash
OS_REGION_NAME="$OS_REGION_NAME" OS_PROJECT_ID="$OS_PROJECT_ID" openstack server list
OS_REGION_NAME="$OS_REGION_NAME" OS_PROJECT_ID="$OS_PROJECT_ID" openstack network list
```

Чтобы проверить доступность конкретного региона:

```bash
OS_REGION_NAME="$OS_REGION_NAME" openstack catalog list
```

## Запрещено (немедленный отказ)

Любые изменения ресурсов Selectel запрещены. Не вызывай команды с глаголами:

- `create`, `delete`, `set`, `unset`, `add`, `remove`, `update`;
- `openstack server reboot|stop|start|shelve|migrate|resize` — это изменение;
- `openstack image upload|save` — тоже изменение;
- `openstack token issue` — само по себе чтение, но **никогда** не выводи токены в журналы, комментарии к MR или в Notion.

Если сомневаешься — прогони команду через `openstack --help` и проверь, что глагол относится к чтению (`list`, `show`).

## Связь с terraform-ops

`openstack` CLI — для **точечных проверок** («какие сейчас VM в проекте?», «висит ли flavor?», «какие правила в группе безопасности?»). Прицельно, во время отладки.

`terraform plan -chdir=envs/<env>` — для **изменений**. Через MR в репозитории инфраструктуры, никогда не `apply` напрямую из агента. Процесс описан в навыке `terraform-ops`.

Никогда не используй `openstack ... create/delete` как замену Terraform — расхождение состояния сломает следующий `terraform plan` и потребует ручного `terraform state rm` + `terraform import` для починки.

## Правила безопасности

Общий список — в навыке `safety-guardrails`. Главное, что специфично для Selectel:

- Все изменения ресурсов Selectel — только через MR с terraform.
- **Никогда** не логируй `$OS_PASSWORD` (в выводе shell, комментариях к MR, комментариях в Notion, сообщениях алертов).
- Передача учётных данных — только явное решение оператора; отдельное окружение на агента не является изоляцией процесса. Утечка требует немедленной эскалации без чтения или вывода секрета. Ротация — это ручной регламент или CI, но никогда не последовательность команд агента.
- Соблюдай лимиты провайдера и `retry-after` в ответе. Не запускай параллельные циклы `openstack ... list` — используй `--long` / `-f json` и локальный фильтр через jq.

## Полезные однострочники

```bash
# Все VM во всех проектах выбранного региона (одна команда, без цикла)
OS_REGION_NAME="$OS_REGION_NAME" openstack server list --all-projects -f json

# Плавающие IP, привязанные к серверам
OS_REGION_NAME="$OS_REGION_NAME" openstack floating ip list --status ACTIVE -f json \
  | jq '.[] | select(.["Fixed IP Address"] != null)'

# Проверка связности до эндпоинта OpenStack
OS_REGION_NAME="$OS_REGION_NAME" openstack token issue >/dev/null && echo "auth OK"

# Снимок всех проектов Selectel в JSON
openstack project list -f json
```

## Документация

- Документация Selectel: <https://docs.selectel.ru/en/cloud-servers/>
- Справочник OpenStack CLI: <https://docs.openstack.org/python-openstackclient/latest/cli/index.html>
- Terraform-провайдер Selectel/OpenStack: <https://registry.terraform.io/providers/selectel/selectel/latest/docs>
- Локации Selectel (источник истины для карты регионов): <https://docs.selectel.ru/en/infrastructure/locations/>
