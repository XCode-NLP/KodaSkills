---
name: notion-cli
description: "Работа с API Notion через командную строку Notion (`ntn`), управление воркерами и загрузка файлов. Используй, когда пользователь просит вызвать API Notion, развернуть воркер, загрузить файл, создать страницу, запросить базу данных или выполнить любую задачу с командой `ntn`."
license: MIT
metadata:
  author: makenotion
  source: https://github.com/makenotion/skills
  tags: [notion, cli, api]
---

# Командная строка Notion

## Сначала посмотри справку

Командная строка сама себя документирует. Всегда предпочитай запускать эти команды, а не угадывать синтаксис или полагаться на заученные знания:

- `ntn api ls` — перечислить все публичные эндпоинты API.
- `ntn api <path> --help` — показать методы, ссылки на документацию и примеры для эндпоинта.
- `ntn api <path> --docs` — вывести полную официальную документацию по эндпоинту.
- `ntn api <path> --spec` — вывести сокращённый фрагмент OpenAPI (полезно для понимания схем запроса и ответа).
- `ntn pages get <page-id>` — получить страницу в виде Markdown. Используй это для чтения содержимого страницы.
- `ntn <command> --help` — справка по любой команде и подкоманде.

## Установка

```bash
curl -fsSL https://ntn.dev | bash
```

## Аутентификация

- Командная строка автоматически использует `NOTION_API_TOKEN`, если он задан.
- Сначала проверь `NOTION_API_TOKEN`. Если он уже задан, используй его, а не предлагай пользователю выполнить `ntn login`.
- `ntn login` / `ntn logout` — вход и выход командной строки (используй, только если не применяется `NOTION_API_TOKEN`). Для `ntn login` пользователю нужно открыть ссылку в браузере.

## `ntn api`

Полный синтаксис — в `ntn api --help`. Кратко:

```bash
# GET с параметром запроса
ntn api v1/users page_size==100

# POST с полями тела прямо в команде
ntn api v1/pages parent[page_id]=abc123

# POST с телом в JSON
ntn api v1/pages -d '{"parent":{"page_id":"abc123"}}'
```

Метод определяется автоматически (GET по умолчанию, POST при наличии тела). Переопределить можно через `-X METHOD`.

### Markdown для страниц и комментариев

Для содержимого страниц в Markdown предпочитай `ntn pages create` и `ntn pages update`. Поле `markdown` используй при создании и изменении комментариев через `ntn api`.

```bash
# Комментарий с markdown
ntn api v1/comments -d '{"parent":{"page_id":"abc123"},"markdown":"Здесь [ссылка](https://example.com) и **жирный текст**."}'

# Страница с телом в markdown
ntn pages create --parent page:abc123 --content '## Заголовок\n\nНекоторое *оформленное* содержимое.'
```

Поле `markdown` поддерживает встроенное оформление (жирный, курсив, код, ссылки и так далее). К `rich_text` прибегай, только если нужны возможности, которых нет в Markdown (например, упоминания, свои эмодзи или цвета).

## `ntn files`

Удобная обёртка над API загрузки файлов.

```bash
ntn files create < image.png
ntn files create --external-url https://example.com/photo.png
ntn files list
ntn files get <upload-id>
```

## `ntn workers`

Управление воркерами Notion (развёртывание, список, выполнение и так далее). Подкоманды — в `ntn workers --help`.

```bash
ntn workers new my-worker        # создать заготовку нового проекта
ntn workers deploy               # развернуть из текущего каталога
ntn workers ls                   # список воркеров
ntn workers exec <capability>    # выполнить возможность
```
