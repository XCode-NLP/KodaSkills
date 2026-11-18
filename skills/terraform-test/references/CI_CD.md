# Интеграция с CI/CD

## GitHub Actions

```yaml
name: Terraform Tests

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.0

      - run: terraform fmt -check -recursive
      - run: terraform init
      - run: terraform validate
      - name: Run unit tests (plan mode, no credentials needed)
        run: terraform test -filter=unit_test -verbose

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.0

      - run: terraform init
      - name: Run integration tests
        run: terraform test -filter=integration_test -verbose
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```

## GitLab CI

```yaml
stages:
  - validate
  - test

terraform-unit-tests:
  image: hashicorp/terraform:1.9
  stage: validate
  before_script:
    - terraform init
  script:
    - terraform fmt -check -recursive
    - terraform validate
    - terraform test -filter=unit_test -verbose

terraform-integration-tests:
  image: hashicorp/terraform:1.9
  stage: test
  before_script:
    - terraform init
  script:
    - terraform test -filter=integration_test -verbose
  only:
    - main
```

## Рекомендуемая стратегия в CI

- Запускай модульные тесты (режим плана и тесты с подменой) на каждом pull request — быстро, без учётных данных.
- Запускай интеграционные тесты только при слиянии в main или по ночам — нужны облачные учётные данные.
- Используй `-filter=unit_test` и `-filter=integration_test`, чтобы разделять типы тестов по соглашению об именовании.
- Храни облачные учётные данные в секретах CI, никогда в коде.
