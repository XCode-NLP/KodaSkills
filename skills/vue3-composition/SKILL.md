---
name: vue3-composition
description: "Код на Vue 3 Composition API, который выдерживает рост за пределы демо: контракты компонентов, границы provide и inject, соглашения v-model и когда НЕ надо выносить композабл. Используй при создании или проверке компонентов, композаблов и хранилищ Vue 3."
license: MIT
metadata:
  author: LeonxLJX
  source: https://github.com/LeonxLJX/web-engineer-skills
  tags: [vue, javascript, frontend]
---

# Дисциплина Vue 3 Composition API

## Сначала контракты

Компонент — это API. Прежде чем писать разметку, напиши контракт:

```ts
// ❌ implicit contract — every prop optional, everything stringly-typed
defineProps(['item', 'dense', 'onChange'])

// ✅ explicit, typed, minimal
const props = withDefaults(defineProps<{
  item: Todo
  dense?: boolean
}>(), { dense: false })

const emit = defineEmits<{
  change: [value: Todo['id'], source: 'user' | 'sync']
}>()
```

Правила:

1. **Props — это данные, а не суп из настроек.** Если передаёшь больше пяти булевых флагов, компонент делает две работы — раздели его.
2. **`defineEmits` с синтаксисом кортежей** — типизированные данные избавляют от раскопок «что там опять в `$event`».
3. **`v-model` на поле, а не на форму.** `v-model:title` лучше, чем передача объектов с шумом `update:*`.

## Границы provide и inject

- `provide` — для **контекста уровня фреймворка** (тема, i18n, флаги возможностей), а не чтобы обойти props.
- Ключи внедрения должны быть типизированы и экспортированы из одного модуля:

```ts
// keys.ts
export const THEME_KEY: InjectionKey<Theme> = Symbol('theme')
```

- Если два компонента общаются через provide и inject и ни один не является фабрикой-предком, это скрытый глобал — используй хранилище.

## Композаблы: выноси поведение, а не синтаксис

Выноси композабл, когда есть **поведение с состоянием** (таймер, подписка, стек отмены), а не чтобы сэкономить строки:

```ts
// ✅ behavior: owns state + lifecycle
export function useInterval(cb: () => void, ms: MaybeRef<number>) {
  let id: ReturnType<typeof setInterval> | undefined
  watch(() => toValue(ms), (ms) => {
    if (id) clearInterval(id)
    if (ms > 0) id = setInterval(cb, ms)
  }, { immediate: true })
  onScopeDispose(() => id && clearInterval(id))
}
```

Антипаттерны:

- `useXxx()`, который только оборачивает computed, — это функция, оставь её простой.
- Композаблы, которые вызывают `onMounted` для побочных эффектов вместо `watch` и `watchEffect`, — ломают SSR и тестируемость.

## Реактивность: не теряй нить

- Деструктуризация props ломает реактивность — используй `toRefs(props)` или оставь `props.x`.
- `reactive()` для объектов, `ref()` для примитивов и результатов API. Смешивание `reactive`-массивов с логикой замены — классический источник багов; предпочитай `ref<T[]>` и `value = next`.
- Асинхронное состояние: выводи через `computed` из единственного источника истины (`status` плюс `data` плюс `error`), никогда не держи три параллельных ref, которые надо синхронизировать.

## Производительность без микрооптимизаций

- Для больших списков, которые заменяются целиком, бери `shallowRef`.
- `v-memo` только при измеренной проблеме рендера: это контракт, что зависимости мемо полностью определяют вывод, а неверные зависимости дают устаревший интерфейс.
- Виртуализируй списки больше 1000 строк; не разбивай на страницы то, что пользователи прокручивают.

## Критерий готовности (чек-лист агента)

- [ ] Props и emits типизированы; никаких `defineProps(['a','b'])`
- [ ] Нет проброса props глубже двух уровней (вместо этого provide или хранилище)
- [ ] Каждый композабл владеет своей очисткой (`onScopeDispose`)
- [ ] Безопасно для SSR: нет `window` и `document` вне защиты жизненного цикла
- [ ] Ключи в списках — стабильные идентификаторы, никогда индекс
