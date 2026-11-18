# Управление хранилищем

Управляй cookie, localStorage, sessionStorage и состоянием хранилища браузера.

## Состояние хранилища

Сохраняй и восстанавливай полное состояние браузера, включая cookie и хранилище.

### Сохранение состояния

```bash
# сохранить в автоматически созданное имя файла (storage-state-{timestamp}.json)
playwright-cli state-save

# сохранить в заданное имя файла
playwright-cli state-save my-auth-state.json
```

### Восстановление состояния

```bash
# загрузить состояние хранилища из файла
playwright-cli state-load my-auth-state.json

# перезагрузи страницу, чтобы применить cookie
playwright-cli open https://example.com
```

### Формат файла состояния

Сохранённый файл содержит:

```json
{
  "cookies": [
    {
      "name": "session_id",
      "value": "abc123",
      "domain": "example.com",
      "path": "/",
      "expires": 1893456000,
      "httpOnly": true,
      "secure": true,
      "sameSite": "Lax"
    }
  ],
  "origins": [
    {
      "origin": "https://example.com",
      "localStorage": [
        { "name": "theme", "value": "dark" },
        { "name": "user_id", "value": "12345" }
      ]
    }
  ]
}
```

## Cookie

### Перечислить все cookie

```bash
playwright-cli cookie-list
```

### Отфильтровать cookie по домену

```bash
playwright-cli cookie-list --domain=example.com
```

### Отфильтровать cookie по пути

```bash
playwright-cli cookie-list --path=/api
```

### Получить конкретный cookie

```bash
playwright-cli cookie-get session_id
```

### Задать cookie

```bash
# простой cookie
playwright-cli cookie-set session abc123

# cookie с опциями
playwright-cli cookie-set session abc123 --domain=example.com --path=/ --httpOnly --secure --sameSite=Lax

# cookie со сроком действия (в формате Unix timestamp)
playwright-cli cookie-set remember_me token123 --expires=1893456000
```

### Удалить cookie

```bash
playwright-cli cookie-delete session_id

# только на одном домене, другие домены сохранят свой session_id
playwright-cli cookie-delete session_id --domain=example.com
```

### Очистить все cookie

```bash
playwright-cli cookie-clear
```

### Продвинутый случай: несколько cookie или свои опции

Для сложных сценариев, например добавления нескольких cookie сразу, используй `run-code`:

```bash
playwright-cli run-code "async page => {
  await page.context().addCookies([
    { name: 'session_id', value: 'sess_abc123', domain: 'example.com', path: '/', httpOnly: true },
    { name: 'preferences', value: JSON.stringify({ theme: 'dark' }), domain: 'example.com', path: '/' }
  ]);
}"
```

## LocalStorage

### Перечислить все элементы localStorage

```bash
playwright-cli localstorage-list
```

### Получить одно значение

```bash
playwright-cli localstorage-get token
```

### Задать значение

```bash
playwright-cli localstorage-set theme dark
```

### Задать значение JSON

```bash
playwright-cli localstorage-set user_settings '{"theme":"dark","language":"en"}'
```

### Удалить один элемент

```bash
playwright-cli localstorage-delete token
```

### Очистить весь localStorage

```bash
playwright-cli localstorage-clear
```

### Продвинутый случай: несколько операций

Для сложных сценариев, например установки нескольких значений сразу, используй `run-code`:

```bash
playwright-cli run-code "async page => {
  await page.evaluate(() => {
    localStorage.setItem('token', 'jwt_abc123');
    localStorage.setItem('user_id', '12345');
    localStorage.setItem('expires_at', Date.now() + 3600000);
  });
}"
```

## SessionStorage

### Перечислить все элементы sessionStorage

```bash
playwright-cli sessionstorage-list
```

### Получить одно значение

```bash
playwright-cli sessionstorage-get form_data
```

### Задать значение

```bash
playwright-cli sessionstorage-set step 3
```

### Удалить один элемент

```bash
playwright-cli sessionstorage-delete step
```

### Очистить sessionStorage

```bash
playwright-cli sessionstorage-clear
```

## IndexedDB

### Перечислить базы данных

```bash
playwright-cli run-code "async page => {
  return await page.evaluate(async () => {
    const databases = await indexedDB.databases();
    return databases;
  });
}"
```

### Удалить базу данных

```bash
playwright-cli run-code "async page => {
  await page.evaluate(() => {
    indexedDB.deleteDatabase('myDatabase');
  });
}"
```

## Частые приёмы

### Переиспользование состояния авторизации

```bash
# шаг 1: войти и сохранить состояние
playwright-cli open https://app.example.com/login
playwright-cli snapshot
playwright-cli fill e1 "user@example.com"
playwright-cli fill e2 "password123"
playwright-cli click e3

# сохранить состояние авторизации
playwright-cli state-save auth.json

# шаг 2: позже восстановить состояние и пропустить вход
playwright-cli state-load auth.json
playwright-cli open https://app.example.com/dashboard
# уже авторизован!
```

### Полный цикл сохранения и восстановления

```bash
# подготовить состояние авторизации
playwright-cli open https://example.com
playwright-cli eval "() => { document.cookie = 'session=abc123'; localStorage.setItem('user', 'john'); }"

# сохранить состояние в файл
playwright-cli state-save my-session.json

# ... позже, в новой сессии ...

# восстановить состояние
playwright-cli state-load my-session.json
playwright-cli open https://example.com
# cookie и localStorage восстановлены!
```

## Замечания по безопасности

- Никогда не коммить файлы состояния хранилища, содержащие токены авторизации.
- Добавь `*.auth-state.json` в `.gitignore`.
- Удаляй файлы состояния после завершения автоматизации.
- Для чувствительных данных используй переменные окружения.
- По умолчанию сессии работают в режиме в памяти, что безопаснее для чувствительных операций.
