# Типовые приёмы

**Содержание:** [Лимиты: общий 30 rps и ответы на колбэки (≤ 2/с)](#лимиты-общий-30-rps-и-ответы-на-колбэки-2с) · [Повтор `attachment.not.ready`](#повтор-attachmentnotready) · [Отслеживание чатов без `GET /chats`](#отслеживание-чатов-без-get-chats) · [Планировщик отложенной отправки (без `send_at`)](#планировщик-отложенной-отправки-без-send_at) · [Разбиение текста длиннее 4000 символов](#разбиение-текста-длиннее-4000-символов) · [Вебхук: быстрый ответ, асинхронная обработка, идемпотентность](#вебхук-быстрый-ответ-асинхронная-обработка-идемпотентность) · [Корректное завершение](#корректное-завершение)

> Источник: GO github.com/max-messenger/max-bot-api-client-go/v2 v2.4.0 · TS @maxhub/max-bot-api 0.3.1 · лимиты из `bot-api.md` (DOCS, получено 21.09.2026) · сверено 21.09.2026. Если это выглядит устаревшим, проверяй репозитории и сайт.

Ни один клиент не ограничивает частоту, не повторяет запросы в общем случае и ничего не хранит за тебя (см. разделы «Ошибки» в `go-client.md` и `ts-client.md`). Эти рецепты закрывают пробелы, о которых говорит DOCS. Каждый намеренно минимален — куски, работающие в памяти, в продакшене замени на Redis или БД, где это отмечено.

## Лимиты: общий 30 rps и ответы на колбэки (≤ 2/с)

DOCS: около 30 запросов в секунду к `platform-api2.max.ru` в целом, а `POST /answers` (ответы на колбэки) — не более 2 в секунду на чат; ни то ни другое клиенты не соблюдают. Небольшое ведро токенов закрывает оба: для первого ключ глобальный, для второго — id чата.

```go
package ratelimit

import (
	"context"
	"sync"
	"time"
)

// Limiter — ведро токенов без фоновых горутин, поэтому дешёво держать по одному на чат
// в карте (для потолка 2/с на ответы) рядом с одним глобальным экземпляром (для 30 rps).
type Limiter struct {
	mu     sync.Mutex
	rate   float64 // токенов в секунду
	burst  float64
	tokens float64
	last   time.Time
}

// New возвращает ограничитель, пропускающий rps запросов в секунду. rps должен быть > 0.
func New(rps int) *Limiter {
	if rps <= 0 {
		panic("ratelimit: rps must be > 0")
	}
	r := float64(rps)
	return &Limiter{rate: r, burst: r, tokens: r, last: time.Now()}
}

// Wait блокируется, пока не появится токен или не завершится ctx.
func (l *Limiter) Wait(ctx context.Context) error {
	for {
		l.mu.Lock()
		now := time.Now()
		l.tokens = min(l.burst, l.tokens+now.Sub(l.last).Seconds()*l.rate)
		l.last = now
		if l.tokens >= 1 {
			l.tokens--
			l.mu.Unlock()
			return nil
		}
		wait := time.Duration((1 - l.tokens) / l.rate * float64(time.Second))
		l.mu.Unlock()

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(wait):
		}
	}
}
```

```typescript
// То же ведро токенов: используется и для общего потолка 30 rps, и — с ключом по id чата
// в Map<number, RateLimiter> — для потолка 2/с на ответы.
export class RateLimiter {
  private tokens: number;
  private last = Date.now();

  // Без таймеров: токены пополняются лениво, поэтому экземпляр на чат в Map ничего не стоит в простое.
  constructor(private readonly rps: number) {
    if (!(rps > 0)) throw new RangeError('rps must be > 0');
    this.tokens = rps;
  }

  async wait(): Promise<void> {
    for (;;) {
      const now = Date.now();
      this.tokens = Math.min(this.rps, this.tokens + ((now - this.last) / 1000) * this.rps);
      this.last = now;
      if (this.tokens >= 1) {
        this.tokens -= 1;
        return;
      }
      await new Promise((r) => setTimeout(r, ((1 - this.tokens) / this.rps) * 1000));
    }
  }
}
```

## Повтор `attachment.not.ready`

Оба SDK уже повторяют это автоматически **внутри `Messages.Send` и `Comments.*`** (Go: 3 попытки, задержки 1 и 2 с; TS: 3 попытки, 1, 2 и 4 с) — не оборачивай эти вызовы своим циклом повторов, получится двойной повтор. Пробел — сам `Upload.Upload`: в обоих клиентах у него нет повторов вообще. Если вызов загрузки упал транзиентно, повтори загрузку вручную до вызова `Send`.

```go
import (
	"context"
	"errors"
	"io"
	"time"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

func uploadWithRetry(ctx context.Context, api *maxbot.Api, r io.ReaderAt, name string, size int64) (string, error) {
	var lastErr error
	for attempt := 0; attempt < 3; attempt++ {
		token, err := api.Upload.Upload(ctx, model.UploadImage, io.NewSectionReader(r, 0, size), name, size)
		if err == nil {
			return token, nil
		}
		lastErr = err
		var netErr *maxbot.NetworkError
		if !errors.As(err, &netErr) {
			return "", err // не транзиентная сетевая ошибка, не повторяем
		}
		time.Sleep(time.Duration(attempt+1) * time.Second)
	}
	return "", lastErr
}
```

```typescript
import type { Api } from '@maxhub/max-bot-api';

// У ctx.api.uploadImage/uploadVideo/uploadAudio/uploadFile повторов тоже нет.
// UploadImageOptions принимает { source: FileSource } либо { url: string }.
export async function uploadWithRetry(
  api: Api,
  source: Parameters<Api['uploadImage']>[0],
  attempts = 3,
): Promise<Awaited<ReturnType<Api['uploadImage']>>> {
  let lastErr: unknown;
  for (let i = 0; i < attempts; i += 1) {
    try {
      return await api.uploadImage(source);
    } catch (err) {
      lastErr = err;
      await new Promise((r) => setTimeout(r, (i + 1) * 1000));
    }
  }
  throw lastErr;
}
```

## Отслеживание чатов без `GET /chats`

Эндпоинт списка чатов удалён (июнь 2026; см. `bot-api.md`). Сохраняй id чатов сам из событий членства по мере их прихода, вместо того чтобы потом пытаться перечислить чаты.

```go
import (
	"context"

	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

// Store — твоё собственное хранилище (таблица в БД, KV-хранилище и т. п.).
type Store interface {
	SaveChat(chatID int64)
	RemoveChat(chatID int64)
}

func trackChats(store Store) func(context.Context, model.Update) {
	return func(_ context.Context, u model.Update) {
		switch u.UpdateType {
		case "bot_added", "bot_started":
			store.SaveChat(u.ChatID)
		case "bot_removed":
			store.RemoveChat(u.ChatID)
		}
	}
}
```

```typescript
import type { Bot, Context } from '@maxhub/max-bot-api';

export interface ChatStore {
  save(chatId: number): Promise<void>;
  remove(chatId: number): Promise<void>;
}

export function trackChats(bot: Bot, store: ChatStore): void {
  bot.on('bot_added', async (ctx: Context) => { if (ctx.chatId) await store.save(ctx.chatId); });
  bot.on('bot_started', async (ctx: Context) => { if (ctx.chatId) await store.save(ctx.chatId); });
  bot.on('bot_removed', async (ctx: Context) => { if (ctx.chatId) await store.remove(ctx.chatId); });
}
```

## Планировщик отложенной отправки (без `send_at`)

Поля отложенной отправки в API нет (проверено по `schema.yaml`) — отложенная отправка целиком на стороне клиента. Таймер в процессе годится для коротких задержек, но теряется при перезапуске и деплое; для всего, что дольше нескольких минут или должно пережить перезапуск, сохраняй задачу (строка в БД плюс поллер либо настоящая очередь), а не держи в памяти.

```go
import (
	"context"
	"time"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
)

// ScheduleSend срабатывает через d; отмена — возвращённой функцией. Только в памяти —
// не переживает перезапуск процесса.
func ScheduleSend(ctx context.Context, api *maxbot.Api, chatID int64, text string, d time.Duration) func() {
	timer := time.AfterFunc(d, func() {
		msg := maxbot.NewMessage().SetChat(chatID).SetText(text)
		_, _ = api.Messages.Send(ctx, msg)
	})
	return func() { timer.Stop() }
}
```

```typescript
import type { Bot } from '@maxhub/max-bot-api';

// Только в памяти — не переживает перезапуск процесса; для долговечности сохраняй задачу.
export function scheduleSend(bot: Bot, chatId: number, text: string, delayMs: number): () => void {
  const handle = setTimeout(() => {
    bot.api.sendMessageToChat(chatId, text).catch(() => {});
  }, delayMs);
  return () => clearTimeout(handle);
}
```

## Разбиение текста длиннее 4000 символов

Поле `text` ограничено 4000 символами (`NewMessageBody` и `NewCommentBody`, подтверждено в `schema.yaml`). Режь сначала по границам абзацев, затем по пробелам, чтобы не разорвать слово пополам; это **не** гарантирует, что открытый участок markdown или HTML (например, незакрытый `**bold**`) не перейдёт через границу, — считай это эвристикой по мере возможностей и предпочитай резать по своим границам абзацев, когда исходный текст под твоим контролем.

Лимит считает каждый символ сырого `text` (включая разметку) — символы, а не байты: кириллица в UTF-8 занимает 2 байта на символ, поэтому режь по рунам (Go) или кодовым точкам (TS) и никогда по смещениям байтов или UTF-16.

```go
// splitMessage делит text на части не длиннее limit символов (рун), предпочитая границы
// перевода строки, затем пробела во второй половине каждого куска.
func splitMessage(text string, limit int) []string {
	r := []rune(text)
	var parts []string
	for len(r) > limit {
		cut := limit
		if i := lastRune(r[:limit], '\n'); i > limit/2 {
			cut = i
		} else if i := lastRune(r[:limit], ' '); i > limit/2 {
			cut = i
		}
		parts = append(parts, string(r[:cut]))
		r = r[cut:]
	}
	return append(parts, string(r))
}

func lastRune(r []rune, x rune) int {
	for i := len(r) - 1; i >= 0; i-- {
		if r[i] == x {
			return i
		}
	}
	return -1
}
```

```typescript
export function splitMessage(text: string, limit = 4000): string[] {
  // Array.from делит по кодовым точкам, поэтому эмодзи и другие суррогатные пары никогда не рвутся пополам.
  let rest = Array.from(text);
  const parts: string[] = [];
  while (rest.length > limit) {
    let cut = rest.lastIndexOf('\n', limit - 1);
    if (cut < limit / 2) cut = rest.lastIndexOf(' ', limit - 1);
    if (cut < limit / 2) cut = limit;
    parts.push(rest.slice(0, cut).join(''));
    rest = rest.slice(cut);
  }
  parts.push(rest.join(''));
  return parts;
}
```

## Вебхук: быстрый ответ, асинхронная обработка, идемпотентность

`Api.GetHandler` в Go вызывает твой обработчик **синхронно** до записи ответа — если обработка может быть медленной, отправляй её в горутину сам и отвязывай контекст, поскольку контекст запроса отменяется, как только обработчик вернётся. Встроенный обработчик вебхука в TS уже отвечает `200 OK` *до* запуска цепочки middleware (ошибки после этого доходят только до `bot.catch()`, MAX повторять не будет). Ни один SDK не даёт стабильного идентификатора доставки и не дедуплицирует за тебя. Строй свой ключ из `update_type` и `timestamp` плюс `message_id`, `comment_id` или `callback_id`, когда они есть, чтобы отбрасывать повторные доставки вебхука.

```go
import (
	"context"
	"fmt"
	"sync"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

// FastAck выносит обработку в горутину и отбрасывает повторные
// доставки. В продакшене замени sync.Map на Redis или БД с TTL.
func FastAck(process func(context.Context, model.Update)) maxbot.UpdateHandler {
	var seen sync.Map
	return func(ctx context.Context, u model.Update) {
		key := fmt.Sprintf("%s:%d:%s%s%s", u.UpdateType, u.Timestamp, u.MessageID, u.PostID, u.CommentID)
		if _, dup := seen.LoadOrStore(key, struct{}{}); dup {
			return
		}
		go process(context.WithoutCancel(ctx), u)
	}
}
```

```typescript
import type { Bot, Context, MiddlewareFn } from '@maxhub/max-bot-api';

// bot.webhookCallback() и createWebhook() уже отвечают 200 до запуска этой цепочки;
// это middleware добавляет только фильтрацию повторных доставок.
export function dedupe(): MiddlewareFn<Context> {
  const seen = new Set<string>();
  return async (ctx, next) => {
    const key = `${ctx.updateType}:${ctx.update.timestamp}:${ctx.messageId ?? ''}`;
    if (seen.has(key)) return;
    seen.add(key);
    if (seen.size > 10000) seen.clear(); // грубая граница; для реального трафика используй Redis с TTL
    await next();
  };
}

export function wireWebhook(bot: Bot): void {
  bot.use(dedupe());
}
```

## Корректное завершение

Перестань принимать новые обновления, дай обработчикам в работе закончить, затем выходи.

```go
import (
	"context"
	"net/http"
	"os/signal"
	"syscall"
	"time"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
)

func runWithGracefulShutdown(api *maxbot.Api, srv *http.Server) error {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	errCh := make(chan error, 1)
	go func() { errCh <- srv.ListenAndServe() }()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		return srv.Shutdown(shutdownCtx)
	}
}
```

```typescript
import type { Bot } from '@maxhub/max-bot-api';

export function installGracefulShutdown(bot: Bot): void {
  const shutdown = async (signal: string) => {
    console.log(`received ${signal}, shutting down`);
    bot.stopPolling();
    await bot.stopWebhook();
    process.exit(0);
  };
  process.on('SIGINT', () => { void shutdown('SIGINT'); });
  process.on('SIGTERM', () => { void shutdown('SIGTERM'); });
}
```
