# Операции с плагинами и темами

Используй этот файл для установки, активации, обновления и просмотра состояния.

## Частые команды

- Плагины:
  - `wp plugin list`;
  - `wp plugin status <slug>`;
  - `wp plugin activate <slug>`;
  - `wp plugin deactivate <slug>`;
  - `wp plugin update --all`.
- Темы:
  - `wp theme list`;
  - `wp theme activate <slug>`;
  - `wp theme update --all`.

## Ограничения

- в рабочей среде избегай `update --all` без окна обслуживания;
- в сети сайтов активация плагина может быть для одного сайта или для всей сети,
  подтверди намерение.
