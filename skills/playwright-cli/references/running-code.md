# Запуск своего кода Playwright

Используй `run-code`, чтобы выполнить произвольный код Playwright для продвинутых сценариев, не покрытых командами CLI.

## Синтаксис

```bash
playwright-cli run-code "async page => {
  // Your Playwright code here
  // Access page.context() for browser context operations
}"
```

Можно также загрузить функцию из файла:

```bash
playwright-cli run-code --filename=./my-script.js
```


Код должен быть одним выражением-функцией: он оборачивается в `(...)` и вычисляется.
Синтаксис import/export/require не поддерживается.

Код выполняется в изолированном контексте, а не в полноценном окружении Node.js. `require`, `process` и модули Node
недоступны. Доступны таймеры (`setTimeout`, `setInterval`), `fetch`, `URL`, `Buffer`, `crypto`, `AbortController`, `TextEncoder`
и `TextDecoder`.

## Геолокация

```bash
# выдать разрешение на геолокацию и задать местоположение
playwright-cli run-code "async page => {
  await page.context().grantPermissions(['geolocation']);
  await page.context().setGeolocation({ latitude: 37.7749, longitude: -122.4194 });
}"

# задать местоположение Лондона
playwright-cli run-code "async page => {
  await page.context().grantPermissions(['geolocation']);
  await page.context().setGeolocation({ latitude: 51.5074, longitude: -0.1278 });
}"

# сбросить подмену геолокации
playwright-cli run-code "async page => {
  await page.context().clearPermissions();
}"
```

## Разрешения

```bash
# выдать несколько разрешений
playwright-cli run-code "async page => {
  await page.context().grantPermissions([
    'geolocation',
    'notifications',
    'camera',
    'microphone'
  ]);
}"

# выдать разрешения для конкретного источника
playwright-cli run-code "async page => {
  await page.context().grantPermissions(['clipboard-read'], {
    origin: 'https://example.com'
  });
}"
```

## Подмена медиавозможностей

```bash
# тёмная цветовая схема
playwright-cli run-code "async page => {
  await page.emulateMedia({ colorScheme: 'dark' });
}"

# светлая цветовая схема
playwright-cli run-code "async page => {
  await page.emulateMedia({ colorScheme: 'light' });
}"

# уменьшенное движение
playwright-cli run-code "async page => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
}"

# медиа для печати
playwright-cli run-code "async page => {
  await page.emulateMedia({ media: 'print' });
}"
```

## Стратегии ожидания

```bash
# дождаться, пока сеть успокоится
playwright-cli run-code "async page => {
  await page.waitForLoadState('networkidle');
}"

# дождаться конкретного элемента
playwright-cli run-code "async page => {
  await page.locator('.loading').waitFor({ state: 'hidden' });
}"

# дождаться, пока функция вернёт true
playwright-cli run-code "async page => {
  await page.waitForFunction(() => window.appReady === true);
}"

# ждать с таймаутом
playwright-cli run-code "async page => {
  await page.locator('.result').waitFor({ timeout: 10000 });
}"
```

## Фреймы и iframe

```bash
# работать с iframe
playwright-cli run-code "async page => {
  const frame = page.locator('iframe#my-iframe').contentFrame();
  await frame.locator('button').click();
}"

# получить все фреймы
playwright-cli run-code "async page => {
  const frames = page.frames();
  return frames.map(f => f.url());
}"
```

## Скачивание файлов

```bash
# обработать скачивание файла
playwright-cli run-code "async page => {
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download' }).click();
  const download = await downloadPromise;
  await download.saveAs('./downloaded-file.pdf');
  return download.suggestedFilename();
}"
```

## Буфер обмена

```bash
# прочитать буфер обмена (нужно разрешение)
playwright-cli run-code "async page => {
  await page.context().grantPermissions(['clipboard-read']);
  return await page.evaluate(() => navigator.clipboard.readText());
}"

# записать в буфер обмена
playwright-cli run-code "async page => {
  await page.evaluate(text => navigator.clipboard.writeText(text), 'Hello clipboard!');
}"
```

## Информация о странице

```bash
# получить заголовок страницы
playwright-cli run-code "async page => {
  return await page.title();
}"

# получить текущий URL
playwright-cli run-code "async page => {
  return page.url();
}"

# получить содержимое страницы
playwright-cli run-code "async page => {
  return await page.content();
}"

# получить размер области просмотра
playwright-cli run-code "async page => {
  return page.viewportSize();
}"
```

## Выполнение JavaScript

```bash
# выполнить JavaScript и вернуть результат
playwright-cli run-code "async page => {
  return await page.evaluate(() => {
    return {
      userAgent: navigator.userAgent,
      language: navigator.language,
      cookiesEnabled: navigator.cookieEnabled
    };
  });
}"

# передать аргументы в evaluate
playwright-cli run-code "async page => {
  const multiplier = 5;
  return await page.evaluate(m => document.querySelectorAll('li').length * m, multiplier);
}"
```

## Обработка ошибок

```bash
# try-catch в run-code
playwright-cli run-code "async page => {
  try {
    await page.getByRole('button', { name: 'Submit' }).click({ timeout: 1000 });
    return 'clicked';
  } catch (e) {
    return 'element not found';
  }
}"
```

Ошибки в обработчиках событий сообщаются как ошибки консоли.

## Сложные сценарии

```bash
# войти и сохранить состояние
playwright-cli run-code "async page => {
  await page.goto('https://example.com/login');
  await page.getByRole('textbox', { name: 'Email' }).fill('user@example.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('secret');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('**/dashboard');
  await page.context().storageState({ path: 'auth.json' });
  return 'Login successful';
}"

# собрать данные с нескольких страниц
playwright-cli run-code "async page => {
  const results = [];
  for (let i = 1; i <= 3; i++) {
    await page.goto(\`https://example.com/page/\${i}\`);
    const items = await page.locator('.item').allTextContents();
    results.push(...items);
  }
  return results;
}"
```
