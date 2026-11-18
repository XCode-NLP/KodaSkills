## Правила именования плагинов (правило 17 и проверка имени в Plugin Check)

Источники: [требования к заголовку плагина](https://developer.wordpress.org/plugins/plugin-basics/header-requirements/#header-fields) · [подробные правила плагинов, §17](https://developer.wordpress.org/plugins/wordpress-org/detailed-plugin-guidelines/) · проверки Plugin Check `Plugin_Header_Fields_Check` и `Trademarks_Check`, а также подсказки AI Namer.

### Технические требования к имени

| Правило | Подробности | Код ошибки |
|------|---------|------------|
| Нельзя использовать имена-заглушки | `"Plugin Name"` и `"My Basics Plugin"` отклоняются | `plugin_header_invalid_plugin_name` |
| Минимум 5 буквенно-цифровых символов | Имя должно содержать не менее 5 латинских букв (a–Z) или цифр | `plugin_header_unsupported_plugin_name` (только для новых плагинов) |
| Имя должно быть в readme | Заголовок `=== Plugin Name ===` обязателен и должен быть корректным | `invalid_plugin_name` / `empty_plugin_name` |
| Имя должно совпадать между файлами | Имя в readme и в заголовке плагина должны совпадать (с учётом регистра и раскодирования сущностей) | `mismatched_plugin_name` (предупреждение) |

**Правила слага:** нижний регистр, только дефисы, максимум 50 символов, образуется из
отображаемого имени.

### Правила качества именования (AI Namer)

**1. Никаких обобщённых имён**

Имя должно быть достаточно конкретным, чтобы отличить плагин от примерно 60 000 других.

- отклоняется: «Shipping», «Ecommerce Tracker», «SEO Plugin»;
- принимается: «ShipGlex Shipping», «Shipping Tracker for UPS»;
- исключение: придуманные, оригинальные термины допустимы, если стоят **в начале** имени.

**2. Имя должно быть связано с функцией плагина**

Отображаемое имя должно соотноситься с тем, что плагин реально делает. Исключение —
оригинальные придуманные термины.

**3. Никакого переполнения ключевыми словами**

Неестественное повторение ключевых слов в имени ради поисковой оптимизации не допускается.

**4. Имя не должно быть слишком похоже на существующие плагины**

Проверяется по каталогу плагинов WordPress.org. Если похоже, предложи выразительный термин
(имя автора, бренд или составленный термин) в начале.

**5. Правила использования товарных знаков и названий проектов**

Товарные знаки и названия проектов допустимы **только** после связок вроде `for`, `with`,
`using` или `and`:

- ✅ `"My Plugin for WooCommerce"` — товарный знак после «for», affiliation не подразумевается;
- ✅ `"Pricing Rates for WooCommerce"` — подходит;
- ❌ `"WooCommerce Pricing Rates"` — начинается с товарного знака, подразумевает affiliation;
- ❌ `"Nicedev Paypal for WooCommerce"` — PayPal не стоит в структуре без affiliation;
  правильная форма: `"Nicedev Payment Gateway with PayPal for WooCommerce"`;
- ❌ `"PricingPress"` — словослияние с `-Press` (товарный знак WordPress);
- проверяй словослияния: имена, смешивающие товарный знак (например, `-Press`, `Woo-`), не
  допускаются.

**6. Запрещённые и нежелательные термины**

Запрещённые и нежелательные термины не могут встречаться **нигде** в имени — даже после
`for` и `with`.

#### Запрещённые термины (жёсткий блок)

| Термин | Причина |
|------|--------|
| Facebook, FB, fbook, Whatsapp, WA, Instagram, Insta, Gram, INS, Threads, Oculus | Юридический запрос Meta: нельзя использовать в имени, слаге и баннерах |
| WordPress, wordpess, wpress | Товарный знак WordPress; избыточно в каталоге WP.org |
| WP (как отдельный или избыточный, например «for WP») | То же, что WordPress — избыточно в этом контексте |
| Trustpilot | Прямой запрос от владельца товарного знака |
| Binance Pay | Прямой запрос от владельца товарного знака |

#### Нежелательные термины (нужно убрать)

| Термин | Причина |
|------|--------|
| plugin (когда избыточно, например «SEO Plugin») | Избыточно; запрещено первым словом |
| best, #1, First, Perfect, The most | Превосходные степени и непроверяемые сравнительные утверждения |
| free (когда избыточно, например «(free)») | Все плагины каталога бесплатны — избыточно |
| WP, W P (в начале или конце, если имеется в виду WordPress) | Сокращение WordPress — избыточно |
| Gutenberg, gberg, guten, berg | Создаёт путаницу; актуальное название — редактор блоков |

### Список товарных знаков для слагов (статическая проверка `Trademarks_Check`)

Следующие слаги статически блокируются. Термины, оканчивающиеся на `-`, не могут **начинать**
слаг; термины без `-` не могут встречаться **нигде** в слаге. `woocommerce` (без дефиса)
допускается только как `for-woocommerce`, `with-woocommerce`, `using-woocommerce` или
`and-woocommerce`.

```
adobe-, adsense-, advanced-custom-fields-, adwords-, akismet-,
all-in-one-wp-migration, amazon-, android-, apple-, applenews-, applepay-,
aws-, azon-, bbpress-, bing-, booking-com, bootstrap-, buddypress-,
chatgpt-, chat-gpt-, cloudflare-, contact-form-7-, cpanel-, disqus-, divi-,
dropbox-, easy-digital-downloads-, elementor-, envato-,
fbook, facebook, fb-, fb-messenger, fedex-, feedburner, firefox-,
fontawesome-, font-awesome-, ganalytics-, gberg, github-, givewp-, google-,
googlebot-, googles-, gravity-form-, gravity-forms-, gravityforms-, gtmetrix-,
gutenberg, guten-, hubspot-, ig-, insta-, instagram, internet-explorer-,
ios-, jetpack-, macintosh-, macos-, mailchimp-, microsoft-,
ninja-forms-, oculus, onlyfans-, only-fans-, opera-, paddle-, paypal-,
pinterest-, plugin, skype-, stripe-, tiktok-, tik-tok-, trustpilot,
twitch-, twitter-, tweet, ups-, usps-, vvhatsapp, vvcommerce, vva-, vvoo,
wa-, webpush-vn, wh4tsapps, whatsapp, whats-app, watson, windows-,
wocommerce, woocom-, woocommerce, woocomerce, woo-commerce, woo-, wo-,
wordpress, wordpess, wpress, wp, wc, wp-mail-smtp-, yandex-, yahoo-,
yoast, youtube-, you-tube-
```

**Словослияния тоже блокируются:** любой слаг, начинающийся с `woo` (без учёта регистра),
например `woopress`, `wooland`.

### Примеры именования

| Имя плагина | Вердикт | Причина |
|-------------|---------|--------|
| `Shipping` | ❌ | Слишком обобщённо |
| `Ecommerce Tracker` | ❌ | Слишком обобщённо, нет контекста |
| `Shipping Tracker for UPS` | ✅ | Описательно и с контекстом |
| `ShipGlex Shipping` | ✅ | Придуманный термин в начале |
| `WooCommerce Pricing Rates` | ❌ | Начинается с товарного знака |
| `Pricing Rates for WooCommerce` | ✅ | Товарный знак после «for» |
| `PricingPress` | ❌ | Словослияние с `-Press` |
| `PRT Text editor for WP` | ❌ | WP запрещён и избыточен; правильно: `PRT Text editor` |
| `Nicedev Paypal for WooCommerce` | ❌ | PayPal не в структуре без affiliation |
| `Nicedev Payment Gateway with PayPal for WooCommerce` | ✅ | Корректная структура |
| `Best SEO Plugin for WordPress` | ❌ | Превосходная степень и запрещённые термины |
| `My Free Slider` | ❌ | «free» избыточно и нежелательно |

### Контрольный список проверки имени (до публикации)

- [ ] имя не является заглушкой (`Plugin Name`, `My Basics Plugin`);
- [ ] в имени не менее 5 буквенно-цифровых символов;
- [ ] имя совпадает в заголовке плагина и в readme;
- [ ] имя конкретное, а не слишком обобщённое для 60 000+ плагинов;
- [ ] имя связано с тем, что плагин реально делает;
- [ ] нет переполнения ключевыми словами;
- [ ] нигде нет запрещённых терминов (бренды Meta, избыточные WordPress и WP, Trustpilot,
  Binance Pay);
- [ ] нет нежелательных терминов (Plugin, Best/#1, Free, Gutenberg, отдельный WP);
- [ ] товарные знаки и названия проектов стоят только после `for`, `with`, `using` или `and`;
- [ ] нет словослияний с товарными знаками WordPress или WooCommerce;
- [ ] слаг в нижнем регистре, только дефисы, максимум 50 символов, без заблокированных терминов.
