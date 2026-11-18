# Справочник по разметке блоков

## Синтаксис комментариев

Блоки WordPress сериализуются в HTML-комментарии с атрибутами JSON.

```html
<!-- wp:block-name {"attr":"value"} -->
<div class="wp-block-block-name">Inner content</div>
<!-- /wp:block-name -->

<!-- wp:block-name {"attr":"value"} /-->  (self-closing, no inner content)
```

Правила:

- открывающий тег: `<!-- wp:namespace/name {JSON} -->`;
- блоки ядра опускают пространство имён: `<!-- wp:heading -->` (не `core/heading`);
- JSON должен быть корректным: без висячих запятых, строки в двойных кавычках;
- самозакрывающиеся блоки (распорка, разделитель, изображение без подписи) заканчиваются `/-->`;
- у каждого открывающего комментария **обязан** быть парный закрывающий.

## Самые используемые блоки в паттернах

### Блоки раскладки

**Group** — основной контейнер, поддерживает все типы раскладки:

```html
<!-- wp:group {"layout":{"type":"constrained"}} -->
<div class="wp-block-group">
  <!-- inner blocks -->
</div>
<!-- /wp:group -->
```

Типы раскладки:

- `{"type":"constrained"}` — по центру с максимальной шириной (по умолчанию для секций);
- `{"type":"constrained","contentSize":"800px","wideSize":"1200px"}` — собственные ширины;
- `{"type":"flex","flexWrap":"nowrap"}` — горизонтальный ряд;
- `{"type":"flex","orientation":"vertical"}` — вертикальный стек;
- `{"type":"grid","columnCount":3}` — CSS-сетка с фиксированным числом колонок;
- `{"type":"grid","minimumColumnWidth":"250px"}` — адаптивная сетка с автоматическим
  заполнением.

Переопределение тега: `{"tagName":"section"}`, `{"tagName":"header"}`, `{"tagName":"footer"}`.

**Columns / Column:**

```html
<!-- wp:columns -->
<div class="wp-block-columns">
  <!-- wp:column {"width":"66.66%"} -->
  <div class="wp-block-column" style="flex-basis:66.66%">
    <!-- inner blocks -->
  </div>
  <!-- /wp:column -->
  <!-- wp:column {"width":"33.33%"} -->
  <div class="wp-block-column" style="flex-basis:33.33%">
    <!-- inner blocks -->
  </div>
  <!-- /wp:column -->
</div>
<!-- /wp:columns -->
```

### Блоки содержимого

**Heading:**

```html
<!-- wp:heading {"level":2,"fontSize":"x-large"} -->
<h2 class="wp-block-heading has-x-large-font-size">Heading text</h2>
<!-- /wp:heading -->
```

**Paragraph:**

```html
<!-- wp:paragraph {"fontSize":"medium","textColor":"contrast"} -->
<p class="has-contrast-color has-text-color has-medium-font-size">Body text</p>
<!-- /wp:paragraph -->
```

**Image:**

```html
<!-- wp:image {"sizeSlug":"full","linkDestination":"none"} -->
<figure class="wp-block-image size-full">
  <img src="https://example.com/image.jpg" alt="Descriptive alt text"/>
</figure>
<!-- /wp:image -->
```

**Cover:**

```html
<!-- wp:cover {"url":"https://example.com/bg.jpg","dimRatio":60,"overlayColor":"contrast","minHeight":500,"minHeightUnit":"px","layout":{"type":"constrained"}} -->
<div class="wp-block-cover" style="min-height:500px">
  <span aria-hidden="true" class="wp-block-cover__background has-contrast-background-color has-background-dim-60 has-background-dim"></span>
  <img class="wp-block-cover__image-background" alt="" src="https://example.com/bg.jpg" data-object-fit="cover"/>
  <div class="wp-block-cover__inner-container">
    <!-- inner blocks -->
  </div>
</div>
<!-- /wp:cover -->
```

**Buttons / Button:**

```html
<!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
<div class="wp-block-buttons">
  <!-- wp:button {"backgroundColor":"primary","textColor":"base"} -->
  <div class="wp-block-button"><a class="wp-block-button__link has-base-color has-primary-background-color has-text-color has-background wp-element-button">Click me</a></div>
  <!-- /wp:button -->
  <!-- wp:button {"className":"is-style-outline"} -->
  <div class="wp-block-button is-style-outline"><a class="wp-block-button__link wp-element-button">Secondary</a></div>
  <!-- /wp:button -->
</div>
<!-- /wp:buttons -->
```

**Spacer:**

```html
<!-- wp:spacer {"height":"var:preset|spacing|50"} -->
<div style="height:var(--wp--preset--spacing--50)" aria-hidden="true" class="wp-block-spacer"></div>
<!-- /wp:spacer -->
```

**Separator:**

```html
<!-- wp:separator {"backgroundColor":"contrast","className":"is-style-wide"} -->
<hr class="wp-block-separator has-text-color has-contrast-color has-alpha-channel-opacity has-contrast-background-color has-background is-style-wide"/>
<!-- /wp:separator -->
```

**Media & Text:**

```html
<!-- wp:media-text {"mediaPosition":"right","mediaType":"image","mediaWidth":40} -->
<div class="wp-block-media-text has-media-on-the-right is-stacked-on-mobile" style="grid-template-columns:auto 40%">
  <div class="wp-block-media-text__content">
    <!-- inner blocks -->
  </div>
  <figure class="wp-block-media-text__media">
    <img src="https://example.com/image.jpg" alt="Description"/>
  </figure>
</div>
<!-- /wp:media-text -->
```

**Query Loop (список записей):**

```html
<!-- wp:query {"queryId":0,"query":{"perPage":3,"pages":0,"offset":0,"postType":"post","order":"desc","orderBy":"date","inherit":false}} -->
<div class="wp-block-query">
  <!-- wp:post-template {"layout":{"type":"grid","columnCount":3}} -->
    <!-- wp:post-featured-image {"isLink":true} /-->
    <!-- wp:post-title {"isLink":true,"fontSize":"large"} /-->
    <!-- wp:post-excerpt {"excerptLength":20} /-->
  <!-- /wp:post-template -->
</div>
<!-- /wp:query -->
```

## Структура атрибута style

Атрибут `style` хранит собственные значения (не слаги пресетов):

```json
{
  "style": {
    "spacing": {
      "padding": {"top":"var:preset|spacing|50","right":"var:preset|spacing|50","bottom":"var:preset|spacing|50","left":"var:preset|spacing|50"},
      "margin": {"top":"0","bottom":"0"},
      "blockGap": "var:preset|spacing|30"
    },
    "border": {
      "radius": "8px",
      "width": "1px",
      "color": "var:preset|color|contrast",
      "style": "solid"
    },
    "color": {
      "background": "#1a1a2e",
      "text": "#ffffff",
      "gradient": "linear-gradient(135deg,rgb(6,147,227) 0%,rgb(155,81,224) 100%)"
    },
    "typography": {
      "fontSize": "clamp(1rem, 2vw, 1.5rem)",
      "lineHeight": "1.4",
      "letterSpacing": "-0.02em"
    }
  }
}
```

Синтаксис ссылки на пресет в значениях стиля: `var:preset|{type}|{slug}` (не CSS `var()`).

## Соглашение об именовании классов пресетов

При использовании слагов пресетов (а не встроенного стиля) блоки получают CSS-классы:

- `"backgroundColor":"primary"` → `has-primary-background-color has-background`;
- `"textColor":"contrast"` → `has-contrast-color has-text-color`;
- `"fontSize":"large"` → `has-large-font-size`;
- `"fontFamily":"heading"` → `has-heading-font-family`;
- `"gradient":"vivid-cyan-blue-to-vivid-purple"` →
  `has-vivid-cyan-blue-to-vivid-purple-gradient-background has-background`.

## Блокировка блоков

Чтобы пользователи не меняли структуру паттерна:

```json
{
  "lock": {"move": true, "remove": true}
}
```

На блоках-контейнерах `templateLock` ограничивает детей:

- `"templateLock":"all"` — нельзя вставлять, перемещать и удалять;
- `"templateLock":"insert"` — нельзя добавлять и удалять, но можно перемещать;
- `"templateLock":"contentOnly"` — редактируется только текст и медиа, структура заблокирована.

## Выравнивание блоков

Используй атрибут `align` для широкой и полной ширины:

```json
{"align":"wide"}   <!-- учитывает wideSize -->
{"align":"full"}   <!-- выходит до края области просмотра -->
```
