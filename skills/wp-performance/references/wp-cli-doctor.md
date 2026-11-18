# WP-CLI doctor (`wp doctor`)

Используй это для быстрых проверок готовности к работе.

## Установка (если отсутствует)

- `wp package install wp-cli/doctor-command`

Документация:

- Проверки по умолчанию: https://make.wordpress.org/cli/handbook/doctor-default-checks/
- Настройка проверок: https://make.wordpress.org/cli/handbook/guides/doctor/doctor-customize-config/

## Рекомендуемое использование

- `wp doctor check --all` — выполнить все зарегистрированные проверки;
- `wp doctor check autoload-options-size constant-savequeries-falsy constant-wp-debug-falsy` —
  прогон, сфокусированный на производительности;
- `wp doctor check --all --spotlight` — показать только предупреждения и ошибки;
- `wp doctor list` — посмотреть доступные проверки.

`wp doctor check` требует либо `--all`, либо хотя бы одно имя проверки; без того и другого он
завершается с сообщением «Please specify one or more checks, or use --all.»

Особенно важно для производительности:

- `autoload-options-size` — порог автозагружаемых опций;
- `constant-savequeries-falsy` и `constant-wp-debug-falsy` — избегай дорогих по
  производительности флагов отладки в рабочем окружении;
- проверки cron (число задач и дубликаты).
