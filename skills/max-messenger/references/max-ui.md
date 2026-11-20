# MAX UI — библиотека React-компонентов для мини-приложений

> Источник: UI github.com/max-messenger/max-ui@1df07bd (npm `@maxhub/max-ui` 0.5.0) · сверено 21.09.2026. `dev.max.ru/ui` отстаёт от репозитория (см. раздел о переходах) — если это выглядит устаревшим, сначала проверь репозиторий.

`@maxhub/max-ui` — библиотека React-компонентов, не зависящая от Bridge: её можно использовать в мини-приложениях MAX, в других суперприложениях и в обычных веб-приложениях. В исходниках **нет ни одной кодовой зависимости от MAX Bridge** (`window.WebApp`) — см. [Определение платформы и темы](#определение-платформы-и-темы).

## Установка

```shell
npm i @maxhub/max-ui
```

Peer-зависимости заданы **точными версиями, а не диапазонами**: `react@19.2.8` и `react-dom@19.2.8`. Верь `package.json`, а не README: в списке возможностей README до сих пор написано «React 18+», это устаревший маркетинговый текст. Строгий установщик (`npm --strict-peer-deps`, настройки pnpm по умолчанию) может упасть на любой другой патч-версии React 19.x, пока в репозитории не расширят этот пин.

Импортируй CSS один раз глобально (импорт с побочным эффектом — нужен сборщик или CSS-загрузчик, обычный `tsc` не подойдёт):

```tsx
import '@maxhub/max-ui/dist/styles.css';
```

Пакет собран только как ESM (`"type": "module"`, сборки CJS нет). Веб-шрифт в комплект не входит — стили текста для Android рассчитывают, что приложение само подключит веб-шрифт Roboto (или что он есть в системе); на iOS используется системный набор шрифтов, дополнительно ничего не нужно.

## Провайдер `<MaxUI>`

Оберни корень приложения один раз:

```tsx
import type { ReactNode } from 'react';
import { MaxUI } from '@maxhub/max-ui';
import '@maxhub/max-ui/dist/styles.css';

export function Root({ children }: { children: ReactNode }) {
  return (
    <MaxUI platform="ios" colorScheme="dark" resetBody>
      {children}
    </MaxUI>
  );
}
```

| Проп | Тип | По умолчанию | Заметки |
|---|---|---|---|
| `children` | `ReactNode` | — | |
| `platform` | `'ios' \| 'android'` | определяется автоматически | См. определение ниже. |
| `colorScheme` | `'light' \| 'dark'` | определяется автоматически | См. определение ниже. |
| `resetBody` | `boolean` | `false` | При `true` добавляет на `document.body` CSS-класс сброса стилей при монтировании и убирает его при размонтировании. |
| `className` | `string` | — | Добавляется к корневому `<div>` провайдера. |

Корневой `<div>` получает классы `MaxUI`, `MaxUI_colorScheme_<light|dark>`, `MaxUI_platform_<ios|android>` и твой `className`.

## Определение платформы и темы

**Определение идёт по User-Agent и медиазапросам, а не через MAX Bridge** — `max-ui` никогда не читает `window.WebApp`:

- `platform` по умолчанию: регулярное выражение по `navigator.userAgent` ищет `iPad|iPhone|iPod` → `'ios'`; всё остальное (включая desktop) → `'android'` (в типе всего два значения, вариантов `'desktop'` и `'web'` здесь нет).
- `colorScheme` по умолчанию: `window.matchMedia('(prefers-color-scheme: dark)')`, причём подписка на изменения темы ОС **сохраняется** и обновляется вживую, если не передать `colorScheme` явно.

Если мини-приложению нужна *настоящая* платформа и тема хоста, прочитай их из Bridge (`window.WebApp.platform`, см. [`mini-apps-bridge.md`](./mini-apps-bridge.md)) и передай результат в `platform` и `colorScheme` явно: собственное автоопределение `max-ui` не отличает webview MAX от обычного мобильного браузера и не зафиксирует тему ОС, пока ты её не переопределишь.

Хуки: `usePlatform(): 'ios' | 'android'`, `useColorScheme(): 'light' | 'dark'`, `useAppearance(): { platform, colorScheme }` — все читают из `MaxUIContext`, который заполняет ближайший `<MaxUI>`.

## Каталог компонентов

Основные экспортируемые компоненты (`components/*` плюс вёрстка из `internal/*`; низкоуровневые помощники `Ripple`, `ClearableInput`, `SvgButton`, `Tappable` тоже экспортируются, но здесь не перечислены). Сайт `dev.max.ru/ui` **отстаёт от этого списка**: он до сих пор показывает удалённые компоненты (`Dot`, `ToolButton`, `Avatar.OnlineDot`) и `SearchInput`, которого в исходниках нет, а `Radio` (добавлен в 0.5.0) там отсутствует. Считай таблицу ниже, собранную по исходникам 0.5.0, достоверной.

| Компонент | Ключевые пропы | Заметки |
|---|---|---|
| `Avatar.Container` | `size?: 16\|20\|24\|...\|96\|number` (по умолчанию `40`), `form?: 'circle'\|'squircle'`, `onlineStatus?: boolean`, `overlay?`, `rightTopCorner?`, `rightBottomCorner?: ReactNode` | Индикатор «в сети» рисуется только для круглых аватаров размером 24–80 px. |
| `Avatar.Image` | `fallback?: ReactNode`, `fallbackGradient?: AvatarTextGradient` (по умолчанию `'red'`) | При ошибке загрузки подставляет `Avatar.Text`. |
| `Avatar.Text` | `gradient?: 'red'\|'orange'\|'green'\|'blue'\|'purple'\|'custom'` | |
| `Avatar.Icon`, `Avatar.Overlay`, `Avatar.CloseButton` | только нативные `ComponentProps` | |
| `Button` | `size?: 'xsmall'\|'small'\|'medium'\|'large'`, `variant?: 'primary'\|'secondary'\|'ghost'\|'primary-contrast'\|'secondary-contrast'\|'overlay'\|'destructive'`, `stretched?`, `iconBefore?/iconAfter?/indicator?: ReactNode`, `loading?: boolean` | `loading` блокирует клики и показывает внутренний `Spinner`; на Android при нажатии появляется `Ripple`. |
| `IconButton` | те же `size`, `variant`, `loading`, что у `Button` | |
| `CellAction` | `mode?: 'primary'\|'secondary'\|'themed'\|'destructive'\|'custom'`, `surface?: 'default'\|'island'`, `height?: 'compact'\|'normal'`, `before?: ReactNode`, `showChevron?: boolean` | |
| `CellHeader` | `titleStyle?: 'caps'\|'normal'`, `fullWidth?`, `after?: ReactNode` | |
| `CellInput` | `height?: 'compact'\|'normal'`, `surface?: 'default'\|'island'`, `before?: ReactNode` | |
| `CellList` | `mode?: 'full-width'\|'island'` (по умолчанию `'full-width'`), `filled?`, `header?: ReactNode` | |
| `CellSimple` | `height?: 'compact'\|'normal'`, `surface?: 'default'\|'island'`, `title?/subtitle?/overline?/before?/after?: ReactNode`, `subtitleMode?: 'secondary'\|'tertiary'`, `showChevron?`, `disabled?`, `separator?`, `link?: string`, `as?: ElementType` | Экспортирует отдельный тип `Appearance`, не связанный ни с одним пропом — не описывай его как рабочий проп. |
| `Counter` | `value: number` (обязателен), `variant?: 'primary'\|'primary-contrast'\|'attention'\|'attention-contrast'\|'promo'\|'static'\|'static-contrast'\|'default'\|'mute'\|'menu'`, `rounded?` | |
| `Input` | `mode?: 'default'\|'contrast'`, `size?: 'large'\|'medium'`, `iconBefore?/iconAfter?: ReactNode`, `withClearButton?`, `count?: number`, `hint?: ReactNode` | `size` перекрывает нативный HTML-атрибут `size`. |
| `Textarea` | `mode?: 'primary'\|'secondary'` | |
| `Radio` | только атрибуты нативного `<input type="radio">` | **Новое в 0.5.0** — на сайте пока не описано. |
| `Switch` | только атрибуты нативного `<input type="checkbox">` | Рендерится с `role="switch"`; оформление зависит от платформы. |
| `Spinner` | `size?: 20\|24\|number` (по умолчанию `20`), `appearance?: 'primary'\|'themed'\|'neutral-themed'\|'primary-static'\|'contrast'\|'contrast-static'\|'negative'` | Внутри рисует спиннер, зависящий от платформы, через `usePlatform()`. |
| `Typography.Text` | `variant?:` одно из `hero/header/subheader/title/body/body-strong/detail/detail-strong/description/description-strong/label/label-strong/tag/tag-strong/note/note-strong/action-large/action-medium/action-small/action-xsmall` (по умолчанию `'body'`), `color?: 'primary'\|'secondary'\|'tertiary'\|'inherit'` | **Рекомендуемый API для нового кода** (см. раздел о переходах). |
| `Typography.Display/Headline/Title/Body/Label/Action` | у каждого свой перечень `variant` (устаревшие, но публичные) | Оставлены для совместимости; в новом коде предпочитай `Typography.Text`, хотя пример быстрого старта в README и на сайте всё ещё использует `Typography.Title`. |
| `Container` | `fullWidth?: boolean` | Примитив вёрстки. |
| `Flex` | `display?: 'flex'\|'inline-flex'`, `direction?: 'row'\|'column'\|'row-reverse'\|'column-reverse'`, `align?`, `justify?: 'start'\|'center'\|'end'\|'space-between'`, `wrap?`, `gap?/gapX?/gapY?: number\|string` | Значение `justify="between"` переименовано в `"space-between"`. |
| `Grid` | `display?: 'grid'\|'inline-grid'`, `align?`, `justify?`, `gap?/gapX?/gapY?`, `cols?/rows?: number` | |
| `Panel` | `mode?: 'primary'\|'secondary'`, `centeredX?/centeredY?: boolean` | Не полиморфный (без `asChild`). |
| `EllipsisText` | `maxLines?: number` (по умолчанию `1`) | При `maxLines > 1` используется `line-clamp` — поддерживается не всеми браузерами. |

Большинство интерактивных компонентов (`Button`, `IconButton`, `CellAction`, `CellSimple`, `Avatar.*`, `Container`, `Flex`, `Grid`) принимают проп `asChild` (шаблон `Slot` из Radix), чтобы рендериться другим элементом, сохраняя стили и поведение компонента.

**Описано на сайте, но отсутствует в `src/**` на этом коммите — не используй:** `Dot`, `ToolButton` (удалены в 0.3.0, заменены на `Counter`, `Button` и `IconButton`), `Avatar.OnlineDot` (удалён, используй проп `onlineStatus` у `Avatar.Container`), `SearchInput` (в исходниках нет, пометки об удалении не найдено — считай, что его больше нет). Композиция `Profile` описана на сайте, но каталога `src/compositions/` в этом состоянии репозитория нет — не описывай её поведение.

## Хуки и помощники

| Экспорт | Сигнатура | Заметки |
|---|---|---|
| `usePlatform()` | `(): 'ios' \| 'android'` | |
| `useColorScheme()` | `(): 'light' \| 'dark'` | |
| `useAppearance()` | `(): { platform, colorScheme }` | |
| `useSystemColorScheme(params?)` | `(params?: { listenChanges?: boolean }): 'light' \| 'dark'` | Читает `prefers-color-scheme`; используется внутри `MaxUI`. |
| `useCallbackRef(callback)` | `<T extends (...a: any[]) => any>(callback: T \| undefined): T` | Ref для колбэка со стабильной идентичностью. |
| `useImageLoadingStatus({ src?, referrerPolicy? })` | `(): 'idle' \| 'loading' \| 'loaded' \| 'error'` | На нём построена логика запасного варианта в `Avatar.Image`. |
| `mergeRefs(...refs)`, `hasReactNode(value)`, `getSubtree(props)` | вспомогательные функции | Экспортируются на верхнем уровне — для сборки собственных полиморфных компонентов. |
| `Slot`, `SlotProps`, `Slottable` | реэкспорт из `@radix-ui/react-slot` | Тот же примитив, на котором построен `asChild`. |

## Пример экрана

Форма с полями ввода, переключателем и кнопкой внутри `Panel`, совместима с `@maxhub/max-ui@0.5.0` и `react@19.2.8`. **Проверено, что компилируется при `moduleResolution: "bundler"` (по умолчанию в Vite, webpack, CRA и Next.js) — почему `tsc --moduleResolution nodenext` отвергает тот же импорт, объяснено в разделе о подводных камнях сразу после кода.**

```tsx
import { createRoot } from 'react-dom/client';
import { useState } from 'react';
import {
  MaxUI,
  Panel,
  Flex,
  Typography,
  Input,
  Switch,
  Button,
} from '@maxhub/max-ui';
import '@maxhub/max-ui/dist/styles.css';

function SettingsForm() {
  const [name, setName] = useState('');
  const [notifyEnabled, setNotifyEnabled] = useState(true);

  return (
    <Panel mode="secondary" centeredX>
      <Flex direction="column" gap={12}>
        <Typography.Text variant="title">Profile settings</Typography.Text>

        <Input
          placeholder="Display name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          withClearButton
        />

        <Flex align="center" justify="space-between">
          <Typography.Text variant="body">Notifications</Typography.Text>
          <Switch
            checked={notifyEnabled}
            onChange={(event) => setNotifyEnabled(event.target.checked)}
          />
        </Flex>

        <Button stretched disabled={name.length === 0}>
          Save
        </Button>
      </Flex>
    </Panel>
  );
}

const container = document.getElementById('root');
if (container) {
  createRoot(container).render(
    <MaxUI>
      <SettingsForm />
    </MaxUI>,
  );
}

export default SettingsForm;
```

## Подводные камни

- **`moduleResolution: "nodenext"` и `"node16"` ломают именованные импорты из `@maxhub/max-ui@0.5.0`.** Проверено напрямую: `import { MaxUI, Panel, Button } from '@maxhub/max-ui'` не проходит проверку типов при `tsc --moduleResolution nodenext` с `error TS2305: Module '"@maxhub/max-ui"' has no exported member 'MaxUI'` (и так же для всех остальных компонентов). Причина: в пакете `dist/` лежит один собранный файл рантайма (`dist/index.js`), но полноценное дерево `.d.ts` по компонентам с относительными реэкспортами без расширений (`export * from './Avatar'` и т. п.) и без парных `.js` рядом по этим путям — а строгое разрешение модулей Node ESM этого требует. Тот же импорт спокойно компилируется при `moduleResolution: "bundler"`, который используется по умолчанию (или фактически работает так) в Vite, webpack, Create React App и Next.js. То есть проблема задевает только проекты, где `moduleResolution` явно выставлен в `node16` или `nodenext` (обычно это серверные ESM-библиотеки, а не типичные фронтенды мини-приложений). Если наткнулся на это, переключись на `"bundler"`, а не сообщай об ошибке в своём коде.
- CSS импортируется с побочным эффектом (`import '@maxhub/max-ui/dist/styles.css'`) — для этого нужен CSS-загрузчик сборщика. У обычного `tsc` нет ambient-типа для `*.css`, и он отклонит такой импорт, если проект не предоставит его сам (например, типы `vite/client`).
