# Статическое перечисление

Перечисли возможности плагина по исходному коду, без запущенного окружения. Статическое
перечисление неизбежно приблизительное: динамичность PHP (косвенность через переменные,
регистрация по условию времени выполнения) означает, что полная опись получается только
живым вызовом `wp_get_abilities()`. Когда статическая и живая описи расходятся, доверяй живой;
статическая задаёт расхождение, чтобы ревьюер знал, куда смотреть.

## Типичная форма регистрации

```php
wp_register_ability(
    '<plugin-slug>/<ability-name>',
    array(
        'label'               => __( '...', '<text-domain>' ),
        'description'         => __( '...', '<text-domain>' ),
        'category'            => '<category-slug>',
        'input_schema'        => array( /* ... */ ),
        'execute_callback'    => array( self::class, 'execute_my_ability' ),
        'permission_callback' => array( self::class, 'check_permission' ),
        'meta'                => array(
            'annotations' => array(
                'readonly'    => true,
                'destructive' => false,
                'idempotent'  => true,
            ),
            'show_in_rest' => true,
        ),
    )
);
```

## Шаг 1 — найди каждый вызов регистрации

```bash
grep -rn --include='*.php' 'wp_register_ability\s*(' <plugin-root>/
```

Ноль совпадений → верни понятный отчёт «возможности не зарегистрированы» согласно разделу
«Сбои и отладка» в SKILL.md. Не выдумывай пустую опись.

## Шаг 2 — извлеки имя каждой возможности

Первый аргумент — имя возможности, обычно строковый литерал. Реальное форматирование
разбивает вызов на строки (пример выше сам многострочный), поэтому однострочные регулярные
выражения упускают частые случаи. Используй инструмент для нескольких строк:

```bash
# ripgrep с --multiline и PCRE2 захватывает имя независимо от переноса строки:
rg --multiline --pcre2 --type=php -n \
   "wp_register_ability\s*\(\s*['\"]([^'\"]+)['\"]" <plugin-root>/

# Запасные варианты: pcregrep -M, perl -0777.
```

Если первый аргумент — переменная или константа (`wp_register_ability( $name, ... )`,
`wp_register_ability( MyPlugin\NAME, ... )`), проследи её: недавнее присваивание в той же
функции или константа класса обычно разрешаются; имя, вычисленное в цикле, — нет; в этом
случае отметь ограничение и порекомендуй режим выполнения для авторитетного перечисления.

## Шаг 3 — извлеки блок аннотаций

Аннотации лежат в `meta.annotations.{readonly,destructive,idempotent}`. Для каждой регистрации
читай литерал массива вперёд до парной закрывающей скобки. Частые формы:

- многострочный литерал (самый частый);
- короткая однострочная запись;
- вспомогательный метод (`'annotations' => self::annotations_for_read()`) — разреши метод,
  если он возвращает литерал; иначе пометь `<unresolved>` и запусти враждебную проверку
  только по колбэку;
- константа класса (`'annotations' => self::READONLY_ANNOTATIONS`) — разреши константу.

Запиши `ability_name → declared_annotations`.

## Шаг 4 — перейди от `execute_callback` к его телу

`execute_callback` бывает таким:

```php
'execute_callback' => array( self::class, 'execute_get_things' ),
'execute_callback' => array( My_Class::class, 'execute_get_things' ),
'execute_callback' => array( $this, 'execute_get_things' ),
'execute_callback' => 'my_plugin_execute_get_things',  // функция верхнего уровня
'execute_callback' => function ( $input ) { /* ... */ },  // замыкание
```

Разреши ссылку до места в исходнике: файл, начальная строка, конечная строка. Проверки
корректности аннотаций, линты схем и проверки прав работают в этом диапазоне байтов.

## Пределы статического перечисления

Случаи, когда опись неполна или неоднозначна:

- имена через переменные (перебор `foreach` по списку слагов);
- аннотации через переменные (собираются из конфигурации);
- регистрация по условию (`if ( feature_enabled() )`);
- колбэки через переменные (`array( $this, $callback_name )`).

Запиши каждый такой случай в раздел «Ограничения статического перечисления» отчёта и
порекомендуй повторный прогон в режиме выполнения для авторитетной описи.

## Формат вывода

```markdown
## Static inventory

Found <N> ability registrations across <M> files:

| Ability | Source file | Registration line | Callback file | Callback lines |
|---|---|---|---|---|
| myplugin/get-foo | src/Abilities.php | 42 | src/Abilities.php | 102-134 |
| myplugin/submit-bar | src/Abilities.php | 68 | src/Services/Bar.php | 58-91 |

### Limitations

- <ability>: annotations built dynamically in `annotations_for_read()`;
  recommend runtime mode for annotation cross-check.
```
