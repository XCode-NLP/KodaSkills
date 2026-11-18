# Server-Timing (Performance Lab)

Используй этот файл, когда можешь включить метрики Server-Timing и хочешь смотреть их только с
бэкенда через заголовки HTTP.

Плагин Performance Lab:

- https://wordpress.org/plugins/performance-lab/

Руководство по эталонным замерам:

- https://make.wordpress.org/performance/handbook/measuring-performance/benchmarking-server-timing/

Подход только с бэкенда:

- включи нужный модуль или отдельный плагин;
- запроси URL и посмотри заголовок `Server-Timing`:
  - `curl -sS -D - https://example.test/ -o /dev/null | rg -i \"^server-timing:\"`

Ограничения:

- не включай экспериментальные модули в рабочем окружении без согласования.
