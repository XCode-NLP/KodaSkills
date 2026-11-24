---
name: blueprint
description: "Используй, когда результат работы — JSON Blueprint для WordPress Playground или набор Blueprint: создание, правка, проверка, валидация ключей схемы, выбор шагов и ресурсов, отладка файлов Blueprint. Если нужно только запустить или опубликовать окружение Playground, используй wp-playground."
license: GPL-2.0
compatibility: "WordPress 7.0+, PHP 7.4.0+. Дополнительно нужен Playground CLI или браузер."
metadata:
  author: wordpress
  source: https://github.com/wordpress/agent-skills
  tags: [wordpress, json, blueprint]
---

# Blueprint для WordPress Playground

## Обзор

Blueprint — это JSON-файл, который декларативно настраивает экземпляр WordPress
Playground: устанавливает плагины и темы, задаёт параметры, выполняет PHP и SQL,
работает с файлами и многое другое.

**Основной принцип:** Blueprint — это доверенное описание только на JSON. Никакого
произвольного JavaScript. Оно работает в браузере, в Node.js и в CLI.

## Шаблон для быстрого старта

```json
{
  "$schema": "https://playground.wordpress.net/blueprint-schema.json",
  "landingPage": "/wp-admin/",
  "preferredVersions": { "php": "8.3", "wp": "latest" },
  "steps": [{ "step": "login" }]
}
```

## Свойства верхнего уровня

Все необязательны. Допускаются только документированные ключи — схема отклоняет
неизвестные свойства.

| Свойство | Тип | Замечания |
|----------|------|-------|
| `$schema` | string | Всегда `"https://playground.wordpress.net/blueprint-schema.json"` |
| `landingPage` | string | Относительный путь, например `/wp-admin/` |
| `description` | string | Устаревшее необязательное описание верхнего уровня. Для новых Blueprint предпочитай `meta.description` |
| `meta` | object | `{ title, author, description?, categories? }` — `title` и `author` обязательны |
| `preferredVersions` | object | `{ php, wp }` — оба обязательны, если объект указан |
| `features` | object | `{ networking?: boolean, intl?: boolean }` — **только** эти два ключа, ничего больше. Сеть по умолчанию `true` |
| `phpExtensionBundles` | any | Устарело и больше не используется; схема не ограничивает значение и советует удалить его из Blueprint |
| `extraLibraries` | array | `["wp-cli"]` — добавляется автоматически, если есть шаг `wp-cli` |
| `constants` | object | Сокращение для `defineWpConfigConsts`. Значения: строка, логическое значение, число |
| `plugins` | array | Сокращение для шагов `installPlugin`. Строки — слаги с wp.org |
| `siteOptions` | object | Сокращение для `setSiteOptions` |
| `login` | boolean или object | `true` = вход как администратор. Объект = `{ username?, password? }` (по умолчанию `"admin"` и `"password"`) |
| `steps` | array | Основной конвейер выполнения. Запускается после сокращений |

### Значения preferredVersions

- **php:** только major.minor: `"7.4"`, `"8.0"`, `"8.1"`, `"8.2"`, `"8.3"`, `"8.4"`,
  `"8.5"` или `"latest"`. Версии с патчем вроде `"7.4.1"` недопустимы. Актуальный
  список поддерживаемых версий смотри в схеме.
- **wp:** последние мажорные версии, `"latest"`, `"beta"`, `"nightly"`/`"trunk"` или
  URL собственного zip-архива. Схема также принимает `false` для Playground только на
  PHP; не сочетайте `wp: false` с полями, относящимися к WordPress, — `plugins`,
  `siteOptions`, `login` и шагами, которые работают только с WordPress.

### Сокращения и шаги

Сокращения (`login`, `plugins`, `siteOptions`, `constants`) разворачиваются и
добавляются перед `steps` в **неопределённом порядке**. Если важен порядок
выполнения, используй явные шаги.

## Ссылки на ресурсы

Ресурсы говорят Playground, где найти файлы. Их используют `installPlugin`,
`installTheme`, `writeFile`, `writeFiles`, `importWxr` и другие шаги.

| Тип ресурса | Обязательные поля | Пример |
|--------------|----------------|---------|
| `wordpress.org/plugins` | `slug` | `{ "resource": "wordpress.org/plugins", "slug": "woocommerce" }` |
| `wordpress.org/themes` | `slug` | `{ "resource": "wordpress.org/themes", "slug": "astra" }` |
| `url` | `url` | `{ "resource": "url", "url": "https://example.com/plugin.zip" }` |
| `git:directory` | `url`, `ref` | см. ниже |
| `literal` | `name`, `contents` | `{ "resource": "literal", "name": "file.txt", "contents": "hello" }` |
| `literal:directory` | `name`, `files` | см. ниже |
| `bundled` | `path` | ссылка на файл внутри набора Blueprint, например `{ "resource": "bundled", "path": "/plugin.zip" }` |
| `zip` | `inner` | оборачивает другой ресурс в ZIP — нужен, когда шаг ждёт zip, а источник им не является (например, обёртка для ресурса `url`, указывающего на сырую директорию) |

### git:directory — установка из GitHub

```json
{
  "resource": "git:directory",
  "url": "https://github.com/WordPress/gutenberg",
  "ref": "trunk",
  "refType": "branch",
  "path": "/"
}
```

- Если в `ref` указано имя ветки или тега, ты **обязан** задать `refType`
  (`"branch"` | `"tag"` | `"commit"` | `"refname"`). Без него надёжно разрешается
  только `"HEAD"`.
- `path` выбирает поддиректорию (по умолчанию корень репозитория).

### literal:directory — деревья файлов прямо в описании

```json
{
  "resource": "literal:directory",
  "name": "my-plugin",
  "files": {
    "plugin.php": "<?php /* Plugin Name: My Plugin */ ?>",
    "includes": {
      "helper.php": "<?php // helper code ?>"
    }
  }
}
```

- В `files` поддиректории задаются вложенными объектами: ключи — имена файлов или
  директорий, значения — **простые строки** (содержимое файла) или **объекты**
  (поддиректории). Никогда не используй в значениях ссылки на ресурсы.
- **НЕ используй разделители пути в ключах** (например, `"includes/helper.php"`
  неверно — нужен вложенный объект `"includes": { "helper.php": "..." }`).

## Справочник шагов

Каждый шаг требует `"step": "<имя>"`. Любой шаг может дополнительно содержать
`"progress": { "weight": 1, "caption": "Installing..." }` для индикации в интерфейсе.

### Установка плагинов и тем

```json
{
  "step": "installPlugin",
  "pluginData": { "resource": "wordpress.org/plugins", "slug": "gutenberg" },
  "options": { "activate": true, "targetFolderName": "gutenberg" },
  "ifAlreadyInstalled": "overwrite"
}
```

```json
{
  "step": "installTheme",
  "themeData": { "resource": "wordpress.org/themes", "slug": "twentytwentyfour" },
  "options": { "activate": true, "importStarterContent": true },
  "ifAlreadyInstalled": "overwrite"
}
```

- Используй `pluginData` и `themeData`, а **НЕ** устаревшие `pluginZipFile` и
  `themeZipFile`.
- `pluginData` и `themeData` принимают любую ссылку на файл или директорию: URL
  zip-архива, слаг `wordpress.org/plugins`, `git:directory` или `literal:directory`
  (обёртка `zip` не нужна).
- `options.activate` управляет активацией. Отдельные шаги `activatePlugin` и
  `activateTheme` при использовании `installPlugin` и `installTheme` не нужны.
- `ifAlreadyInstalled`: `"overwrite"` | `"skip"` | `"error"`

### Активация (отдельным шагом)

Нужна только для плагинов и тем, которые уже лежат на диске (например, после
`writeFile` или `writeFiles`):

```json
{ "step": "activatePlugin", "pluginPath": "my-plugin/my-plugin.php" }
```
```json
{ "step": "activateTheme", "themeFolderName": "twentytwentyfour" }
```

### Работа с файлами

```json
{ "step": "writeFile", "path": "/wordpress/wp-content/mu-plugins/custom.php", "data": "<?php // code" }
```

`data` принимает простую строку (как выше) или ссылку на ресурс (например,
`{ "resource": "url", "url": "https://..." }`).

```json
{
  "step": "writeFiles",
  "writeToPath": "/wordpress/wp-content/plugins/",
  "filesTree": {
    "resource": "literal:directory",
    "name": "my-plugin",
    "files": {
      "plugin.php": "<?php\n/*\nPlugin Name: My Plugin\n*/",
      "includes": {
        "helpers.php": "<?php // helpers"
      }
    }
  }
}
```

**`writeFiles` требует ссылку на директорию** (`literal:directory` или
`git:directory`) в `filesTree`, а не простой объект.

Другие операции с файлами: `mkdir`, `cp`, `mv`, `rm`, `rmdir`, `unzip`.

### Выполнение кода

**runPHP:**
```json
{ "step": "runPHP", "code": "<?php require '/wordpress/wp-load.php'; update_option('key', 'value');" }
```
**ЛОВУШКА:** чтобы использовать любые функции WordPress, нужно подключить
`require '/wordpress/wp-load.php';`.

**wp-cli:**
```json
{ "step": "wp-cli", "command": "wp post create --post_type=page --post_title='Hello' --post_status=publish" }
```
Имя шага — `wp-cli` (через дефис), а НЕ `cli` или `wpcli`.

**runSql:**
```json
{ "step": "runSql", "sql": { "resource": "literal", "name": "q.sql", "contents": "UPDATE wp_options SET option_value='val' WHERE option_name='key';" } }
```

### Настройка сайта

```json
{ "step": "setSiteOptions", "options": { "blogname": "My Site", "blogdescription": "A tagline" } }
```
```json
{ "step": "defineWpConfigConsts", "consts": { "WP_DEBUG": true } }
```
```json
{ "step": "setSiteLanguage", "language": "en_US" }
```
```json
{ "step": "defineSiteUrl", "siteUrl": "https://example.com" }
```

### Прочие шаги

| Шаг | Ключевые свойства |
|------|---------------|
| `login` | `username?`, `password?` (по умолчанию `"admin"` и `"password"`) |
| `enableMultisite` | (обязательных свойств нет) |
| `importWxr` | `file` (ссылка на файл) |
| `importThemeStarterContent` | `themeSlug?` |
| `importWordPressFiles` | `wordPressFilesZip`, `pathInZip?` — импортирует целую директорию WordPress из zip-архива |
| `request` | `request: { url, method?, headers?, body? }` |
| `updateUserMeta` | `userId`, `meta` |
| `runWpInstallationWizard` | `options?` — запускает мастер установки WP с заданными параметрами |
| `resetData` | (свойств нет) |

## Частые шаблоны

### mu-плагин прямо в описании (быстрый свой код)

```json
{
  "step": "writeFile",
  "path": "/wordpress/wp-content/mu-plugins/custom.php",
  "data": "<?php\n// mu-plugins load automatically — no activation needed, no require wp-load.php\nadd_filter('show_admin_bar', '__return_false');"
}
```

### Плагин из нескольких файлов прямо в описании

```json
{
  "step": "writeFiles",
  "writeToPath": "/wordpress/wp-content/plugins/",
  "filesTree": {
    "resource": "literal:directory",
    "name": "my-plugin",
    "files": {
      "my-plugin.php": "<?php\n/*\nPlugin Name: My Plugin\n*/\nrequire __DIR__ . '/includes/main.php';",
      "includes": {
        "main.php": "<?php // main logic"
      }
    }
  }
}
```

Затем активируй его отдельным шагом:

```json
{ "step": "activatePlugin", "pluginPath": "my-plugin/my-plugin.php" }
```

### Плагин из ветки GitHub

```json
{
  "step": "installPlugin",
  "pluginData": {
    "resource": "git:directory",
    "url": "https://github.com/user/repo",
    "ref": "feature-branch",
    "refType": "branch",
    "path": "/"
  }
}
```

## Частые ошибки

| Ошибка | Правильно |
|---------|---------|
| `pluginZipFile` / `themeZipFile` | `pluginData` / `themeData` |
| `"step": "cli"` | `"step": "wp-cli"` |
| плоский объект в `writeFiles.filesTree` | нужен ресурс `literal:directory` или `git:directory` |
| разделители пути в ключах `files` | используй вложенные объекты для поддиректорий |
| `runPHP` без `wp-load.php` | всегда `require '/wordpress/wp-load.php';` для функций WP |
| выдуманные ключи верхнего уровня | работают только документированные ключи — схема отклоняет неизвестные свойства |
| выдуманные прокси-URL для GitHub | используй тип ресурса `git:directory` |
| `refType` не указан при `ref` с ветвью или тегом | обязателен — без него работает только `"HEAD"` |
| ссылки на ресурсы в значениях `files` у `literal:directory` | значения должны быть простыми строками (содержимое) или объектами (поддиректории), но не ссылками на ресурсы |
| `features.debug` и другие выдуманные ключи возможностей | `features` поддерживает только `networking` и `intl` — для режима отладки используй `constants: { "WP_DEBUG": true }` |
| `require wp-load.php` в коде mu-плагина | нужно только в шагах `runPHP` — mu-плагины уже выполняются внутри WordPress |
| URL схемы с доменом `.org` | должен быть `playground.wordpress.net`, а не `playground.wordpress.org` |

## Полный справочник

Этот навык покрывает самые частые шаги и шаблоны. Полный API смотри здесь:

- **Документация Blueprint:** https://wordpress.github.io/wordpress-playground/blueprints
- **JSON-схема:** https://playground.wordpress.net/blueprint-schema.json

Дополнительные шаги, не описанные выше: `runPHPWithOptions` (запуск PHP с
собственными настройками `ini`), `runWpInstallationWizard`, а также типы ресурсов
`vfs` и `bundled` (для сложных сценариев встраивания).

## Наборы Blueprint

Набор — это самодостаточный пакет, который содержит `blueprint.json` и все ресурсы,
на которые он ссылается (плагины, темы, файлы WXR и т.п.). Вместо размещения ресурсов
на внешнем хостинге положи их рядом с Blueprint.

### Структура набора

```
my-bundle/
├── blueprint.json          ← должен лежать в корне
├── my-plugin.zip           ← заархивированная директория плагина
├── theme.zip
└── content/
    └── sample-content.wxr
```

Плагины и темы нужно заархивировать до сборки набора: `installPlugin` ждёт zip, а не
сырую директорию. Чтобы создать архив из директории плагина:

```bash
cd my-bundle
zip -r my-plugin.zip my-plugin/
```

### Ссылки на ресурсы набора

Используй тип ресурса `bundled`, чтобы сослаться на файлы внутри набора:

```json
{
  "step": "installPlugin",
  "pluginData": {
    "resource": "bundled",
    "path": "/my-plugin.zip"
  },
  "options": { "activate": true }
}
```

```json
{
  "step": "importWxr",
  "file": {
    "resource": "bundled",
    "path": "/content/sample-content.wxr"
  }
}
```

### Создание набора по шагам

1. Создай директорию набора и положи `blueprint.json` в её корень.
2. Напиши исходники плагина или темы в поддиректории (например,
   `my-plugin/my-plugin.php`).
3. Заархивируй директорию плагина: `zip -r my-plugin.zip my-plugin/`
4. Ссылайся на архив в `blueprint.json` через
   `{ "resource": "bundled", "path": "/my-plugin.zip" }`.

Полный пример — набор, устанавливающий собственный плагин:

```
dashboard-widget-bundle/
├── blueprint.json
├── dashboard-widget.zip        ← архив dashboard-widget/
└── dashboard-widget/           ← исходники плагина (оставлены для правок)
    └── dashboard-widget.php
```

```json
{
  "$schema": "https://playground.wordpress.net/blueprint-schema.json",
  "landingPage": "/wp-admin/",
  "preferredVersions": { "php": "8.3", "wp": "latest" },
  "steps": [
    { "step": "login" },
    {
      "step": "installPlugin",
      "pluginData": { "resource": "bundled", "path": "/dashboard-widget.zip" },
      "options": { "activate": true }
    }
  ]
}
```

### Способы распространения

| Формат | Как использовать |
|--------|-----------|
| ZIP-архив (удалённый) | Сайт: `https://playground.wordpress.net/?blueprint-url=https://example.com/bundle.zip` |
| ZIP-архив (локальный) | CLI: `npx @wp-playground/cli server --blueprint=./bundle.zip` |
| Локальная директория | CLI: `npx @wp-playground/cli server --blueprint=./my-bundle/ --blueprint-may-read-adjacent-files` |
| Директория в репозитории Git | укажи `blueprint-url` на директорию репозитория с `blueprint.json` |

**ЛОВУШКА:** наборам в виде локальной директории всегда нужен флаг
`--blueprint-may-read-adjacent-files`, иначе CLI не прочитает ресурсы набора. Без него
любая ссылка `"resource": "bundled"` завершится ошибкой «File not found». ZIP-наборам
этот флаг не нужен — все файлы внутри архива.

## Проверка Blueprint

### Blueprint прямо в ссылке (быстрая проверка, без набора)

Минифицируй JSON (без лишних пробелов), закодируй его один раз через
`encodeURIComponent()`, добавь префикс `https://playground.wordpress.net/#` и открой
URL в браузере:

```
https://playground.wordpress.net/#%7B%22%24schema%22%3A%22https%3A%2F%2Fplayground.wordpress.net%2Fblueprint-schema.json%22%2C%22preferredVersions%22%3A%7B%22php%22%3A%228.3%22%2C%22wp%22%3A%22latest%22%7D%2C%22steps%22%3A%5B%7B%22step%22%3A%22login%22%7D%5D%7D
```

Очень большие Blueprint могут превысить ограничение длины URL в браузере; тогда
используй CLI или размещённый URL Blueprint. Подробности про ссылки для публикации
см. в `wp-playground/references/website.md`.

### Проверка через локальный CLI

**Интерактивный сервер** (работает, пока его не остановят, открывается в браузере):
```bash
# Набор-директория — нужен --blueprint-may-read-adjacent-files
npx @wp-playground/cli server --blueprint=./my-bundle/ --blueprint-may-read-adjacent-files

# ZIP-набор — самодостаточен, дополнительные флаги не нужны
npx @wp-playground/cli server --blueprint=./bundle.zip
```

**Проверка без интерфейса** (выполняет Blueprint и завершается):
```bash
npx @wp-playground/cli run-blueprint --blueprint=./my-bundle/ --blueprint-may-read-adjacent-files
```

### Проверка через WordPress Playground

Для локальной проверки или проверки в браузере используй навык `wp-playground`. Для
проверки через CLI следуй `wp-playground/references/cli.md` с
`--blueprint=<path-or-url>`; для наборов-директорий передавай
`--blueprint-may-read-adjacent-files`.
