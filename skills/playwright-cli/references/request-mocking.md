# Подмена сетевых запросов

Перехватывай, подменяй, изменяй и блокируй сетевые запросы.

## Команды маршрутов в CLI

```bash
# подменить с заданным статусом
playwright-cli route "**/*.jpg" --status=404

# подменить с телом JSON
playwright-cli route "**/api/users" --body='[{"id":1,"name":"Alice"}]' --content-type=application/json

# подменить с заданными заголовками
playwright-cli route "**/api/data" --body='{"ok":true}' --header="X-Custom: value"

# убрать заголовки из запросов
playwright-cli route "**/*" --remove-header=cookie,authorization

# перечислить активные маршруты
playwright-cli route-list

# убрать один маршрут или все маршруты
playwright-cli unroute "**/*.jpg"
playwright-cli unroute
```

## Шаблоны URL

```
**/api/users           - Точное совпадение пути
**/api/*/details       - Шаблон в пути
**/*.{png,jpg,jpeg}    - Совпадение по расширениям файлов
**/search?q=*          - Совпадение по параметрам запроса
```

## Продвинутая подмена через run-code

Для условных ответов, разбора тела запроса, изменения ответа или задержек:

### Условный ответ в зависимости от запроса

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/login', route => {
    const body = route.request().postDataJSON();
    if (body.username === 'admin') {
      route.fulfill({ body: JSON.stringify({ token: 'mock-token' }) });
    } else {
      route.fulfill({ status: 401, body: JSON.stringify({ error: 'Invalid' }) });
    }
  });
}"
```

### Изменение настоящего ответа

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/user', async route => {
    const response = await route.fetch();
    const json = await response.json();
    json.isPremium = true;
    await route.fulfill({ response, json });
  });
}"
```

### Имитация сетевых сбоев

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/offline', route => route.abort('internetdisconnected'));
}"
# Варианты: connectionrefused, timedout, connectionreset, internetdisconnected
```

### Задержка ответа

```bash
playwright-cli run-code "async page => {
  await page.route('**/api/slow', async route => {
    await new Promise(r => setTimeout(r, 3000));
    route.fulfill({ body: JSON.stringify({ data: 'loaded' }) });
  });
}"
```
