# Wildberries — похожие товары и аналитика SKU

Все эндпоинты: `GET` или `POST` на `https://mpstats.io/api/analytics/v1/wb/<path>`

---

## Похожие товары (на основе ИИ)

### POST identical/items

Похожие товары, подобранные ИИ, для заданного товара.

**Параметры запроса:** `d1`, `d2`, идентификатор SKU, `fbs`.
**Тело:** модель постраничной выдачи, фильтров и сортировки.

### POST identical/categories

Категории похожих товаров, подобранных ИИ.

### POST identical/brands

Бренды похожих товаров, подобранных ИИ.

### POST identical/sellers

Продавцы похожих товаров, подобранных ИИ.

### POST identical/price_segmentation

Ценовая сегментация похожих товаров, подобранных ИИ.

### POST identical/trends

Тренды похожих товаров, подобранных ИИ.

### POST identical/by_date

Данные по дням для похожих товаров, подобранных ИИ.

### POST identical/keywords

Ключевые слова похожих товаров, подобранных ИИ.

### POST identical/warehouses

Данные по складам для похожих товаров, подобранных ИИ.

### POST identical/compare

Сравнение периодов для похожих товаров, подобранных ИИ.

---

## Похожие товары (ИИ Wildberries)

### POST identical_wb/items

Похожие товары по ИИ Wildberries для заданного товара.

**Параметры запроса:** `d1`, `d2`, идентификатор SKU, `fbs`.
**Тело:** модель постраничной выдачи, фильтров и сортировки.

### POST identical_wb/categories

Категории похожих товаров по ИИ Wildberries.

### POST identical_wb/brands

Бренды похожих товаров по ИИ Wildberries.

### POST identical_wb/sellers

Продавцы похожих товаров по ИИ Wildberries.

### POST identical_wb/price_segmentation

Ценовая сегментация похожих товаров по ИИ Wildberries.

### POST identical_wb/trends

Тренды похожих товаров по ИИ Wildberries.

### POST identical_wb/by_date

Данные по дням для похожих товаров по ИИ Wildberries.

### POST identical_wb/keywords

Ключевые слова похожих товаров по ИИ Wildberries.

### POST identical_wb/warehouses

Данные по складам для похожих товаров по ИИ Wildberries.

### POST identical_wb/compare

Сравнение периодов для похожих товаров по ИИ Wildberries.

---

## Похожие товары (по данным Wildberries)

### POST similar/items

Похожие товары по данным Wildberries для заданного товара.

**Параметры запроса:** `d1`, `d2`, идентификатор SKU, `fbs`.
**Тело:** модель постраничной выдачи, фильтров и сортировки.

### POST similar/categories

Категории похожих товаров по данным Wildberries.

### POST similar/brands

Бренды похожих товаров по данным Wildberries.

### POST similar/sellers

Продавцы похожих товаров по данным Wildberries.

### POST similar/price_segmentation

Ценовая сегментация похожих товаров по данным Wildberries.

### POST similar/trends

Тренды похожих товаров по данным Wildberries.

### POST similar/by_date

Данные по дням для похожих товаров по данным Wildberries.

### POST similar/keywords

Ключевые слова похожих товаров по данным Wildberries.

### POST similar/warehouses

Данные по складам для похожих товаров по данным Wildberries.

### POST similar/compare

Сравнение периодов для похожих товаров по данным Wildberries.

---

## Обратный поиск: где товар считается похожим

### POST in_similar/items

Товары, в подборках похожих у которых встречается заданный товар.

**Параметры запроса:** `d1`, `d2`, идентификатор SKU, `fbs`.
**Тело:** модель постраничной выдачи, фильтров и сортировки.

### POST in_similar/categories

Категории, где заданный товар встречается как похожий.

### POST in_similar/brands

Бренды, где заданный товар встречается как похожий.

### POST in_similar/sellers

Продавцы, где заданный товар встречается как похожий.

### POST in_similar/price_segmentation

Ценовая сегментация для обратного поиска похожих.

### POST in_similar/trends

Тренды для обратного поиска похожих.

### POST in_similar/by_date

Данные по дням для обратного поиска похожих.

### POST in_similar/keywords

Ключевые слова для обратного поиска похожих.

### POST in_similar/warehouses

Данные по складам для обратного поиска похожих.

### POST in_similar/compare

Сравнение периодов для обратного поиска похожих.

---

## Аналитика на уровне SKU

Во всех эндпоинтах `{id}` — идентификатор товара на WB (число).

### GET items/{id}

Базовая информация о товаре по SKU.

---

### GET items/{id}/full

Подробная информация и статистика за период по SKU (заменяет прежний эндпоинт `sales`).

---

### GET items/{id}/by_period

Дневная статистика по SKU (продажи и остатки по дням).

---

### GET items/{id}/balance/stores

Текущая разбивка остатков по регионам и складам для SKU.

---

### GET items/{id}/balance/sizes

Текущая разбивка остатков по размерам для SKU.

---

### GET items/{id}/balance/stores_and_sizes

Разбивка остатков одновременно по складам и размерам.

---

### GET items/{id}/balance/colors

Разбивка остатков по цветам.

---

### GET items/{id}/sales/stores

Разбивка продаж по регионам и складам для SKU.

---

### GET items/{id}/sales/sizes

Разбивка продаж по размерам для SKU.

---

### GET items/{id}/sales/heatmap

Тепловая карта продаж для SKU.

---

### GET items/{id}/stores

Склады с данными о продажах и остатках.

---

### GET items/{id}/search_stats

Статистика позиций SKU в поиске.

---

## Позиции SKU по ключевым словам

### POST items/{id}/keywords

Поисковые запросы, в которых встречается SKU, и его позиция в каждом.

**Поля элемента в ответе:**

| Поле | Описание |
|-------|-------------|
| `keyword` | Поисковый запрос |
| `position` | Позиция в результатах поиска |
| `date` | Дата |

---

### POST items/{id}/keywords/hourly

Почасовая статистика позиций SKU по ключевым словам.

---

## Отзывы SKU

### GET items/{id}/comments

История отзывов по SKU.

**Поля элемента в ответе:**

| Поле | Описание |
|-------|-------------|
| `date` | Дата отзыва |
| `text` | Текст отзыва |
| `rating` | Оценка (1–5) |
| `valuation` | Оценка полезности |

---

## FAQ по SKU

### GET items/{id}/faq

Вопросы и ответы по SKU.

---

## История фотографий SKU

### GET items/{id}/photos_history

История изменений фотографий товара по SKU.

---

## Рекомендованные товары для SKU

Эндпоинты рекомендованных товаров доступны по пути `items/{id}/recommended/`.

---

Обёртки-скрипты:

- `scripts/wb/wb-sku.sh`;
- `scripts/wb/wb-similar.sh`;
- `scripts/request.sh` (для любого метода, не покрытого отдельной обёрткой).
