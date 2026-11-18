# Сервер

## Проект и жизненный цикл

Импортируй `MCPServer` из `mcp-use`. Экспортируй сервер как экспорт по умолчанию, чтобы
`mcp-use dev`, `mcp-use build` и `mcp-use start` управляли слушателем и конвейером
представлений. Вызывай `server.listen()` только в явно самостоятельной программе.

Используй пакетный менеджер проекта и существующие скрипты. Для нового стабильного проекта
создавай заготовку, а не воспроизводи вручную обвязку фреймворка:

```bash
npx create-mcp-use-app@latest my-server --template mcp-server
```

## Инструменты

Используй валидатор, совместимый со Standard Schema: Zod, ArkType или Valibot. Описывай поля,
когда описание помогает клиенту или модели выбрать корректный ввод.

```ts
import { MCPServer } from "mcp-use";
import { z } from "zod";

const server = new MCPServer({ name: "inventory", version: "1.0.0" });

export const lookupInventory = server.tool(
  {
    name: "lookup-inventory",
    description: "Return available inventory for one SKU",
    inputSchema: z.object({ sku: z.string().describe("Inventory SKU") }),
    outputSchema: z.object({ sku: z.string(), available: z.number().int() }),
    annotations: { readOnlyHint: true, openWorldHint: false },
  },
  async ({ sku }) => {
    const data = { sku, available: await inventory.count(sku) };
    return {
      content: [{ type: "text", text: JSON.stringify(data) }],
      structuredContent: data,
    };
  },
);
```

Используй `visibility: "app"` для вспомогательных инструментов, предназначенных представлениям и
скрытых от модели. Считай аннотации подсказками о поведении, а не средствами управления доступом.

## Каналы результата

- Краткий читаемый моделью вывод кладите в `content`.
- Проверенный по схеме JSON кладите в `structuredContent`, когда есть `outputSchema`.
- Данные, специфичные для вызова и видимые только представлению, кладите в `_meta` результата;
  проверяй или сужай их в представлении.
- Возвращай `isError: true` с полезным `content` для ожидаемых операционных сбоев.
- Выбрасывай исключение только для неожиданных сбоев, которые должны проявиться как ошибки
  протокола.

## Ресурсы и подсказки

Используй `server.resource()` для одного стабильного URI и `server.resourceTemplate()` для
семейства URI. Возвращай `{ contents: [...] }`; каждая запись должна содержать свой URI и либо
текст, либо blob в base64. Колбэк шаблона получает `(uri, params, ctx)`, а значения шаблона могут
быть `string | string[]`.

Используй `server.prompt()` для готовых для модели сообщений. Аргументы подсказки используют
`schema`, а не `inputSchema` инструмента, и колбэк возвращает `{ messages: [...] }`. Оборачивай
строковое поле в `completable()`, когда клиенты должны получать подсказки, не ограничивая другие
допустимые строки.

## Промежуточное ПО MCP и контекст запроса

Регистрируй промежуточное ПО протокола через `server.use("mcp:<method>", handler)`. Используй
самую узкую операцию, вызывай `next()` и возвращай его результат, если не заменяешь его намеренно.

```ts
server.use("mcp:tools/call", async (ctx, next) => {
  const startedAt = Date.now();
  const result = await next();
  console.log(`${ctx.params.name}: ${Date.now() - startedAt}ms`);
  return result;
});
```

Колбэки инструментов, ресурсов и подсказок получают контекст, ограниченный запросом. Используй
`ctx.signal` для отмены, `ctx.client` для самостоятельно заявленных возможностей клиента и
`ctx.auth` только когда настроен OAuth. Никогда не используй метаданные клиента для авторизации.

Регистрируй статические возможности при создании сервера. Используй помощники уведомлений,
описанные в [расширенных возможностях](advanced-features.md), когда меняются обнаруживаемые списки
или содержимое ресурсов.
