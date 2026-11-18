---
name: terraform-style-guide
description: "Генерация кода Terraform HCL по официальным стилистическим соглашениям и лучшим практикам HashiCorp. Используй при написании, проверке или генерации конфигураций Terraform."
license: MPL-2.0
metadata:
  author: hashicorp
  source: https://github.com/hashicorp/agent-skills
---

# Стиль Terraform

Пиши и поддерживай код Terraform по официальным стилистическим соглашениям и лучшим практикам HashiCorp.

**Справка:** [HashiCorp Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style)

## Как строить генерацию кода

Когда генерируешь код Terraform:

1. Начни с конфигурации провайдера и ограничений версий.
2. Создавай источники данных раньше зависимых ресурсов.
3. Строй ресурсы в порядке зависимостей.
4. Добавь выходные значения для ключевых атрибутов ресурсов.
5. Используй переменные для всех настраиваемых значений.

## Организация файлов

| Файл | Назначение |
|------|---------|
| `terraform.tf` | Требования к версиям Terraform и провайдеров |
| `providers.tf` | Конфигурации провайдеров |
| `main.tf` | Основные ресурсы и источники данных |
| `variables.tf` | Объявления входных переменных (по алфавиту) |
| `outputs.tf` | Объявления выходных значений (по алфавиту) |
| `locals.tf` | Объявления локальных значений |

### Пример структуры

```hcl
# terraform.tf
terraform {
  required_version = ">= 1.14"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# variables.tf
variable "environment" {
  description = "Target deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# locals.tf
locals {
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.environment}-vpc"
  })
}

# outputs.tf
output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}
```

## Форматирование кода

### Отступы и выравнивание

- Используй **два пробела** на уровень вложенности (никаких табуляций).
- Выравнивай знаки равенства у подряд идущих аргументов.

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"
  subnet_id     = "subnet-12345678"

  tags = {
    Name        = "web-server"
    Environment = "production"
  }
}
```

### Организация блоков

Аргументы идут перед блоками, метааргументы — первыми:

```hcl
resource "aws_instance" "example" {
  # Meta-arguments
  count = 3

  # Arguments
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  # Blocks
  root_block_device {
    volume_size = 20
  }

  # Lifecycle last
  lifecycle {
    create_before_destroy = true
  }
}
```

## Соглашения об именовании

- Используй **строчные буквы с подчёркиваниями** для всех имён.
- Используй **описательные существительные**, не повторяя тип ресурса.
- Будь конкретным и осмысленным.
- Имена ресурсов в единственном числе, не во множественном.
- По умолчанию используй `main` для ресурсов, где конкретное описательное имя избыточно или недоступно, при условии что экземпляр только один.

```hcl
# Bad
resource "aws_instance" "webAPI-aws-instance" {}
resource "aws_instance" "web_apis" {}
variable "name" {}

# Good
resource "aws_instance" "web_api" {}
resource "aws_vpc" "main" {}
variable "application_name" {}
```

## Переменные

У каждой переменной должны быть `type` и `description`:

```hcl
variable "instance_type" {
  description = "EC2 instance type for the web server"
  type        = string
  default     = "t2.micro"

  validation {
    condition     = contains(["t2.micro", "t2.small", "t2.medium"], var.instance_type)
    error_message = "Instance type must be t2.micro, t2.small, or t2.medium."
  }
}

variable "database_password" {
  description = "Password for the database admin user"
  type        = string
  sensitive   = true
}
```

## Выходные значения

У каждого выходного значения должно быть `description`:

```hcl
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.web.id
}

output "database_password" {
  description = "Database administrator password"
  value       = aws_db_instance.main.password
  sensitive   = true
}
```

## Динамическое создание ресурсов

### Предпочитай for_each вместо count

```hcl
# Bad - count for multiple resources
resource "aws_instance" "web" {
  count = var.instance_count
  tags  = { Name = "web-${count.index}" }
}

# Good - for_each with named instances
variable "instance_names" {
  type    = set(string)
  default = ["web-1", "web-2", "web-3"]
}

resource "aws_instance" "web" {
  for_each = var.instance_names
  tags     = { Name = each.key }
}
```

### count для условного создания

```hcl
resource "aws_cloudwatch_metric_alarm" "cpu" {
  count = var.enable_monitoring ? 1 : 0

  alarm_name = "high-cpu-usage"
  threshold  = 80
}
```

## Лучшие практики безопасности

Обратись к [SECURITY.md](SECURITY.md). Там есть рекомендации по шифрованию ресурсов,
предотвращению попадания чувствительных данных в состояние и безопасным конфигурациям.

## Фиксация версий

```hcl
terraform {
  required_version = ">= 1.14"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

Используй последнюю мажорную версию каждого провайдера и последнюю минорную версию
Terraform, если иное не задано файлом блокировки зависимостей или другими
модулями, которые использует конфигурация.

**Операторы ограничения версий:**
- `= 1.0.0` — точная версия;
- `>= 1.0.0` — больше или равно;
- `~> 1.0` — разрешает увеличивать крайний правый компонент;
- `>= 1.0, < 2.0` — диапазон версий.

## Конфигурация провайдера

```hcl
provider "aws" {
  region = "us-west-2"

  default_tags {
    tags = {
      ManagedBy = "Terraform"
      Project   = var.project_name
    }
  }
}

# Aliased provider for multi-region
provider "aws" {
  alias  = "east"
  region = "us-east-1"
}
```

## Контроль версий

**Никогда не коммить:**
- `terraform.tfstate`, `terraform.tfstate.backup`;
- директорию `.terraform/`;
- `*.tfplan`;
- файлы `.tfvars` с чувствительными данными.

**Всегда коммить:**
- все файлы конфигурации `.tf`;
- `.terraform.lock.hcl` (файл блокировки зависимостей).

## Инструменты проверки

Запускай перед коммитом:

```bash
terraform fmt -recursive
terraform validate
```

Дополнительные инструменты:
- `tflint` — линтинг и лучшие практики;
- `checkov` и `tfsec` — сканирование безопасности.

## Чек-лист проверки кода

- [ ] Код отформатирован через `terraform fmt`
- [ ] Конфигурация проверена через `terraform validate`
- [ ] Файлы организованы по стандартной структуре
- [ ] У всех переменных есть тип и описание
- [ ] У всех выходных значений есть описание
- [ ] Имена ресурсов — описательные существительные с подчёркиваниями
- [ ] Ограничения версий заданы явно
- [ ] Чувствительные значения помечены `sensitive = true`
- [ ] Нет вшитых учётных данных и секретов
- [ ] Применены лучшие практики безопасности

---

*По материалам: [HashiCorp Terraform Style Guide](https://developer.hashicorp.com/terraform/language/style)*
