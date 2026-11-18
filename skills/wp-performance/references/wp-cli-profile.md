# Профилирование WP-CLI (`wp profile`)

Используй это, когда нужно пригодное к действию профилирование без браузера.

## Установка (если отсутствует)

`wp profile` поставляется отдельным пакетом WP-CLI:

- `wp package install wp-cli/profile-command`

Документация:

- https://wpcli.dev/docs/profile/stage
- https://wpcli.dev/docs/profile/hook
- https://wpcli.dev/docs/profile/eval

## Рекомендуемая последовательность

1. Обзор этапов:
   - `wp profile stage --fields=stage,time,cache_ratio [--url=<url>]`
2. Горячие точки хуков:
   - `wp profile hook --spotlight [--url=<url>]`
   - затем углубись в конкретный хук:
     - `wp profile hook init --spotlight [--url=<url>]`
3. Точечная оценка:
   - `wp profile eval 'do_action(\"init\");' --hook=init`

Советы:

- используй `--url`, чтобы профилировать поведение конкретного сайта или маршрута;
- используй `--skip-plugins` и `--skip-themes`, чтобы изолировать виновные компоненты (осторожно:
  поведение изменится).
