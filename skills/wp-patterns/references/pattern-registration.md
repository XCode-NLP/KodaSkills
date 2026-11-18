# Регистрация паттернов

## Автоматическая регистрация через директорию `/patterns/`

WordPress 6.0 и новее автоматически регистрирует паттерны из `.php`-файлов в директории темы
`patterns/`.

### Заголовок файла (обязательные поля)

```php
<?php
/**
 * Title: Hero with Call to Action
 * Slug: theme-slug/hero-cta
 * Categories: banner, call-to-action
 */
?>
<!-- wp:group ... -->
```

### Все поля заголовка

| Поле | Обязательно | Описание | Пример |
|-------|----------|-------------|---------|
| `Title` | Да | Отображаемое имя в панели вставки | `Hero with Call to Action` |
| `Slug` | Да | Уникальный идентификатор (`namespace/name`) | `theme-slug/hero-cta` |
| `Categories` | Да | Слаги категорий через запятую | `banner, call-to-action` |
| `Description` | Нет | Подсказка или справочный текст в панели вставки | `A full-width hero section` |
| `Viewport Width` | Нет | Ширина предпросмотра в панели вставки (px) | `1400` |
| `Inserter` | Нет | Показывать в панели вставки (`yes` или `no`) | `no` (скрывает из панели вставки) |
| `Keywords` | Нет | Ключевые слова для поиска через запятую | `hero, header, banner` |
| `Block Types` | Нет | Блоки, которые этот паттерн заменяет | `core/post-content` |
| `Post Types` | Нет | Ограничение по типам записей | `page, wp_template` |
| `Template Types` | Нет | Типы шаблонов, для которых предлагается паттерн | `home, front-page` |

### Структура файлов

```
my-theme/
  patterns/
    hero-cta.php
    testimonial-grid.php
    footer-columns.php
  theme.json
  style.css
  ...
```

Имена файлов описательные, но на регистрацию не влияют: идентификатором служит заголовок `Slug`.

## PHP в файлах паттернов

Файлы паттернов выполняют PHP на этапе регистрации, а не при отрисовке. Это принципиально.

### Безопасные функции

```php
<?php esc_html_e( 'Read More', 'theme-textdomain' ); ?>
<?php esc_attr_e( 'Submit', 'theme-textdomain' ); ?>
<?php echo esc_url( get_theme_file_uri( 'assets/images/placeholder.webp' ) ); ?>
<?php echo esc_attr( get_theme_file_uri( 'assets/images/bg.jpg' ) ); ?>
```

Всегда используй:

- `esc_html_e()` и `esc_html__()` для видимого текста (интернационализация и экранирование);
- `esc_attr_e()` и `esc_attr__()` для значений атрибутов (интернационализация и экранирование);
- `esc_url()` для URL;
- `get_theme_file_uri()` для путей к ресурсам темы.

### Небезопасно — НЕ используй

```php
// НЕВЕРНО: зависит от запроса — выполняется на init, а не при отрисовке
<?php $posts = get_posts(); ?>
<?php the_title(); ?>
<?php wp_get_current_user(); ?>
<?php is_admin(); ?>
```

PHP паттерна выполняется один раз при регистрации паттерна (во время `init`), а не при отрисовке
страницы. Любые динамические данные времени выполнения будут устаревшими или недоступными.

### Требования интернационализации

Все видимые пользователю строки должны переводиться:

```php
<!-- wp:heading -->
<h2 class="wp-block-heading"><?php esc_html_e( 'Our Services', 'theme-textdomain' ); ?></h2>
<!-- /wp:heading -->

<!-- wp:button -->
<div class="wp-block-button"><a class="wp-block-button__link wp-element-button"><?php esc_html_e( 'Get Started', 'theme-textdomain' ); ?></a></div>
<!-- /wp:button -->
```

Для значений атрибутов блоков с переводимым текстом экранируй соответствующим образом:

```php
<!-- wp:image {"alt":"<?php esc_attr_e( 'Team photo', 'theme-textdomain' ); ?>"} -->
```

## Ручная регистрация

Для плагинов и паттернов по условию используй `register_block_pattern()`:

```php
register_block_pattern(
    'my-plugin/testimonial-card',
    array(
        'title'       => __( 'Testimonial Card', 'my-plugin' ),
        'description' => __( 'A single testimonial with avatar and quote.', 'my-plugin' ),
        'categories'  => array( 'testimonials' ),
        'content'     => '<!-- wp:group ... --> ... <!-- /wp:group -->',
        'keywords'    => array( 'quote', 'review' ),
    )
);
```

Подключайся к `init`:

```php
add_action( 'init', function() {
    register_block_pattern( ... );
});
```

## Собственные категории

Регистрируй до паттернов:

```php
add_action( 'init', function() {
    register_block_pattern_category(
        'theme-slug-portfolio',
        array( 'label' => __( 'Portfolio', 'theme-textdomain' ) )
    );
});
```

Для тем категории также можно регистрировать через `theme.json`:

```json
{
    "patterns": {
        "categories": [
            { "name": "theme-slug-portfolio", "label": "Portfolio" }
        ]
    }
}
```

## Снятие регистрации паттернов

Удалить паттерны ядра или плагина:

```php
add_action( 'init', function() {
    unregister_block_pattern( 'core/query-standard-posts' );
});
```

Удалить целую категорию:

```php
unregister_block_pattern_category( 'banner' );
```

## Соглашения о пространствах имён

- **Темы**: `theme-slug/pattern-name` (например, `twentytwentyfive/hero-banner`);
- **Плагины**: `plugin-slug/pattern-name` (например, `woocommerce/product-grid`);
- **Ядро**: `core/pattern-name`.

Всегда добавляй префикс слага темы или плагина, чтобы избежать столкновений.
