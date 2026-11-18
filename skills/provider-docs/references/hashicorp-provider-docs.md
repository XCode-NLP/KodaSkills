# Справочник по документации провайдеров HashiCorp

Источник истины для этого навыка:
- https://developer.hashicorp.com/terraform/registry/providers/docs

## Основные правила

- Публикуй документацию провайдера в Terraform Registry через `tfplugindocs`.
- Генерируй документацию провайдера из описаний схемы и markdown-шаблонов.
- Храни шаблоны в директории `docs/` репозитория с ожидаемыми соглашениями об именовании.
- Держи теги выпусков и метаданные манифеста валидными, чтобы Registry мог отрисовать и показать документацию.

## Пути шаблонов

Используй эти пути шаблонов, когда соответствующие объекты провайдера существуют:

- `docs/index.md.tmpl`
- `docs/data-sources/<name>.md.tmpl`
- `docs/resources/<name>.md.tmpl`
- `docs/ephemeral-resources/<name>.md.tmpl`
- `docs/list-resources/<name>.md.tmpl`
- `docs/functions/<name>.md.tmpl`
- `docs/actions/<name>.md.tmpl`
- `docs/guides/<name>.md.tmpl`

Registry отрисовывает страницы действий из `docs/actions/<action>.md`, а
`tfplugindocs` генерирует документацию действий (включая отсутствующие каркасы
шаблонов) начиная с Terraform v1.14.0+. Файлы примеров действий следуют
соглашению `examples/actions/<action_type>/action*.tf`.

## Соглашения о файлах примеров

Держи примеры HCL в директории `examples/` и подключай их в шаблоны,
а не встраивай HCL в файлы `.tmpl`:

```
examples/
├── provider/provider.tf                      # provider block for the index page only
├── resources/<type>/resource.tf              # picked up by generated templates
├── data-sources/<type>/data-source.tf
└── actions/<type>/action.tf
```

- **Один пример на файл**, подключается из шаблонов через
  `{{ tffile "examples/resources/examplecloud_widget/resource.tf" }}` —
  именованные варианты получают собственные файлы (`resource-with-tags.tf`), каждый
  под своим заголовком в шаблоне.
- **Никаких блоков `terraform`, `provider` и `output`** в примерах ресурсов,
  источников данных и действий. Ограничения версий и конфигурация провайдера
  относятся только к индексной странице провайдера; выходные значения отвлекают
  от документируемого объекта. (Единственное исключение —
  `examples/provider/provider.tf`, который существует, чтобы показать конфигурацию
  провайдера.)
- Держи каждый пример минимальным, запускаемым и отформатированным через
  `terraform fmt` — сгенерированная документация выводит файл дословно.

## Процесс генерации

HashiCorp рекомендует подключать запуск генератора через `go generate`:

```go
//go:generate go run github.com/hashicorp/terraform-plugin-docs/cmd/tfplugindocs generate --provider-name <provider_name>
```

Запускай из корня репозитория:

```bash
go generate ./...
```

Альтернативный прямой запуск:

```bash
go run github.com/hashicorp/terraform-plugin-docs/cmd/tfplugindocs generate --provider-name <provider_name>
```

## Страницы действий

Структура повторяет самый крупный рабочий пример, terraform-provider-aws
(`website/docs/actions/` — там написано вручную, потому что этот провайдер старше
поддержки действий в `tfplugindocs`; новые провайдеры должны генерировать):

- Одна страница на действие. В H1 префикс `Action:` — `# Action: examplecloud_restart_widget` —
  так же, как `# Resource:` и `# Data Source:` на соседних страницах.
- Вступительный абзац говорит, что делает действие и синхронное оно или
  асинхронное, затем ссылается на документацию вышестоящего сервиса для
  операции, которую оно вызывает.
- `## Example Usage` начинается с `### Basic Usage` и должен показывать **обе**
  половины использования действия: блок `action` и привязку на стороне ресурса
  `lifecycle { action_trigger { ... } }` — пример действия без триггера
  не запускается:

  ```terraform
  action "examplecloud_restart_widget" "example" {
    config {
      widget_id = examplecloud_widget.example.id
    }
  }

  resource "terraform_data" "trigger" {
    lifecycle {
      action_trigger {
        events  = [after_create, after_update]
        actions = [action.examplecloud_restart_widget.example]
      }
    }
  }
  ```

- `## Argument Reference` перечисляет аргументы `config` (либо плоско, либо
  разбитыми на группы обязательных и необязательных). **Никакого раздела
  атрибутов и выходных значений** — действия не создают состояния, а такой раздел
  вводил бы читателей в заблуждение.
- Соглашения о врезках (пока действия остаются экспериментальными):
  - `~> **Note:**` для предупреждения о статусе предпросмотра, например «`<action>` находится в alpha.
    Его интерфейс и поведение могут меняться по мере развития возможности,
    возможны ломающие изменения.»
  - `!> **Warning:**`, когда действие вызывает изменения, которые Terraform не
    согласует (например, оно изменяет ресурс, чьи атрибуты состояния будут
    устаревшими до следующего обновления) — назови затронутый атрибут и
    последствие.
- Если репозиторий ведёт заметки о выпуске через go-changelog, новые действия
  используют тип записи `release-note:new-action`.

## Ограничения выпуска и публикации

- Используй теги семантических версий с префиксом `v`.
- Создавай теги из ветки по умолчанию.
- Держи `terraform-registry-manifest.json` в корне репозитория.
- Учитывай, что документация появляется в Registry по версии провайдера после публикации выпуска.

## Предпросмотр и разбор проблем

- При необходимости используй процесс предпросмотра HashiCorp, чтобы проверить отрисовку до выпуска.
- Если документация в Registry отсутствует или устарела, проверь:
  - именование тега и ветку, из которой он создан;
  - наличие и валидность файла манифеста;
  - статус публикации версии провайдера.

## Связанные канонические страницы

- Руководство по документации провайдеров:
  - https://developer.hashicorp.com/terraform/registry/providers/docs
- Исходники и использование Terraform Plugin Docs (`tfplugindocs`):
  - https://github.com/hashicorp/terraform-plugin-docs
