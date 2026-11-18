# Дерево решений маршрутизатора (v1)

Это лёгкое руководство по маршрутизации. Оно предполагает, что сначала можно
запустить `wp-project-triage`.

## Шаг 1. Определи тип репозитория (по выводу разбора)

Используй `triage.project.kind` и самые сильные признаки:

- `wp-core` → работа с исходниками ядра WordPress (патчи ядра, PHPUnit, инструменты
  сборки);
- `wp-site` → репозиторий полного сайта (есть `wp-content`; изменения могут
  затрагивать тему и плагины);
- `wp-block-theme` → процессы блочной темы: `theme.json`, шаблоны, паттерны;
- `wp-theme` → процессы классической темы (PHP-шаблоны, `functions.php`,
  `style.css`);
- `wp-block-plugin` → разработка блоков Gutenberg в плагине (`block.json`, сборка);
- `wp-plugin` / `wp-mu-plugin` → процессы плагина (хуки, админка, настройки, cron,
  REST, безопасность);
- `gutenberg` → процессы монорепозитория Gutenberg (пакеты, инструменты,
  документация).

Если подходит несколько типов, выбирай самый конкретный:
`gutenberg` > `wp-core` > `wp-site` > `wp-block-theme` > `wp-block-plugin` >
`wp-theme` > `wp-plugin`.

## Шаг 2. Выбери маршрут по намерению пользователя (ключевые слова)

Маршрутизируй по намерению, даже если тип репозитория широкий (например,
`wp-site`):

- **Interactivity API / директивы `data-wp-*` / `@wordpress/interactivity` /
  `viewScriptModule`**
  - маршрут → `wp-interactivity-api`.
- **Проектирование, реализация или проверка схем, CRUD-поведения или прав
    доступа возможности (ability)**
  - маршрут → `wp-ability-development`.
- **Регистрация, публикация или использование Abilities API /
    `wp_register_ability` / `wp-abilities/v1` / `@wordpress/abilities`**
  - маршрут → `wp-abilities-api`.
- **Неоднозначные запросы про WordPress Playground**
  - маршрут → `wp-playground`, затем следуй его обёртке маршрутизации.
- **Blueprint JSON / схема Blueprint / шаги Blueprint / наборы Blueprint**
  - маршрут → `blueprint`.
- **`@wp-playground/cli` / server / run-blueprint / build-snapshot / auto-mount /
  Xdebug**
  - маршрут → `wp-playground`, затем прочитай `references/cli.md` или
    `references/debugging.md`.
- **playground.wordpress.net / редактор Blueprint / ссылки для публикации /
  Playground только в браузере**
  - маршрут → `wp-playground`, затем прочитай `references/website.md`.
- **Блоки / `block.json` / `registerBlockType` / атрибуты / сериализация при
  сохранении**
  - маршрут → `wp-block-development`.
- **`theme.json` / глобальные стили / `templates/*.html` / `patterns/`**
  - маршрут → `wp-block-themes`.
- **Плагины / хуки / хук активации / удаление / Settings API / страницы админки**
  - маршрут → `wp-plugin-development`.
- **Эндпоинт REST / `register_rest_route` / `permission_callback`**
  - маршрут → `wp-rest-api`.
- **WP-CLI / `wp-cli.yml` / команды**
  - маршрут → `wp-wpcli-and-ops`.
- **Инструменты сборки / `@wordpress/scripts` / webpack / Vite / npm-скрипты**
  - маршрут → `wp-build-tooling` (планируется).
- **Тестирование / PHPUnit / wp-env / Playwright**
  - маршрут → `wp-testing` (планируется).
- **PHPStan / статический анализ / `phpstan.neon` / `phpstan-baseline.neon`**
  - маршрут → `wp-phpstan`.
- **Производительность / кэширование / профилирование запросов / медленный
  редактор**
  - маршрут → `wp-performance`.
- **Безопасность / nonce / права / санитизация и экранирование / загрузки файлов**
  - маршрут → `wp-security` (планируется).

## Шаг 3. Контрольный список ограничений (всегда)

- Перед тем как предлагать команды, проверь, какие инструменты действительно есть
  (Composer, npm/yarn/pnpm).
- Если в проекте уже есть скрипты линтера и тестов, предпочитай их.
- Если ограничения по версиям определить нельзя, спроси целевые версии ядра WP и
  PHP.
