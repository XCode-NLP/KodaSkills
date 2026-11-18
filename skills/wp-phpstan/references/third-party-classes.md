# Классы сторонних разработчиков и шаблоны исключений

Когда PHPStan сообщает об отсутствии существующих классов (например, потому что
WordPress или плагин не установлены в окружении анализа), сначала постарайся
наладить обнаружение и только потом добавляй точечные исключения.

## Прежде чем добавлять `ignoreErrors`

- Убедись, что зависимость действительно есть (установлена или требуется в этом
  окружении).
- Предпочитай заглушки и расширения, уже используемые в репозитории.
- Предпочитай узкое исключение для префикса поставщика широкому исключению.

## Рекомендуемые пакеты заглушек

Заглушки полезны, когда в окружении анализа нет WordPress или API плагина, но
проверка типов всё равно нужна (вместо сплошных исключений).

Частые пакеты:

```bash
composer require --dev szepeviktor/phpstan-wordpress
composer require --dev php-stubs/wordpress-stubs
composer require --dev php-stubs/woocommerce-stubs
composer require --dev php-stubs/acf-pro-stubs
```

Когда заглушки полезны (а иногда необходимы):

- PHPStan запускается в репозитории плагина или темы без полной копии WordPress;
- PHPStan сообщает о неизвестных функциях ядра (например, `add_action()`,
  `get_option()`);
- есть интеграции с необязательными плагинами (WooCommerce, ACF Pro), которые не
  установлены при анализе;
- нужны проверки существования методов и свойств и точные типы возврата вместо
  `ignoreErrors`.

Замечания:

- предпочитай заглушки, совпадающие с версиями во время выполнения: несовпадение
  даёт ложные срабатывания;
- добавление зависимостей Composer меняет репозиторий, подтверди, что для задачи
  это допустимо.

## Убедись, что заглушки загружены

Установить заглушки недостаточно, если PHPStan их не читает. Укажи пути к ним в
`phpstan.neon`.

```neon
parameters:
    bootstrapFiles:
        - %rootDir%/../../php-stubs/woocommerce-stubs/woocommerce-stubs.php
    scanFiles:
        - %rootDir%/../../php-stubs/wordpress-stubs/wordpress-stubs.php
        - %rootDir%/../../php-stubs/acf-pro-stubs/acf-pro-stubs.php
        - %rootDir%/../../woocommerce/action-scheduler/functions.php
```

## Точечные шаблоны исключений (примеры)

```neon
parameters:
    ignoreErrors:
        # Admin Columns Pro
        - '#.*(unknown class|invalid type|call to method .* on an unknown class) AC\\ListScreen.*#'

        # Elementor
        - '#.*(unknown class|invalid type|call to method .* on an unknown class) Elementor\\.*#'

        # Yoast SEO
        - '#.*(unknown class|invalid type|call to method .* on an unknown class) WPSEO_.*#'
```

Правила составления шаблонов:

- покрывай варианты ошибок: `unknown class`, `invalid type`,
  `call to method .* on an unknown class`;
- держи шаблоны достаточно конкретными, чтобы задевать только нужные классы;
- добавляй короткий комментарий с именем плагина или темы;
- группируй связанные шаблоны одной зависимости.

Когда добавлять исключения:

- только для настоящих сторонних зависимостей, с которыми взаимодействует твой
  код;
- документируй каждый шаблон комментарием;
- запускай PHPStan заново, чтобы исключение не скрыло посторонние проблемы.
