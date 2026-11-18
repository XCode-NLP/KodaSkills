# Отрисовка на сервере для Interactivity API

- **Быстрая первая отрисовка**: HTML приходит уже с правильными значениями.
- **Нет сдвига вёрстки**: скрытые элементы остаются скрытыми с первого кадра.
- **Польза для SEO**: поисковые системы видят полностью отрисованное содержимое.
- **Плавная деградация**: содержимое отображается правильно ещё до загрузки
  JavaScript.

## Что нужно настроить

### 1. Включи обработку директив на сервере

**Для компонентов с `block.json`:**

```json
{
  "supports": {
    "interactivity": true
  }
}
```

**Для тем и плагинов без `block.json`:**

Используй `wp_interactivity_process_directives()`, чтобы обработать директивы вручную
(см. раздел «Темы и плагины без block.json» ниже).

### 2. Инициализируй глобальное состояние через `wp_interactivity_state()`

Определи начальные значения состояния в PHP до отрисовки:

```php
wp_interactivity_state( 'myPlugin', array(
  'fruits'    => array( 'Apple', 'Banana', 'Cherry' ),
  'isLoading' => false,
  'count'     => 3,
));
```

Состояние сериализуется и автоматически становится доступно клиентскому JavaScript.

### 3. Инициализируй локальный контекст через `wp_interactivity_data_wp_context()`

Для контекста, ограниченного элементом:

```php
<?php
$context = array(
  'isOpen'   => false,
  'itemId'   => 42,
  'itemName' => 'Example',
);
?>
<div
  data-wp-interactive="myPlugin"
  <?php echo wp_interactivity_data_wp_context( $context ); ?>
>
  <button data-wp-on-async--click="actions.toggle">
    Toggle
  </button>
  <div data-wp-bind--hidden="!context.isOpen">
    Content for <?php echo esc_html( $context['itemName'] ); ?>
  </div>
</div>
```

## Производное состояние на сервере

Когда производное состояние влияет на начальный HTML, определи его в PHP, чтобы
избежать сдвига вёрстки.

### Статическое производное состояние

Когда производное значение известно на момент отрисовки:

```php
$fruits    = array( 'Apple', 'Banana', 'Cherry' );
$hasFruits = count( $fruits ) > 0;

wp_interactivity_state( 'myPlugin', array(
  'fruits'    => $fruits,
  'hasFruits' => $hasFruits,
));
```

### Динамическое производное состояние (через замыкания)

Когда значение зависит от контекста (например, внутри циклов `data-wp-each`):

```php
wp_interactivity_state( 'myPlugin', array(
  'fruits'       => array( 'apple', 'banana', 'cherry' ),
  'shoppingList' => array( 'apple', 'cherry' ),
  'onShoppingList' => function() {
    $state   = wp_interactivity_state();
    $context = wp_interactivity_get_context();
    return in_array( $context['item'], $state['shoppingList'] ) ? 'Yes' : 'No';
  },
));
```

Замыкание вычисляется при обработке директив для каждого элемента.

## Полный пример: список с отрисовкой на сервере

### PHP (колбэк отрисовки или шаблон)

```php
<?php
$fruits = array( 'Apple', 'Banana', 'Cherry' );

wp_interactivity_state( 'myFruitPlugin', array(
  'fruits'    => $fruits,
  'hasFruits' => count( $fruits ) > 0,
  'mango'     => __( 'Mango' ),
));
?>

<div data-wp-interactive="myFruitPlugin">
  <button data-wp-on-async--click="actions.addMango">
    <?php esc_html_e( 'Add Mango' ); ?>
  </button>
  <button data-wp-on-async--click="actions.clearAll">
    <?php esc_html_e( 'Clear All' ); ?>
  </button>

  <ul data-wp-bind--hidden="!state.hasFruits">
    <template data-wp-each="state.fruits">
      <li data-wp-text="context.item"></li>
    </template>
  </ul>

  <p data-wp-bind--hidden="state.hasFruits">
    <?php esc_html_e( 'No fruits available.' ); ?>
  </p>
</div>
```

### JavaScript (view.js)

```javascript
import { store, getContext } from '@wordpress/interactivity';

const { state } = store( 'myFruitPlugin', {
  state: {
    get hasFruits() {
      return state.fruits.length > 0;
    },
  },
  actions: {
    addMango() {
      state.fruits.push( state.mango );
    },
    clearAll() {
      state.fruits = [];
    },
  },
});
```

### Итоговый вывод (начальный HTML)

```html
<div data-wp-interactive="myFruitPlugin">
  <button data-wp-on-async--click="actions.addMango">Add Mango</button>
  <button data-wp-on-async--click="actions.clearAll">Clear All</button>

  <ul>
    <li>Apple</li>
    <li>Banana</li>
    <li>Cherry</li>
  </ul>

  <p hidden>No fruits available.</p>
</div>
```

Атрибут `hidden` добавлен на сервере, потому что `state.hasFruits` истинно.

## Передача значений на клиент

Используй `wp_interactivity_state()`, чтобы передать серверные значения клиентскому
JavaScript.

### Переводы

```php
wp_interactivity_state( 'myPlugin', array(
  'labels' => array(
    'add'    => __( 'Add Item', 'textdomain' ),
    'remove' => __( 'Remove Item', 'textdomain' ),
    'empty'  => __( 'No items found', 'textdomain' ),
  ),
));
```

### URL для Ajax и nonce

```php
wp_interactivity_state( 'myPlugin', array(
  'ajaxUrl' => admin_url( 'admin-ajax.php' ),
  'nonce'   => wp_create_nonce( 'myPlugin_nonce' ),
  'restUrl' => rest_url( 'myPlugin/v1/' ),
));
```

### Использование на клиенте

```javascript
const { state } = store( 'myPlugin', {
  actions: {
    *fetchData() {
      const formData = new FormData();
      formData.append( 'action', 'my_action' );
      formData.append( '_ajax_nonce', state.nonce );

      const response = yield fetch( state.ajaxUrl, {
        method: 'POST',
        body: formData,
      });
      return yield response.json();
    },
  },
});
```

## Темы и плагины без block.json

Для тем и плагинов, которые не используют `block.json`, применяй
`wp_interactivity_process_directives()`:

```php
<?php
wp_interactivity_state( 'myTheme', array(
  'menuOpen' => false,
));

ob_start();
?>

<nav
  data-wp-interactive="myTheme"
  data-wp-class--is-open="state.menuOpen"
>
  <button data-wp-on-async--click="actions.toggleMenu">
    Menu
  </button>
  <ul data-wp-bind--hidden="!state.menuOpen">
    <li><a href="/">Home</a></li>
    <li><a href="/about">About</a></li>
  </ul>
</nav>

<?php
$html = ob_get_clean();
echo wp_interactivity_process_directives( $html );
```

Вызывай `wp_interactivity_process_directives()` только один раз — на самом внешнем
уровне шаблона.

## Справочник вспомогательных функций PHP

| Функция | Назначение |
|----------|---------|
| `wp_interactivity_state( $namespace, $state )` | Инициализировать или получить глобальное состояние для пространства имён |
| `wp_interactivity_data_wp_context( $context )` | Сформировать атрибут `data-wp-context` |
| `wp_interactivity_get_context( $namespace )` | Получить текущий контекст при обработке директив |
| `wp_interactivity_process_directives( $html )` | Обработать директивы вручную (темы и плагины) |

## Частые ошибки

### Обработка директив на сервере не включена

**Для тех, кто использует `block.json`:** без `supports.interactivity` директивы не
обрабатываются:

```json
{
  "supports": {
    "interactivity": true
  }
}
```

**Для тем и плагинов:** убедись, что `wp_interactivity_process_directives()` вызывается
для выводимого HTML.

### Производное состояние отсутствует на сервере

Если `state.hasFruits` определено только в JavaScript, атрибут `hidden` не будет
установлен:

```html
<!-- Без серверного состояния: элемент мелькает и скрывается (сдвиг вёрстки) -->
<p data-wp-bind--hidden="state.hasFruits">No fruits</p>
```

### Состояние не совпадает с ожиданиями клиента

Убедись, что логика производного состояния в PHP и JavaScript совпадает:

```php
// PHP
'hasFruits' => count( $fruits ) > 0,
```

```javascript
// JavaScript — логика должна совпадать с PHP
get hasFruits() {
  return state.fruits.length > 0;
}
```

## Внешние ссылки

- [WordPress: отрисовка на сервере](https://developer.wordpress.org/block-editor/reference-guides/interactivity-api/core-concepts/server-side-rendering/)
- [WordPress: глобальное состояние, локальный контекст и производное состояние](https://developer.wordpress.org/block-editor/reference-guides/interactivity-api/core-concepts/undestanding-global-state-local-context-and-derived-state/)
- [WordPress: справочник Interactivity API](https://developer.wordpress.org/block-editor/reference-guides/interactivity-api/api-reference/)
