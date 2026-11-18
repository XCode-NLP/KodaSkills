# Проверка атрибутов элемента

Когда снимок не показывает `id`, `class`, атрибуты `data-*` или другие свойства DOM элемента, используй `eval`, чтобы их посмотреть.

## Примеры

```bash
playwright-cli snapshot
# в снимке кнопка отображается как e7, но её id и data-атрибуты не видны

# получить id элемента
playwright-cli eval "el => el.id" e7

# получить все CSS-классы
playwright-cli eval "el => el.className" e7

# получить конкретный атрибут
playwright-cli eval "el => el.getAttribute('data-testid')" e7
playwright-cli eval "el => el.getAttribute('aria-label')" e7

# получить вычисленное значение свойства стиля
playwright-cli eval "el => getComputedStyle(el).display" e7
```
