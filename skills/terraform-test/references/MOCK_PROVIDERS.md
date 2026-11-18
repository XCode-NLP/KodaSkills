# Подменяющие провайдеры

Подменяющие провайдеры имитируют поведение провайдера, не создавая настоящую инфраструктуру (Terraform 1.7.0+). Используй их для быстрых модульных тестов без учётных данных.

## Базовый подменяющий провайдер

```hcl
mock_provider "aws" {
  mock_resource "aws_instance" {
    defaults = {
      id            = "i-1234567890abcdef0"
      instance_type = "t2.micro"
      ami           = "ami-12345678"
      public_ip     = "203.0.113.1"
      private_ip    = "10.0.1.100"
    }
  }

  mock_data "aws_ami" {
    defaults = {
      id = "ami-0c55b159cbfafe1f0"
    }
  }

  mock_data "aws_availability_zones" {
    defaults = {
      names = ["us-west-2a", "us-west-2b", "us-west-2c"]
    }
  }
}

run "test_with_mocks" {
  command = plan  # Mocks only work with plan mode

  assert {
    condition     = aws_instance.example.id == "i-1234567890abcdef0"
    error_message = "Mock instance ID should match"
  }
}
```

## Подменяющий провайдер с псевдонимом

```hcl
mock_provider "aws" {
  alias = "mocked"

  mock_resource "aws_s3_bucket" {
    defaults = {
      id  = "test-bucket-12345"
      arn = "arn:aws:s3:::test-bucket-12345"
    }
  }
}

run "test_with_aliased_mock" {
  command = plan

  providers = {
    aws = provider.aws.mocked
  }

  assert {
    condition     = aws_s3_bucket.example.id == "test-bucket-12345"
    error_message = "Bucket ID should match mock"
  }
}
```

## Частые значения подмены

```hcl
mock_provider "aws" {
  mock_resource "aws_instance" {
    defaults = {
      id                          = "i-1234567890abcdef0"
      arn                         = "arn:aws:ec2:us-west-2:123456789012:instance/i-1234567890abcdef0"
      instance_type               = "t2.micro"
      ami                         = "ami-12345678"
      availability_zone           = "us-west-2a"
      subnet_id                   = "subnet-12345678"
      vpc_security_group_ids      = ["sg-12345678"]
      associate_public_ip_address = true
      public_ip                   = "203.0.113.1"
      private_ip                  = "10.0.1.100"
      tags                        = {}
    }
  }

  mock_resource "aws_vpc" {
    defaults = {
      id                   = "vpc-12345678"
      arn                  = "arn:aws:ec2:us-west-2:123456789012:vpc/vpc-12345678"
      cidr_block           = "10.0.0.0/16"
      enable_dns_hostnames = true
      enable_dns_support   = true
      instance_tenancy     = "default"
      tags                 = {}
    }
  }

  mock_resource "aws_subnet" {
    defaults = {
      id                      = "subnet-12345678"
      arn                     = "arn:aws:ec2:us-west-2:123456789012:subnet/subnet-12345678"
      vpc_id                  = "vpc-12345678"
      cidr_block              = "10.0.1.0/24"
      availability_zone       = "us-west-2a"
      map_public_ip_on_launch = false
      tags                    = {}
    }
  }

  mock_resource "aws_s3_bucket" {
    defaults = {
      id                 = "test-bucket-12345"
      arn                = "arn:aws:s3:::test-bucket-12345"
      bucket             = "test-bucket-12345"
      bucket_domain_name = "test-bucket-12345.s3.amazonaws.com"
      region             = "us-west-2"
      tags               = {}
    }
  }

  mock_data "aws_ami" {
    defaults = {
      id                  = "ami-0c55b159cbfafe1f0"
      name                = "ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-20210430"
      architecture        = "x86_64"
      root_device_type    = "ebs"
      virtualization_type = "hvm"
    }
  }

  mock_data "aws_availability_zones" {
    defaults = {
      names    = ["us-west-2a", "us-west-2b", "us-west-2c"]
      zone_ids = ["usw2-az1", "usw2-az2", "usw2-az3"]
    }
  }

  mock_data "aws_vpc" {
    defaults = {
      id                   = "vpc-12345678"
      cidr_block           = "10.0.0.0/16"
      enable_dns_hostnames = true
      enable_dns_support   = true
    }
  }
}
```

## Когда использовать подмену

**Подходит:**
- проверка логики Terraform, условий, выражений `for_each` и `count`;
- проверка преобразований переменных и расчёта выходных значений;
- локальная разработка без облачных учётных данных;
- быстрый цикл обратной связи в CI/CD.

**Не подходит:**
- проверка реального поведения API провайдера;
- проверка побочных эффектов настоящего создания ресурсов;
- сквозное интеграционное тестирование.

## Ограничения

- **Только режим плана** — подмена не работает с `command = apply`.
- Значения подмены могут не отражать реальные вычисляемые значения атрибутов.
- Подмену нужно обновлять вручную при изменении схем провайдеров.
- Нельзя проверить реальные зависимости ресурсов и тайминги.
