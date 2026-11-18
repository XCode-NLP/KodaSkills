# Генерация тестов (план → генерация → лечение)

Сквозной процесс создания и поддержки тестов Playwright с `playwright-cli`. Каждое действие `playwright-cli` печатает эквивалентный код Playwright на TypeScript, и этот сгенерированный код — исходный материал для любого теста. Разделы ниже можно использовать независимо:

- **Как работает генерация** — основной механизм, на котором держится всё остальное: действия превращаются в TypeScript, плюс как добавлять проверки.
- **План** — исследуй приложение и создай файл спецификации с описанием того, что нужно проверить.
- **Генерация** — преврати спецификацию в файлы тестов Playwright. Обнови спецификацию, если она расплывчата или устарела.
- **Лечение** — разбери падающие тесты, исправь код, согласуй спецификацию с реальностью.

План, генерация и лечение опираются на один механизм: запусти `npx playwright test --debug=cli` в фоне, затем `playwright-cli attach tw-XXXX`, чтобы интерактивно управлять приостановленной страницей. Механику отладки и подключения смотри в [playwright-tests.md](playwright-tests.md).

---

## 0. Как работает генерация

Каждое действие, которое ты выполняешь через `playwright-cli`, порождает соответствующий код Playwright на TypeScript. Этот код появляется в выводе, и его можно копировать прямо в файлы тестов.

```bash
# запустить сессию
playwright-cli open https://example.com/login

# снять снимок, чтобы увидеть элементы
playwright-cli snapshot
# вывод показывает: e1 [textbox "Email"], e2 [textbox "Password"], e3 [button "Sign In"]

# заполнить поля формы — код генерируется автоматически
playwright-cli fill e1 "user@example.com"
# Ran Playwright code:
# await page.getByRole('textbox', { name: 'Email' }).fill('user@example.com');

playwright-cli fill e2 "password123"
# Ran Playwright code:
# await page.getByRole('textbox', { name: 'Password' }).fill('password123');

playwright-cli click e3
# Ran Playwright code:
# await page.getByRole('button', { name: 'Sign In' }).click();
```

### Сборка файла теста

Собери сгенерированный код в тест Playwright:

```typescript
import { test, expect } from '@playwright/test';

test('login flow', async ({ page }) => {
  // Generated code from playwright-cli session:
  await page.goto('https://example.com/login');
  await page.getByRole('textbox', { name: 'Email' }).fill('user@example.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('password123');
  await page.getByRole('button', { name: 'Sign In' }).click();

  // Add assertions
  await expect(page).toHaveURL(/.*dashboard/);
});
```

### Используй семантические локаторы

Сгенерированный код по возможности использует локаторы по роли, они устойчивее:

```typescript
// Generated (good - semantic)
await page.getByRole('button', { name: 'Submit' }).click();

// Avoid (fragile - CSS selectors)
await page.locator('#submit-btn').click();
```

### Исследуй до записи

Снимай снимки, чтобы понять структуру страницы до записи действий:

```bash
playwright-cli open https://example.com
playwright-cli snapshot
# изучи структуру элементов
playwright-cli click e5
```

### Добавляй проверки вручную

Сгенерированный код фиксирует действия, но не проверки. Добавляй ожидания в тест через один из рекомендуемых матчеров:

- `toBeVisible()` — элемент отрисован и виден;
- `toHaveText(text)` — текстовое содержимое элемента совпадает;
- `toHaveValue(value) / toBeEmpty()` — значение input или select совпадает;
- `toBeChecked() / not.toBeChecked()` — состояние флажка совпадает;
- `toMatchAriaSnapshot(snapshot)` — страница (или локатор) совпадает с частью снимка доступности.

Используй `playwright-cli generate-locator <target>`, чтобы получить выражение локатора для проверки, и команды snapshot или eval, чтобы снять ожидаемое значение.

Когда проверяешь текстовое содержимое, следи, чтобы сгенерированный локатор не содержал текст самого элемента. `getByTestId()` или `getByLabel()` обычно хорошо работают с проверкой текста. Когда локатор основан на тексте, предпочитай `toBeVisible()`.

Снимок для сравнения не обязан содержать всю информацию — фиксируй только то, что нужно для проверки. Для нестабильных значений можно использовать регулярные выражения.

```bash
# получить устойчивый локатор элемента по ссылке для проверки
playwright-cli --raw generate-locator e5
# getByRole('button', { name: 'Submit' })

# снять ожидаемое текстовое содержимое для toHaveText
playwright-cli --raw eval "el => el.textContent" e5

# снять ожидаемое значение поля для toHaveValue/toBeEmpty
playwright-cli --raw eval "el => el.value" e5

# снять ожидаемый снимок доступности для toMatchAriaSnapshot/toBeChecked
# (всей страницы или по ссылке на область)
playwright-cli --raw snapshot
playwright-cli --raw snapshot e5
```

```typescript
// Generated action
await page.getByRole('button', { name: 'Submit' }).click();

// Manual assertions using the outputs above:
await expect(page.getByRole('alert', { name: 'Success' })).toBeVisible();
await expect(page.getByTestId('main-header')).toHaveText('Welcome, user');
await expect(page.getByRole('textbox', { name: 'Email' })).toHaveValue('user@example.com');
await expect(page.getByRole('checkbox', { name: 'Enable notifications' })).toBeChecked();

// toMatchAriaSnapshot on the whole page, finds a matching region
await expect(page).toMatchAriaSnapshot(`
  - heading "Welcome, user"
  - link /\\d+ new messages?/
  - button "Sign out"
`);

// toMatchAriaSnapshot scoped to a region
await expect(page.getByRole('navigation')).toMatchAriaSnapshot(`
  - link "Home"
  - link /\\d+ new messages?/
  - link "Profile"
`);
```

---

## 1. Планирование

Цель: получить файл спецификации (например, `specs/<feature>.plan.md`) с перечнем сценариев для проверки. **Всегда** записывай спецификацию в файл.

### 1.1 Предусловие: рабочая область

Прежде всего проверь, что в рабочей области установлен Playwright:

```bash
# любая из этих команд подтверждает рабочую область
test -f playwright.config.ts || test -f playwright.config.js
npx --no-install playwright --version
```

Если Playwright не установлен, разверни его и дай пользователю выбрать значения по умолчанию:

```bash
npm init playwright@latest
```

### 1.2 Предусловие: затравочный тест

**Затравочный тест** — минимальный тест, который приводит страницу в состояние, с которого начинается каждый сценарий: переход в приложение, нужный вход, флаги возможностей и т. д. Сценарии исходят из чистого старта *после* затравки. `--debug=cli` приостанавливает выполнение *внутри* этого теста, поэтому затравка — начало каждой сессии планирования и генерации.

Минимально достаточная затравка:

```ts
// tests/seed.spec.ts
import { test } from '@playwright/test';

test('seed', async ({ page }) => {
  await page.goto('https://example.com/');
});
```

Предпочтительный вариант — вынести переход в фикстуру, чтобы тесты сценариев её переиспользовали:

```ts
// tests/fixtures.ts
import { test as baseTest } from '@playwright/test';
export { expect } from '@playwright/test';

export const test = baseTest.extend({
  page: async ({ page }, use) => {
    await page.goto('https://example.com/');
    await use(page);
  },
});
```

```ts
// tests/seed.spec.ts
import { test } from './fixtures';

test('seed', async ({ page }) => {
  // Fixture already navigates. This empty body tells agents where to start.
});
```

Если затравки нет, создай её, как минимум с переходом в приложение.

### 1.3 Исследуй приложение

Запусти приложение через затравку в фоне и подключись:

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/seed.spec.ts --debug=cli
# дождись "Debugging Instructions" и имени сессии tw-XXXX
playwright-cli attach tw-XXXX
```

Продолжи выполнение, чтобы затравка прошла, затем исследуй приложение:

```bash
playwright-cli resume                   # продолжить, чтобы затравочный тест выполнился полностью
playwright-cli snapshot                 # инвентаризация интерактивных элементов
playwright-cli click e5                 # пройди по сценарию
playwright-cli eval "location.href"     # прочитай URL или состояние
playwright-cli show --annotate          # попроси пользователя указать на что-то
```

Составь карту:

- интерактивных поверхностей (формы, кнопки, списки, фильтры, модальные окна);
- основных пользовательских путей от начала до конца;
- крайних случаев: пустые состояния, ошибки валидации, очень длинный ввод, граничные значения;
- сохранения состояния: перезагрузка, local/session storage, фрагменты URL;
- навигации: какие элементы меняют URL, как работают кнопки «назад» и «вперёд».

**Важно**: не открывай URL приложения просто через playwright-cli, всегда иди через тест, чтобы воспроизвести его особую настройку.
**Важно**: останови фоновый тест, когда закончишь исследование.

### 1.4 Напиши файл спецификации

Сохрани в `specs/<feature>.plan.md`. Используй такую структуру:

```markdown
# <Feature> Test Plan

## Application Overview

<One paragraph describing what the feature does and why it matters.>

## Test Scenarios

### 1. <Group Name>

**Seed:** `tests/seed.spec.ts`

#### 1.1. <kebab-case-scenario-name>

**File:** `tests/<group>/<kebab-case-scenario-name>.spec.ts`

**Steps:**
  1. <Concrete user step>
    - expect: <observable outcome>
    - expect: <another observable outcome>
  2. <Next step>
    - expect: <outcome>

#### 1.2. <next-scenario>
...

### 2. <Next Group>

**Seed:** `tests/seed.spec.ts`
...
```

Рекомендации:

- Каждый сценарий независим и начинается с чистого состояния затравки — никогда не выстраивай сценарии в цепочку.
- Имена сценариев в kebab-case и совпадают с именем файла теста (`should-add-single-todo` → `should-add-single-todo.spec.ts`).
- Покрывай успешный путь, крайние случаи, валидацию, негативные сценарии, сохранение состояния.
- Пиши шаги на уровне пользователя («введи "Buy milk" в поле»), а не на уровне API («вызови `fill`»).
- Наблюдаемые результаты выноси в пункты `- expect:`; каждый из них при генерации становится проверкой.

---

## 2. Генерация

Цель: взять файл спецификации и получить файлы тестов Playwright. При необходимости обнови спецификацию, если она разошлась с реальностью.

### 2.1 Входные данные

- **Файл спецификации**, например `specs/basic-operations.plan.md`.
- **Цель**: один сценарий (например, `1.2`), целая группа (`1`) или все.
- **Файл затравки**, берётся из строки `**Seed:**` группы сценария.

### 2.2 Сгенерируй один сценарий

Для каждого целевого сценария по очереди (никогда параллельно — сценарии делят сессию затравки):

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test <seed-file> --debug=cli   # в фоне
playwright-cli attach tw-XXXX
# resume
```

**Не** открывай URL приложения просто через playwright-cli, всегда иди через тест, чтобы воспроизвести его особую настройку.

Пройди пункты `Steps:` сценария один за другим через `playwright-cli`, считая спецификацию планом, а живое приложение — источником истины. Если шаг расплывчат («нажми кнопку» — какую?), ссылается на элемент, которого больше нет, или противоречит фактическому поведению приложения, решай сам: обнови спецификацию под то, что приложение действительно делает, и продолжай. Править спецификацию посреди генерации — это ожидаемо.

Каждое действие печатает эквивалентный код Playwright на TypeScript (см. [Как работает генерация](#0-как-работает-генерация)):

```bash
playwright-cli snapshot                         # найти ссылки
playwright-cli fill e3 "John Doe"               # -> page.getByRole('textbox', {...}).fill(...)
playwright-cli press Enter
playwright-cli click e7
```

Для каждого пункта `- expect:` добавь явную проверку. Подробности в разделе [Как работает генерация](#0-как-работает-генерация).

Собери сгенерированный код и запиши файл теста по пути из спецификации:

```ts
// spec: specs/basic-operations.plan.md
// seed: tests/seed.spec.ts
import { test, expect } from './fixtures';   // или '@playwright/test', если файла фикстур нет

test.describe('Signing in and out', () => {
  test('should sign in', async ({ page }) => {
    // 1. Navigate to the application
    // (handled by the seed fixture)

    // 2. Type 'John Doe' into the username field
    await page.getByRole('textbox', { name: 'username' }).fill('John Doe');

    // 3. Type password
    await page.getByRole('textbox', { name: 'password' }).fill('TestPassword');

    // 4. Press Enter to submit
    await page.getByRole('textbox', { name: 'password' }).press('Enter');

    await expect(page.getByRole('heading')).toContainText('Welcome, John Doe!');
  });
});
```

Правила:

- **Один тест на файл.** Путь файла, имя describe и имя теста берутся из спецификации дословно (без порядкового номера).
- Перед действиями каждого пронумерованного шага ставь комментарий `// N. <текст шага>`.
- Имя группы describe бери из спецификации дословно (без порядкового номера `1.`).
- Импортируй из `./fixtures`, если в проекте есть такой файл, иначе из `@playwright/test`.
- **Важно**: закрой сессию CLI и останови фоновый тест перед переходом к следующему сценарию.

### 2.3 Сгенерируй несколько сценариев

Повтори 2.2 для целевых сценариев по одному, перезапуская затравку между ними, чтобы каждый тест начинался с чистой страницы. Убедись, что каждый запуск теста остановлен до начала следующего.

### 2.4 Запусти сгенерированные тесты

После генерации запусти новые тесты один раз:

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/<group>/<scenario>.spec.ts
```

Любой сбой — в раздел 3.

---

## 3. Лечение

Цель: исправить падающие тесты и обновить спецификацию, если предполагаемое поведение приложения изменилось.

### 3.1 Найди падающие тесты

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test
```

Запиши список падающих записей `<file>:<line>` и обрабатывай их по одной. Не пытайся исправлять параллельно — общее состояние и одна сессия CLI делают это хрупким.

### 3.2 Отладь один сбой

Запусти единственный падающий тест в режиме отладки в фоне и подключись:

```bash
PLAYWRIGHT_HTML_OPEN=never npx playwright test tests/<group>/<scenario>.spec.ts:<line> --debug=cli
# дождись "Debugging Instructions" и имени сессии tw-XXXX
playwright-cli attach tw-XXXX
```

Тест приостановлен на старте. Пройди шаги вперёд или выполни до места прямо перед падающим действием или проверкой, затем разбирайся:

```bash
playwright-cli snapshot                # элемент изменился, переехал или переименован?
playwright-cli console                 # ошибки на стороне приложения?
playwright-cli requests                # запрос упал? неверные данные?
playwright-cli show --annotate         # попроси пользователя указать место
```

Частые причины: смещение селектора, новый элемент-обёртка, переименование метки или ARIA, тайминг (переход, асинхронная загрузка), обновлённый текст проверки в приложении, утечка тестовых данных между запусками.

Отрепетируй исправленное взаимодействие через `playwright-cli` — сгенерированный в выводе код ты вставишь обратно в тест.

### 3.3 Внеси исправление

Отредактируй файл теста: обнови локатор, проверку, порядок шагов или входные данные под исправленное поведение. Останови фоновый запуск отладки. Запусти тест ещё раз, чтобы убедиться, что он зелёный.

Никогда не пропускай хуки и не добавляй задержки как исправление. Никогда не используй `networkidle`.

### 3.4 Согласуй со спецификацией

Открой спецификацию, на которую ссылается заголовок `// spec:` в файле теста, и найди сценарий, соответствующий тесту.

- **Исправление чисто техническое** (смещение локатора, более удачная форма проверки), а описанное в спецификации поведение на уровне пользователя по-прежнему соответствует приложению → спецификацию не трогай.
- **Исправление изменило видимые пользователю шаги, входные данные, порядок или ожидаемые результаты**, описанные в спецификации → обнови спецификацию под реальность. Держи идентификатор сценария и путь файла стабильными; меняются только строки шагов и ожиданий.
- **Непонятно, намеренно ли изменилось приложение** (спецификация устарела) **или это регрессия** (тест был прав, приложение — нет) → **остановись и спроси пользователя**. Приведи:
  - идентификатор сценария (например, `2.3`);
  - строки спецификации, которые больше не совпадают;
  - наблюдаемое поведение приложения (цитата из снимка или конкретный результат).

Только после ответа пользователя либо обнови спецификацию (намеренное изменение), либо оформи или отметь тест как покрывающий баг (регрессию).

### 3.5 Итерации и отказ от попыток

- Исправляй сбои по одному, запуская тесты после каждого.
- Если после тщательного разбора ты уверен, что тест верен, а приложение — нет, *и* пользователь подтвердил, что это баг: пометь тест как `test.fixme(...)` с комментарием, ссылающимся на решение пользователя или на issue. Никогда не пропускай тест молча.

---

## Перекрёстные ссылки

| Что нужно | Где смотреть |
|---|---|
| Механика `--debug=cli` и подключения | [playwright-tests.md](playwright-tests.md) |
| Подмена запросов при исследовании и генерации | [request-mocking.md](request-mocking.md) |
| Управление сессией браузера CLI | [session-management.md](session-management.md) |
