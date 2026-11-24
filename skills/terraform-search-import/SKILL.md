---
name: terraform-search-import
description: "Поиск существующих облачных ресурсов через запросы Terraform Search и их массовый импорт под управление Terraform. Используй, когда нужно взять неуправляемую инфраструктуру под контроль Terraform, провести аудит облачных ресурсов или перейти на инфраструктуру как код."
license: MPL-2.0
compatibility: "Требуется Terraform 1.14 или новее и провайдеры с поддержкой list-ресурсов"
metadata:
  author: hashicorp
  source: https://github.com/hashicorp/agent-skills
  tags: [terraform, импорт, облако]
---

# Поиск и массовый импорт в Terraform

Находи существующие облачные ресурсы через декларативные запросы и генерируй конфигурацию для массового импорта в состояние Terraform.

**Ссылки:**
- [Terraform Search — блок list](https://developer.hashicorp.com/terraform/language/block/tfquery/list)
- [Массовый импорт](https://developer.hashicorp.com/terraform/language/import/bulk)

## Когда использовать

- Когда нужно взять неуправляемые ресурсы под контроль Terraform.
- Для аудита существующей облачной инфраструктуры.
- При переходе от ручного провижининга к инфраструктуре как коду.
- Для поиска ресурсов в нескольких регионах и аккаунтах.

## ВАЖНО: сначала проверь поддержку провайдера

**ДО начала ты ОБЯЗАН убедиться, что целевой тип ресурса поддерживается:**

```bash
# посмотреть, какие list-ресурсы доступны
./scripts/list_resources.sh aws      # конкретный провайдер
./scripts/list_resources.sh          # все настроенные провайдеры
```

## Дерево решений

1. **Определи целевой тип ресурса** (например, aws_s3_bucket, aws_instance).
2. **Проверь поддержку**: запусти `./scripts/list_resources.sh <provider>`.
3. **Выбери порядок работы**:
   - **Если поддерживается**: проверь доступную версию Terraform.
   - **Если версия Terraform выше 1.14.0**: используй порядок работы Terraform Search (ниже).
   - **Если не поддерживается или версия Terraform ниже 1.14.0**: используй порядок ручного поиска (см. [references/MANUAL-IMPORT.md](references/MANUAL-IMPORT.md)).

   **Замечание**: список поддерживаемых ресурсов быстро растёт. Всегда проверяй текущую поддержку, прежде чем прибегать к ручному импорту.

## Предусловия

Прежде чем писать запросы, убедись, что провайдер поддерживает list-ресурсы для твоего целевого типа.

### Узнай доступные list-ресурсы

Запусти вспомогательный скрипт, чтобы извлечь поддерживаемые list-ресурсы из провайдера:

```bash
# из директории с конфигурацией провайдера (при необходимости запускает terraform init)
./scripts/list_resources.sh aws      # конкретный провайдер
./scripts/list_resources.sh          # все настроенные провайдеры
```

Либо запроси схему провайдера вручную:

```bash
terraform providers schema -json | jq '.provider_schemas | to_entries | map({key: (.key | split("/")[-1]), value: (.value.list_resource_schemas // {} | keys)})'
```

Terraform Search требует инициализированной рабочей директории. Убедись, что есть конфигурация с нужным провайдером, прежде чем запускать запросы:

```hcl
# terraform.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

Запусти `terraform init`, чтобы скачать провайдер, затем переходи к запросам.

## Порядок работы Terraform Search (только поддерживаемые ресурсы)

1. Создай файлы `.tfquery.hcl` с блоками `list`, задающими поисковые запросы.
2. Запусти `terraform query`, чтобы найти подходящие ресурсы.
3. Сгенерируй конфигурацию через `-generate-config-out=<file>`.
4. Проверь и доработай сгенерированные блоки `resource` и `import`.
5. Запусти `terraform plan` и `terraform apply`, чтобы импортировать.

## Структура файла запросов

Файлы запросов используют расширение `.tfquery.hcl` и поддерживают:
- блоки `provider` для аутентификации;
- блоки `list` для поиска ресурсов;
- блоки `variable` и `locals` для параметризации.

```hcl
# discovery.tfquery.hcl
provider "aws" {
  region = "us-west-2"
}

list "aws_instance" "all" {
  provider = aws
}
```

## Синтаксис блока list

```hcl
list "<list_type>" "<symbolic_name>" {
  provider = <provider_reference>  # Required

  # Optional: filter configuration (provider-specific)
  # The `config` block schema is provider-specific. Discover available options using `terraform providers schema -json | jq '.provider_schemas."registry.terraform.io/hashicorp/<provider>".list_resource_schemas."<resource_type>"'`

  config {
    filter {
      name   = "<filter_name>"
      values = ["<value1>", "<value2>"]
    }
    region = "<region>"  # AWS-specific
  }
  # Optional: limit results
  limit = 100
}
```

## Поддерживаемые list-ресурсы

Поддержка list-ресурсов зависит от версии провайдера. **Всегда проверяй, что доступно в твоей версии провайдера, через скрипт поиска.**

## Примеры запросов

### Базовый поиск

```hcl
# найти все инстансы EC2 в настроенном регионе
list "aws_instance" "all" {
  provider = aws
}
```

### Поиск с фильтрами

```hcl
# найти инстансы по метке
list "aws_instance" "production" {
  provider = aws

  config {
    filter {
      name   = "tag:Environment"
      values = ["production"]
    }
  }
}

# найти инстансы по типу
list "aws_instance" "large" {
  provider = aws

  config {
    filter {
      name   = "instance-type"
      values = ["t3.large", "t3.xlarge"]
    }
  }
}
```

### Поиск в нескольких регионах

```hcl
provider "aws" {
  region = "us-west-2"
}

locals {
  regions = ["us-west-2", "us-east-1", "eu-west-1"]
}

list "aws_instance" "all_regions" {
  for_each = toset(local.regions)
  provider = aws

  config {
    region = each.value
  }
}
```

### Параметризованные запросы

```hcl
variable "target_environment" {
  type    = string
  default = "staging"
}

list "aws_instance" "by_env" {
  provider = aws

  config {
    filter {
      name   = "tag:Environment"
      values = [var.target_environment]
    }
  }
}
```

## Запуск запросов

```bash
# выполнить запросы и показать результаты
terraform query

# сгенерировать файл конфигурации
terraform query -generate-config-out=imported.tf

# передать переменные
terraform query -var='target_environment=production'
```

## Формат вывода запроса

```
list.aws_instance.all   account_id=123456789012,id=i-0abc123,region=us-west-2   web-server
```

Столбцы: `<query_address>   <identity_attributes>   <name_tag>`

## Сгенерированная конфигурация

Флаг `-generate-config-out` создаёт:

```hcl
# __generated__ by Terraform
resource "aws_instance" "all_0" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  # ... all attributes
}

import {
  to       = aws_instance.all_0
  provider = aws
  identity = {
    account_id = "123456789012"
    id         = "i-0abc123"
    region     = "us-west-2"
  }
}
```

## Доработка после генерации

Сгенерированная конфигурация содержит все атрибуты. Приведи её в порядок:

1. Удали вычисляемые атрибуты только для чтения.
2. Замени жёстко заданные значения переменными.
3. Дай ресурсам осмысленные имена.
4. Разложи по подходящим файлам.

```hcl
# Before: generated
resource "aws_instance" "all_0" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t2.micro"
  arn                    = "arn:aws:ec2:..."  # Remove - computed
  id                     = "i-0abc123"        # Remove - computed
  # ... many more attributes
}

# After: cleaned
resource "aws_instance" "web_server" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id

  tags = {
    Name        = "web-server"
    Environment = var.environment
  }
}
```

## Импорт по идентификатору

Сгенерированные импорты используют импорт по идентификатору (Terraform 1.12+):

```hcl
import {
  to       = aws_instance.web
  provider = aws
  identity = {
    account_id = "123456789012"
    id         = "i-0abc123"
    region     = "us-west-2"
  }
}
```

## Проверка импортированного состояния

После `terraform apply`, который импортирует ресурсы, проверь, что действительно попало в состояние.
Предпочитай документированные, стабильные и более экономные по токенам команды чтению сырого
файла состояния:

```bash
# убедиться, что ресурсы теперь управляются (и заодно проверить адреса)
terraform state list

# посмотреть итоговые значения атрибутов импортированных ресурсов
terraform show -json | jq '.values.root_module.resources[] | {address, type, name}'
```

`terraform show -json` требует установленных провайдеров (`terraform init`), поскольку
он отрисовывает значения по схемам провайдеров. **Обращайся к сырому состоянию
(`terraform state pull` или `terraform.tfstate`) только когда** провайдеры недоступны и
`init` не может выполниться, нужна лишь грубая информация (адреса, выходные значения, `serial` и `lineage`)
или нужно избежать запуска Terraform. Не разбирай сырой формат состояния версии 4 как стабильный
интерфейс. **Замечание:** состояние содержит чувствительные значения в открытом виде в любом формате — никогда
не выводи содержимое состояния в журналы или в чат.

## Рекомендации

### Проектирование запросов
- Начинай широко, затем добавляй фильтры, чтобы сузить результаты.
- Используй `limit`, чтобы не переполнить вывод.
- Проверяй запросы до генерации конфигурации.

### Работа с конфигурацией
- Проверяй весь сгенерированный код перед применением.
- Удаляй ненужные значения по умолчанию.
- Придерживайся единых соглашений об именовании.
- Добавляй нормальную абстракцию через переменные.

## Разбор проблем

| Проблема | Решение |
|-------|----------|
| «No list resources found» | Проверь, что версия провайдера поддерживает list-ресурсы |
| Запрос возвращает пусто | Проверь регион и значения фильтров |
| В сгенерированной конфигурации ошибки | Удали вычисляемые атрибуты, исправь устаревшие аргументы |
| Импорт падает | Убедись, что ресурса ещё нет в состоянии |

## Полный пример

```hcl
# main.tf - Initialize provider
terraform {
  required_version = ">= 1.14"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"  # Always use latest version
    }
  }
}

# discovery.tfquery.hcl - Define queries
provider "aws" {
  region = "us-west-2"
}

list "aws_instance" "team_instances" {
  provider = aws

  config {
    filter {
      name   = "tag:Owner"
      values = ["platform"]
    }
    filter {
      name   = "instance-state-name"
      values = ["running"]
    }
  }

  limit = 50
}
```

```bash
# Execute workflow
terraform init
terraform query
terraform query -generate-config-out=generated.tf
# Review and clean generated.tf
terraform plan
terraform apply
```
