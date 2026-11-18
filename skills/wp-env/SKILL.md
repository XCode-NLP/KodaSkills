---
name: wp-env
description: "Используй при настройке, конфигурировании и отладке локального окружения разработки WordPress через @wordpress/env (wp-env). Срабатывает на упоминания wp-env, локальной разработки WordPress, WordPress в Docker или просьб запустить, остановить и настроить локальный экземпляр WordPress."
license: GPL-2.0
compatibility: "Рассчитано на WordPress 7.0+ (PHP 7.4.0+). Нужны Docker и Node.js 18.12+."
metadata:
  author: wordpress
  source: https://github.com/wordpress/agent-skills
---

# @wordpress/env (wp-env)

Локальное окружение разработки WordPress на Docker, работающее без конфигурации: для
плагинов, тем и ядра.

## Когда использовать

- Пользователь просит настроить локальное окружение разработки WordPress.
- В проекте есть файл `.wp-env.json`.
- Пользователь упоминает `wp-env`, `@wordpress/env` или разработку WordPress в Docker.
- Пользователь хочет локально запускать команды WP-CLI, тесты PHPUnit или отлаживать
  через Xdebug.
- Разбор проекта определил плагин или тему, которым нужен локальный экземпляр
  WordPress.

**wp-env или wp-playground?** Для быстрого локального WordPress по умолчанию
предпочитай навык **wp-playground**: он быстрее, одноразовый и не требует Docker.
Используй **wp-env**, когда задача действительно этого требует:

- в репозитории уже есть `.wp-env.json`;
- нужна настоящая база MySQL (PHPUnit против базы, команды `wp db`, данные, которые
  переживают перезапуск);
- внутри окружения нужно выполнять произвольные команды (доступ к оболочке,
  Composer, полный WP-CLI через `wp-env run`);
- это исходники ядра WordPress или Gutenberg;
- пользователь явно просит wp-env или Docker.

wp-env умеет работать и без Docker, используя Playground как среду выполнения
(`npx @wordpress/env start --runtime=playground`, экспериментально). Это всё ещё
wp-env с тем же `.wp-env.json`, поэтому считай такой режим запасным вариантом без
Docker для проекта, где конфигурация wp-env уже есть, а не третьей альтернативой. Он
заменяет MySQL на SQLite и лишает `wp-env run` и отдельного окружения тестов — то
есть большей части причин выбирать wp-env. Для быстрого WordPress без Docker и без
конфигурации wp-env используй напрямую навык **wp-playground**.

## Что нужно на входе

1. **Состояние Docker** — убедись, что Docker установлен и запущен: `docker info`
2. **Версия Node.js** — должна быть >= 18.12.0: `node -v`
3. **Тип проекта** — плагин, тема или полный сайт (проверь `.wp-env.json`, заголовки
   плагина или заголовки темы в `style.css`).
4. **Существующая конфигурация** — прочитай `.wp-env.json` и
   `.wp-env.override.json`, если они есть.

## Порядок работы

### 1. Установи wp-env

```sh
# Глобально (рекомендуется)
npm -g install @wordpress/env

# Или локально в проект
npm i @wordpress/env --save-dev
# Затем используй: npx wp-env start
```

### 2. Запусти окружение

```sh
wp-env start
```

Учётные данные по умолчанию:

- **URL:** http://localhost:8888/wp-admin/
- **Имя пользователя:** `admin`
- **Пароль:** `password`

Частые параметры запуска:

- `wp-env start --update` — подтянуть свежие исходники и перенастроить;
- `wp-env start --xdebug` — включить Xdebug (режим отладки);
- `wp-env start --xdebug=profile,trace` — несколько режимов Xdebug;
- `wp-env start --auto-port` — найти свободные порты, если стандартные заняты.

### 3. Автоопределение (без файла конфигурации)

Если `.wp-env.json` нет, wp-env сканирует текущую директорию:

| Определённый тип | Как определяется | Автоконфигурация |
|--------------|-------------|-------------|
| Плагин | заголовок `Plugin Name:` в `.php`-файле в корне | `{ "plugins": ["."] }` |
| Тема | заголовок `Theme Name:` в `style.css` | `{ "themes": ["."] }` |
| Ядро | существует `wp-includes/version.php` | `{ "core": "." }` |

### 4. Настрой через `.wp-env.json`

Положи файл в корень проекта. Все поля необязательны.

```json
{
  "core": null,
  "phpVersion": "8.1",
  "plugins": [
    ".",
    "https://downloads.wordpress.org/plugin/akismet.zip",
    "WordPress/classic-editor"
  ],
  "themes": [],
  "port": 8888,
  "multisite": false,
  "phpmyadmin": false,
  "config": {
    "WP_DEBUG": true,
    "SCRIPT_DEBUG": true
  },
  "mappings": {
    "wp-content/mu-plugins": "./mu-plugins"
  },
  "lifecycleScripts": {
    "afterStart": "wp-env run cli wp rewrite structure /%postname%/"
  }
}
```

#### Форматы строк-источников (для `core`, `plugins`, `themes`, `mappings`)

| Формат | Пример |
|--------|---------|
| Локальный путь | `"."`, `"./path"`, `"../path"` |
| Сокращение GitHub | `"WordPress/classic-editor"`, `"owner/repo#branch"` |
| URL ZIP-архива | `"https://downloads.wordpress.org/plugin/akismet.zip"` |
| Git по SSH | `"ssh://user@host/repo.git#ref"` |

**ЛОВУШКА:** короткие слаги плагинов и тем с WordPress.org (например, `"akismet"`)
НЕ работают. Указывай полный URL ZIP-архива.

#### Локальные переопределения через `.wp-env.override.json`

Создай `.wp-env.override.json` рядом с `.wp-env.json` для личных настроек (файл
добавляется в `.gitignore`). Объединяются только `config` и `mappings`, все
остальные поля (включая массивы `plugins` и `themes`) **полностью заменяют**
базовые.

### 5. Выполняй команды в контейнерах

```sh
# Команды WP-CLI
wp-env run cli wp user list
wp-env run cli wp plugin list
wp-env run cli wp option update blogname "My Site"
wp-env run cli "wp rewrite structure /%postname%/"

# Команды в конкретной директории
wp-env run cli --env-cwd=wp-content/plugins/my-plugin composer install

# Тесты PHPUnit
wp-env run cli --env-cwd=wp-content/plugins/my-plugin vendor/bin/phpunit

# Передача флагов через разделитель --
wp-env run cli php -- --version

# Доступ к MySQL
wp-env run mysql mysql -- --user=root --password=password wordpress
```

Доступные контейнеры: `mysql`, `wordpress`, `cli`, `composer`, `phpmyadmin`.

### 6. Управляй окружением

```sh
wp-env stop                    # Остановить и освободить порты
wp-env reset development       # Сбросить базу разработки (тестовая сохраняется)
wp-env reset all               # Сбросить все базы
wp-env logs                    # Поток логов PHP и Docker
wp-env logs --no-watch         # Вывести логи и выйти
wp-env status                  # Показать URL, порты, конфигурацию
wp-env status --json           # Статус в машиночитаемом виде
wp-env cleanup                 # Удалить контейнеры и тома (образы остаются)
wp-env destroy                 # Удалить всё, включая образы
```

### 7. Настройка Xdebug

```sh
wp-env start --xdebug          # Включить режим отладки
wp-env start --xdebug=coverage # Для покрытия кода
wp-env start                   # Отключить Xdebug (перезапуск без флага)
```

Режимы: `debug`, `profile`, `trace`, `develop`, `coverage`.

IDE слушает порт **9003**. В `launch.json` для VS Code нужно:

```json
{
  "type": "php",
  "request": "launch",
  "name": "Listen for Xdebug",
  "port": 9003,
  "pathMappings": {
    "/var/www/html/wp-content/plugins/your-plugin": "${workspaceFolder}"
  }
}
```

### 8. Мультисайт

```json
{ "multisite": true, "plugins": ["."] }
```

## Проверка

- [ ] `wp-env status` показывает запущенные контейнеры с правильными портами
- [ ] `http://localhost:8888/wp-admin/` открывает админку WordPress
- [ ] `wp-env run cli wp plugin list` показывает ожидаемые плагины
- [ ] разрабатываемый плагин или тема видны в админке WordPress
- [ ] сброс базы работает: `wp-env reset development`

## Сбои и отладка

| Симптом | Причина | Исправление |
|---------|-------|-----|
| «Cannot connect to Docker daemon» | Docker не запущен | Запусти Docker Desktop |
| «Port 8888 already in use» | Конфликт портов | Используй `--auto-port` или задай свой `port` в `.wp-env.json` |
| Плагин не появляется | в основном PHP-файле нет заголовка `Plugin Name:` | Добавь стандартный комментарий-заголовок плагина |
| «Could not find a valid source» | неверная строка-источник в конфигурации | Для плагинов с wp.org указывай полный URL ZIP, а не короткий слаг |
| Окружение устарело после изменения исходников | закэшированные тома Docker | `wp-env start --update` или `wp-env destroy && wp-env start` |
| Белый экран или ошибки PHP | повреждённая база | `wp-env reset all && wp-env start` |
| Переопределение не действует | неверное поведение объединения | `plugins` и `themes` в файле переопределения **заменяют** базовые массивы; объединяются только `config` и `mappings` |
| Окружение тестов недоступно | неверный порт | Окружение тестов по умолчанию работает на порту 8889 |
| Xdebug не подключается | IDE не слушает или неверный порт | Убедись, что IDE слушает порт 9003 с правильным `pathMappings` |
| Ошибка прав при глобальной установке через npm | Node установлен в системный путь | Используй `nvm` или ставь локально: `npm i -D @wordpress/env` и запускай через `npx wp-env` |

## Когда эскалировать

- проблемы Docker вне зоны ответственности wp-env (сеть, место на диске, бэкенд
  WSL2);
- собственные конфигурации Docker Compose, конфликтующие с wp-env;
- интеграция в конвейер CI/CD, требующая нестандартных настроек Docker;
- среда выполнения WordPress Playground (`--runtime=playground`) экспериментальна и
  поддерживает не все возможности.

## Ссылки

- [Официальная документация](https://developer.wordpress.org/block-editor/reference-guides/packages/packages-env/)
- [Руководство по началу работы](https://developer.wordpress.org/block-editor/getting-started/devenv/get-started-with-wp-env/)
- [Исходный код](https://github.com/WordPress/gutenberg/tree/trunk/packages/env)
