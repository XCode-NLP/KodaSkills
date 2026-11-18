# Запись видео

Записывай сессии автоматизации браузера на видео для отладки, документации или проверки. На выходе — WebM (кодек VP8/VP9).

## Базовая запись

```bash
# сначала открой браузер
playwright-cli open

# начни запись; --cursor рисует анимированный курсор мыши, который доезжает до каждой точки действия
# и растягивает действия на 800 мс, чтобы курсор успел доехать
playwright-cli video-start demo.webm --cursor --fps=60

# добавь маркер главы для перехода между разделами
playwright-cli video-chapter "Getting Started" --description="Opening the homepage" --duration=2000

# переходи и выполняй действия
playwright-cli goto https://example.com
playwright-cli snapshot
playwright-cli click e1

# добавь ещё одну главу
playwright-cli video-chapter "Filling Form" --description="Entering test data" --duration=2000
playwright-cli fill e2 "test input"

# останови и сохрани
playwright-cli video-stop
```

## Курсор, подсветка цели и точка клика

Для каждого действия можно нарисовать три украшения: **курсор** мыши, рамку **подсветки** вокруг
целевого элемента и маркер-**точку** в месте клика. Подпись-**заголовок** с названием действия
появляется вместе с `video-show-actions`. Курсор — единственное, что включает `video-start --cursor`;
остальное включается отдельно и оформляется обычными CSS-объявлениями, так что выглядит ровно так,
как ты хочешь.

```bash
# только курсор, больше ничего на экране
playwright-cli video-start demo.webm --cursor

# подпись действия, красная точка клика и тёмная рамка вокруг цели
playwright-cli video-show-actions --duration=800 --position=top-right \
  --point-style="width: 20px; height: 20px; border-radius: 50%; background: rgba(255,0,0,.7)" \
  --highlight-style="outline: 2px solid #333; background: rgba(0,128,255,.15)" \
  --title-style="font-size: 16px"

# перестать аннотировать действия
playwright-cli video-hide-actions
```

Те же опции доступны программно, и для сценариев-витрин это лучший выбор:

```js
await page.screencast.showActions({
  // 'pointer' (по умолчанию) анимирует курсор от предыдущей точки действия, 'none' скрывает его.
  cursor: 'pointer',
  // Как долго украшения остаются на экране. На эту же задержку растягиваются действия, по умолчанию 500 мс.
  duration: 800,
  // Куда ставится заголовок действия: top-left, top, top-right, bottom-left, bottom, bottom-right.
  position: 'top-right',
  style: {
    // Маркер в точке клика. Элемент нулевого размера и центрирован на точке,
    // поэтому задай ему размер или рисуй вокруг точки через box-shadow. Скрыт, если не задан.
    point: 'width: 20px; height: 20px; border-radius: 50%; background: rgba(255, 0, 0, .7)',
    // Рамка, накрывающая целевой элемент. Скрыта, если не задана.
    // Предпочитай `outline` вместо `border`, он не уменьшает рамку.
    highlight: 'outline: 2px solid #333; background: rgba(0, 128, 255, .15)',
    // Заголовок действия. Используй 'display: none', чтобы оставить курсор, но убрать подпись.
    title: 'font-size: 16px',
  },
});
```

Замечания:
- Все украшения плавно исчезают за `duration`. Переопредели `animation` в стиле, чтобы сделать иначе.
- Курсор остаётся на экране в последней точке действия между действиями и при переходах
  и движется по слегка изогнутой траектории, поэтому читается как рука, двигающая мышь.
- Вызови `page.screencast.hideActions()`, чтобы перестать аннотировать и скрыть курсор.

## Рекомендации

### 1. Используй описательные имена файлов

```bash
# включай контекст в имя файла
playwright-cli video-start recordings/login-flow-2024-01-15.webm
playwright-cli video-start recordings/checkout-test-run-42.webm
```

### 2. Записывай сценарии-витрины целиком

Когда записываешь видео для пользователя или как доказательство работы, лучше создать фрагмент кода и выполнить его через run-code.
Это позволяет вставлять уместные паузы между действиями и аннотировать видео. Для этого есть новые API Playwright.

1) Пройди сценарий через CLI и запиши все локаторы и действия. Эти локаторы понадобятся, чтобы запросить их ограничивающие рамки для подсветки.
2) Создай файл с нужным сценарием для видео (ниже). Используй pressSequentially с задержкой для красивого набора, делай разумные паузы.
3) Запусти `playwright-cli run-code --filename your-script.js`.

**Важно**: у наложений `pointer-events: none` — они не мешают взаимодействию со страницей. Можно спокойно держать постоянные наложения видимыми, пока кликаешь, заполняешь поля и выполняешь любые действия на странице.

```js
async page => {
  await page.screencast.start({ path: 'video.webm', size: { width: 1280, height: 800 }, fps: 60 });
  // Показать курсор и отметить точку клика, растянуть действия на 800 мс.
  await page.screencast.showActions({
    duration: 800,
    style: {
      point: 'width: 20px; height: 20px; border-radius: 50%; background: rgba(255, 0, 0, .7)',
      title: 'display: none',
    },
  });
  await page.goto('https://demo.playwright.dev/todomvc');

  // Показать карточку главы — размывает страницу и показывает диалог.
  // Блокирует до истечения duration, затем удаляется автоматически.
  // Используй это для простых случаев, но всегда можешь вручную собрать своё красивое
  // наложение через await page.screencast.showOverlay().
  await page.screencast.showChapter('Adding Todo Items', {
    description: 'We will add several items to the todo list.',
    duration: 2000,
  });

  // Выполнить действие
  await page.getByRole('textbox', { name: 'What needs to be done?' }).pressSequentially('Walk the dog', { delay: 60 });
  await page.getByRole('textbox', { name: 'What needs to be done?' }).press('Enter');
  await page.waitForTimeout(1000);

  // Показать следующую главу
  await page.screencast.showChapter('Verifying Results', {
    description: 'Checking the item appeared in the list.',
    duration: 2000,
  });

  // Добавить постоянную аннотацию, которая остаётся, пока ты выполняешь действия.
  // У наложений pointer-events: none, поэтому они не блокируют клики.
  const annotation = await page.screencast.showOverlay(`
    <div style="position: absolute; top: 8px; right: 8px;
      padding: 6px 12px; background: rgba(0,0,0,0.7);
      border-radius: 8px; font-size: 13px; color: white;">
      ✓ Item added successfully
    </div>
  `);

  // Выполнить ещё действия, пока аннотация видна
  await page.getByRole('textbox', { name: 'What needs to be done?' }).pressSequentially('Buy groceries', { delay: 60 });
  await page.getByRole('textbox', { name: 'What needs to be done?' }).press('Enter');
  await page.waitForTimeout(1500);

  // Убрать аннотацию, когда закончил
  await annotation.dispose();

  // Можно также подсвечивать нужные локаторы и давать контекстные аннотации.
  const bounds = await page.getByText('Walk the dog').boundingBox();
  await page.screencast.showOverlay(`
    <div style="position: absolute;
      top: ${bounds.y}px;
      left: ${bounds.x}px;
      width: ${bounds.width}px;
      height: ${bounds.height}px;
      border: 1px solid red;">
    </div>
    <div style="position: absolute;
      top: ${bounds.y + bounds.height + 5}px;
      left: ${bounds.x + bounds.width / 2}px;
      transform: translateX(-50%);
      padding: 6px;
      background: #808080;
      border-radius: 10px;
      font-size: 14px;
      color: white;">Check it out, it is right above this text
    </div>
  `, { duration: 2000 });

  await page.screencast.stop();
}
```

Проявляй изобретательность: наложения — мощный инструмент.

### Сводка API наложений

| Метод | Назначение |
|--------|----------|
| `page.screencast.showChapter(title, { description?, duration?, styleSheet? })` | Полноэкранная карточка главы с размытым фоном — идеальна для переходов между разделами |
| `page.screencast.showOverlay(html, { duration? })` | Своё HTML-наложение — для подписей, меток, подсветок |
| `disposable.dispose()` | Убрать постоянное наложение, добавленное без duration |
| `page.screencast.hideOverlays()` / `page.screencast.showOverlays()` | Временно скрыть или показать все наложения |
| `page.screencast.showActions({ cursor, duration, position, style })` | Курсор, точка клика, подсветка цели и заголовок действия |
| `page.screencast.hideActions()` | Перестать аннотировать действия и скрыть курсор |

### 3. Прикрепи запись к pull request

Запись сценария-витрины — лучшее доказательство работы для изменения, видимого пользователю. GitHub принимает WebM как есть, поэтому, когда запись выглядит как надо, прикрепи её через `gh` 2.99+, а не описывай сценарий словами:

```bash
gh pr create --title "feat(todo): add items inline" --body-file body.md --attach ./demo.webm
gh pr comment 123 --body "Walkthrough of the new flow." --attach ./demo.webm
gh issue comment 456 --body "Recording of the repro steps." --attach ./repro.webm
```

`gh` добавляет вложения без ссылок в конец тела, а для обзора сценария это подходящее место. Видео ограничены 10 МБ на бесплатных планах и 100 МБ на платных, поэтому держи сценарий сфокусированным, записывай в умеренном размере, например 1280x800, и убирай главы, которые ничего не добавляют к рассказу. Полный набор команд, включая прикрепление артефактов тестов из CI, смотри в [pr-attachments.md](pr-attachments.md).

## Трассировка и видео

| Возможность | Видео | Трассировка |
|---------|-------|---------|
| Результат | файл WebM | файл трассы (открывается в Trace Viewer) |
| Что показывает | визуальную запись | снимки DOM, сеть, консоль, действия |
| Сценарий | демонстрации, документация | отладка, анализ |
| Размер | Больше | Меньше |

## Ограничения

- Запись добавляет небольшие накладные расходы к автоматизации.
- Большие записи могут занимать много места на диске.
