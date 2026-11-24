---
name: terraform-test
description: "Подробное руководство по написанию и запуску тестов Terraform. Используй при создании тестовых файлов (.tftest.hcl), написании сценариев с блоками run, проверке поведения инфраструктуры через утверждения, подмене провайдеров и источников данных, тестировании выходных значений модулей и конфигураций ресурсов, а также при разборе синтаксиса и выполнения тестов Terraform."
license: MPL-2.0
metadata:
  author: hashicorp
  source: https://github.com/hashicorp/agent-skills
  tags: [terraform, тестирование]
---

# Тесты Terraform

Встроенный фреймворк тестирования Terraform проверяет, что обновления конфигурации не вносят ломающих изменений. Тесты выполняются на временных ресурсах, защищая существующую инфраструктуру и файлы состояния.

## Справочные файлы

- `references/MOCK_PROVIDERS.md` — синтаксис подменяющих провайдеров, частые значения по умолчанию, когда использовать подмену (только Terraform 1.7.0+ — пропусти, если версия пользователя ниже 1.7);
- `references/CI_CD.md` — примеры конвейеров GitHub Actions и GitLab CI;
- `references/EXAMPLES.md` — полный пример набора тестов (модульные, интеграционные и с подменой для модуля VPC).

Читай нужный справочный файл, когда пользователь спрашивает про подмену, интеграцию с CI/CD или хочет полный пример.

## Основные понятия

- **Тестовый файл** (`.tftest.hcl` / `.tftest.json`): содержит блоки `run`, проверяющие конфигурацию;
- **Блок run**: один тестовый сценарий с необязательными переменными, провайдерами и утверждениями;
- **Блок assert**: условия, которые должны быть истинны, чтобы тест прошёл;
- **Подменяющий провайдер**: имитирует поведение провайдера без настоящей инфраструктуры (Terraform 1.7.0+);
- **Режимы теста**: `apply` (по умолчанию, создаёт настоящие ресурсы) или `plan` (проверяет только логику).

## Структура файлов

```
my-module/
├── main.tf
├── variables.tf
├── outputs.tf
└── tests/
    ├── defaults_unit_test.tftest.hcl         # plan mode — fast, no resources
    ├── validation_unit_test.tftest.hcl        # plan mode
    └── full_stack_integration_test.tftest.hcl # apply mode — creates real resources
```

Используй `*_unit_test.tftest.hcl` для тестов в режиме плана и `*_integration_test.tftest.hcl` для тестов в режиме применения, чтобы их можно было фильтровать в CI по отдельности.

## Структура тестового файла

```hcl
# Optional: test-wide settings
test {
  parallel = true  # Enable parallel execution for all run blocks (default: false)
}

# Optional: file-level variables (highest precedence, override all other sources)
variables {
  aws_region    = "us-west-2"
  instance_type = "t2.micro"
}

# Optional: provider configuration
provider "aws" {
  region = var.aws_region
}

# Required: at least one run block
run "test_default_configuration" {
  command = plan

  assert {
    condition     = aws_instance.example.instance_type == "t2.micro"
    error_message = "Instance type should be t2.micro by default"
  }
}
```

## Блок run

```hcl
run "test_name" {
  command  = plan  # or apply (default)
  parallel = true  # optional, since v1.9.0

  # Override file-level variables
  variables {
    instance_type = "t3.large"
  }

  # Reference a specific module
  module {
    source  = "./modules/vpc"  # local or registry only (not git/http)
    version = "5.0.0"          # registry modules only
  }

  # Control state isolation
  state_key = "shared_state"  # since v1.9.0

  # Plan behavior
  plan_options {
    mode    = refresh-only  # or normal (default)
    refresh = true
    replace = [aws_instance.example]
    target  = [aws_instance.example]
  }

  # Assertions
  assert {
    condition     = aws_instance.example.id != ""
    error_message = "Instance should have a valid ID"
  }

  # Expected failures (test passes if these fail)
  expect_failures = [
    var.instance_count
  ]
}
```

## Частые приёмы тестирования

### Проверка выходных значений

```hcl
run "test_outputs" {
  command = plan

  assert {
    condition     = output.vpc_id != null
    error_message = "VPC ID output must be defined"
  }

  assert {
    condition     = can(regex("^vpc-", output.vpc_id))
    error_message = "VPC ID should start with 'vpc-'"
  }
}
```

### Условные ресурсы

```hcl
run "test_nat_gateway_disabled" {
  command = plan

  variables {
    create_nat_gateway = false
  }

  assert {
    condition     = length(aws_nat_gateway.main) == 0
    error_message = "NAT gateway should not be created when disabled"
  }
}
```

### Количество ресурсов

```hcl
run "test_resource_count" {
  command = plan

  variables {
    instance_count = 3
  }

  assert {
    condition     = length(aws_instance.workers) == 3
    error_message = "Should create exactly 3 worker instances"
  }
}
```

### Метки

```hcl
run "test_resource_tags" {
  command = plan

  variables {
    common_tags = {
      Environment = "production"
      ManagedBy   = "Terraform"
    }
  }

  assert {
    condition     = aws_instance.example.tags["Environment"] == "production"
    error_message = "Environment tag should be set correctly"
  }

  assert {
    condition     = aws_instance.example.tags["ManagedBy"] == "Terraform"
    error_message = "ManagedBy tag should be set correctly"
  }
}
```

### Источники данных

```hcl
run "test_data_source_lookup" {
  command = plan

  assert {
    condition     = data.aws_ami.ubuntu.id != ""
    error_message = "Should find a valid Ubuntu AMI"
  }

  assert {
    condition     = can(regex("^ami-", data.aws_ami.ubuntu.id))
    error_message = "AMI ID should be in correct format"
  }
}
```

### Правила валидации

```hcl
run "test_invalid_environment" {
  command = plan

  variables {
    environment = "invalid"
  }

  expect_failures = [
    var.environment
  ]
}
```

### Последовательные тесты с зависимостями

```hcl
run "setup_vpc" {
  command = apply

  assert {
    condition     = output.vpc_id != ""
    error_message = "VPC should be created"
  }
}

run "test_subnet_in_vpc" {
  command = plan

  variables {
    vpc_id = run.setup_vpc.vpc_id
  }

  assert {
    condition     = aws_subnet.example.vpc_id == run.setup_vpc.vpc_id
    error_message = "Subnet should be in the VPC from setup_vpc"
  }
}
```

### Опции плана (только обновление, точечно)

```hcl
run "test_refresh_only" {
  command = plan

  plan_options {
    mode = refresh-only
  }

  assert {
    condition     = aws_instance.example.tags["Environment"] == "production"
    error_message = "Tags should be refreshed correctly"
  }
}

run "test_specific_resource" {
  command = plan

  plan_options {
    target = [aws_instance.example]
  }

  assert {
    condition     = aws_instance.example.instance_type == "t2.micro"
    error_message = "Targeted resource should be planned"
  }
}
```

### Параллельные модули

```hcl
run "test_networking_module" {
  command  = plan
  parallel = true

  module {
    source = "./modules/networking"
  }

  assert {
    condition     = output.vpc_id != ""
    error_message = "VPC should be created"
  }
}

run "test_compute_module" {
  command  = plan
  parallel = true

  module {
    source = "./modules/compute"
  }

  assert {
    condition     = output.instance_id != ""
    error_message = "Instance should be created"
  }
}
```

### Совместное использование ключа состояния

```hcl
run "create_foundation" {
  command   = apply
  state_key = "foundation"

  assert {
    condition     = aws_vpc.main.id != ""
    error_message = "Foundation VPC should be created"
  }
}

run "create_application" {
  command   = apply
  state_key = "foundation"

  variables {
    vpc_id = run.create_foundation.vpc_id
  }

  assert {
    condition     = aws_instance.app.vpc_id == run.create_foundation.vpc_id
    error_message = "Application should use foundation VPC"
  }
}
```

### Порядок очистки (объекты S3 раньше бакета)

```hcl
run "create_bucket" {
  command = apply

  assert {
    condition     = aws_s3_bucket.example.id != ""
    error_message = "Bucket should be created"
  }
}

run "add_objects" {
  command = apply

  assert {
    condition     = length(aws_s3_object.files) > 0
    error_message = "Objects should be added"
  }
}

# Cleanup destroys in reverse: objects first, then bucket
```

### Несколько провайдеров с псевдонимами

```hcl
provider "aws" {
  alias  = "primary"
  region = "us-west-2"
}

provider "aws" {
  alias  = "secondary"
  region = "us-east-1"
}

run "test_with_specific_provider" {
  command = plan

  providers = {
    aws = provider.aws.secondary
  }

  assert {
    condition     = aws_instance.example.availability_zone == "us-east-1a"
    error_message = "Instance should be in us-east-1 region"
  }
}
```

### Сложные условия

```hcl
assert {
  condition = alltrue([
    for subnet in aws_subnet.private :
    can(regex("^10\\.0\\.", subnet.cidr_block))
  ])
  error_message = "All private subnets should use 10.0.0.0/8 CIDR range"
}
```

## Очистка

После завершения теста ресурсы уничтожаются в **обратном порядке блоков run**. Это важно для зависимостей (например, объекты S3 раньше бакета). Используй `terraform test -no-cleanup`, чтобы пропустить очистку при отладке.

## Запуск тестов

```bash
terraform test                                        # all tests
terraform test tests/defaults.tftest.hcl             # specific file
terraform test -filter=test_vpc_configuration        # by run block name
terraform test -test-directory=integration-tests     # custom directory
terraform test -verbose                              # detailed output
terraform test -no-cleanup                           # skip resource cleanup
```

## Рекомендации

1. **Именование**: `*_unit_test.tftest.hcl` для режима плана, `*_integration_test.tftest.hcl` для режима применения.
2. **Имена тестов**: используй описательные имена блоков run, объясняющие проверяемый сценарий.
3. **По умолчанию план**: используй `command = plan`, если не нужно проверять реальное поведение ресурсов.
4. **Используй подмену** для внешних зависимостей — быстрее и не нужны учётные данные (см. `references/MOCK_PROVIDERS.md`).
5. **Сообщения об ошибках**: делай их достаточно конкретными, чтобы диагностировать сбой без повторного запуска теста.
6. **Негативные тесты**: используй `expect_failures`, чтобы проверить, что правила валидации отвергают плохие входные данные.
7. **Покрытие переменных**: проверяй разные комбинации переменных, чтобы пройти все ветки кода — переменные теста имеют наивысший приоритет и переопределяют все другие источники.
8. **Источники модулей**: тестовые файлы поддерживают только локальные пути и модули из реестра — не URL git и HTTP.
9. **Параллельное выполнение**: используй `parallel = true` для независимых тестов с разными файлами состояния.
10. **Очистка**: интеграционные тесты уничтожают ресурсы в обратном порядке блоков run автоматически; используй `-no-cleanup` для отладки.
11. **CI/CD**: запускай модульные тесты на каждом pull request, интеграционные — при слиянии (см. `references/CI_CD.md`).

## Разбор проблем

| Проблема | Решение |
|-------|----------|
| Сбои утверждений | Используй `-verbose`, чтобы увидеть фактические и ожидаемые значения |
| Нет учётных данных | Используй подменяющие провайдеры для модульных тестов |
| Неподдерживаемый источник модуля | Преобразуй источники git и HTTP в локальные модули |
| Тесты мешают друг другу | Используй `state_key` или отдельные модули для изоляции |
| Медленные тесты | Используй `command = plan` и подмену; интеграционные тесты запускай отдельно |

## Ссылки

- [Документация по тестированию Terraform](https://developer.hashicorp.com/terraform/language/tests)
- [Команда terraform test](https://developer.hashicorp.com/terraform/cli/commands/test)
