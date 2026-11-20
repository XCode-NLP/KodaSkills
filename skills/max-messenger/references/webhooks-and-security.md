> Источник: DOCS https://dev.max.ru/docs-api (методы/POST/subscriptions, «Рекомендации») +
> BRIDGE https://dev.max.ru/docs/webapps/validation + https://dev.max.ru/docs/webapps/bridge +
> GO github.com/max-messenger/max-bot-api-client-go/v2@c832c5b (`v2.4.0`) +
> TS @maxhub/max-bot-api@0.3.1 · сверено 21.09.2026. Если это выглядит устаревшим, перепроверь те страницы
> и примечания к выпускам клиентов.

# Вебхуки и безопасность

**Содержание:** [Подписка на обновления](#подписка-на-обновления) · [Требования к доставке](#требования-к-доставке) · [Проверка секретного заголовка](#проверка-секретного-заголовка) · [Три формулы HMAC рядом](#три-формулы-hmac-рядом) · [Long polling против вебхука](#long-polling-против-вебхука) · [Подводные камни](#подводные-камни)

Все формулы проверки MAX в одном месте: секретный заголовок вебхука, `initData` мини-приложения и два HMAC-хеша телефона и контакта, с проверенным кодом на Go и TypeScript. Про доверие TLS и CA хоста API — в `references/tls-trust.md`.

## Подписка на обновления

`POST /subscriptions`, тело:

| Поле | Тип | Заметки |
|---|---|---|
| `url` | string, обязателен | Должен начинаться с `https://`. |
| `update_types` | string[], необязателен | Какие значения `update_type` получать; не указывай — получать все. |
| `secret` | string, необязателен, но настоятельно рекомендуется | 5–256 символов, допустимый набор `[A-Za-z0-9_-]`. Возвращается при каждой доставке, см. ниже. |

`GET /subscriptions` перечисляет активные подписки; `DELETE /subscriptions?url=<url>` удаляет одну. Вебхук и long polling взаимоисключающие: подписка на URL вебхука неявно прекращает работу long polling для продакшен-трафика (см. «Long polling против вебхука» ниже).

## Требования к доставке

- Эндпоинт вебхука должен слушать **только порт 443** — не указывай номер порта в `url`.
- TLS: сертификат от доверенного CA **или сертификат, выпущенный Минцифры** (см. `references/tls-trust.md`); самоподписанные не годятся; домен в `url` должен совпадать с CN или SAN сертификата; сервер обязан предъявить полную цепочку. **С 25.05.2026** доставка по простому HTTP и самоподписанные сертификаты отклоняются outright — это жёсткое требование, а не рекомендация.
- Твой эндпоинт должен ответить **HTTP 200 за 30 секунд**. Всё остальное (неверный статус, таймаут, ошибка соединения) считается неудачной доставкой.
- Неудачные доставки повторяются до **10 раз** с экспоненциально растущими интервалами: 60 с, затем 150 с (×2,5), затем 375 с (×2,5) и так далее.
- Если ни одна доставка не удалась в течение **8 часов** с момента события, MAX автоматически отписывает бота от этого URL вебхука — ты молча перестаёшь получать обновления, пока не подпишешься снова.

## Проверка секретного заголовка

MAX возвращает заданный `secret` при каждом POST вебхука в заголовке **`X-Max-Bot-Api-Secret`**. Сравнивать нужно за постоянное время: наивное сравнение строк через `==` или `!=` утекает информацию о том, сколько ведущих байт совпало, а это реальный (пусть и узкий) побочный канал для подбора долгоживущего секрета.

**Известный пробел в официальном Go-клиенте:** собственная проверка секрета в `Api.GetHandler` использует обычный Go `!=`, а не `subtle.ConstantTimeCompare` (`bot.go`, `Api.GetHandler`, v2.4.0), хотя в других местах сравнение за постоянное время применяется корректно (`ValidateInitData`, ниже). Если используешь `GetHandler` как есть, оберни его, как показано ниже, чтобы получить проверку за постоянное время; не считай, что SDK уже делает это за тебя.

**TS-клиент делает это правильно по умолчанию:** `bot.start({mode:'webhook',...})`, `bot.webhookCallback(...)` и `bot.createWebhook(...)` сравнивают заголовок через `timingSafeEqual` в Node после проверки равенства длин. Одна особенность поведения, о которой надо знать: несовпадающий или отсутствующий заголовок возвращает **404 Not Found**, а не 401 или 403, — не строй алерты, которые следят только за 401. Если оставить `secret` незаданным, TS SDK принимает **любой** запрос на путь вебхука вообще без проверки — в продакшене всегда задавай секрет.

```go
package main

import (
	"context"
	"crypto/hmac"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
	"github.com/max-messenger/max-bot-api-client-go/v2/model"
)

// secureWebhook оборачивает обработчик (например, результат api.GetHandler) проверкой секрета
// за постоянное время, закрывая пробел в сравнении через обычный `!=` внутри GetHandler.
func secureWebhook(next http.HandlerFunc, secret string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		got := r.Header.Get("X-Max-Bot-Api-Secret")
		if subtle.ConstantTimeCompare([]byte(got), []byte(secret)) != 1 {
			http.Error(w, http.StatusText(http.StatusUnauthorized), http.StatusUnauthorized)
			return
		}
		next(w, r)
	}
}

// validateInitData реализует алгоритм initData мини-приложения
// (https://dev.max.ru/docs/webapps/validation). Передавай window.WebApp.initData ровно так,
// как его прислал клиент. Здесь он URL-декодируется один раз — см. подводный камень про maxbot.ValidateInitData.
func validateInitData(initData, botToken string, maxAge time.Duration) (bool, error) {
	values, err := url.ParseQuery(initData)
	if err != nil {
		return false, fmt.Errorf("parse initData: %w", err)
	}

	hashValues, ok := values["hash"]
	if !ok || len(hashValues) != 1 {
		return false, fmt.Errorf("hash parameter must be present exactly once")
	}
	receivedHash := hashValues[0]
	values.Del("hash")

	authDate, err := strconv.ParseInt(values.Get("auth_date"), 10, 64)
	if err != nil {
		return false, fmt.Errorf("parse auth_date: %w", err)
	}
	if time.Since(time.Unix(authDate, 0)) > maxAge {
		return false, fmt.Errorf("auth_date is stale")
	}

	pairs := make([]string, 0, len(values))
	for key, vals := range values {
		for _, v := range vals {
			pairs = append(pairs, key+"="+v)
		}
	}
	sort.Strings(pairs)
	dataCheckString := strings.Join(pairs, "\n")

	secretMAC := hmac.New(sha256.New, []byte("WebAppData"))
	secretMAC.Write([]byte(botToken))
	secretKey := secretMAC.Sum(nil)

	mac := hmac.New(sha256.New, secretKey)
	mac.Write([]byte(dataCheckString))
	computedHash := hex.EncodeToString(mac.Sum(nil))

	if subtle.ConstantTimeCompare([]byte(receivedHash), []byte(computedHash)) != 1 {
		return false, fmt.Errorf("hash verification failed")
	}
	return true, nil
}

// verifyPhoneHash проверяет хеш, который возвращает requestContact() из Bridge (отдельная,
// более простая формула, чем initData: без предварительного вывода "WebAppData", ключ HMAC — сырой токен бота).
func verifyPhoneHash(authDate, phone, userID, hash, botToken string) bool {
	phone = strings.TrimPrefix(phone, "+")
	message := strings.Join([]string{
		"authDate=" + authDate,
		"phone=" + phone,
		"userId=" + userID,
	}, "\n")

	mac := hmac.New(sha256.New, []byte(botToken))
	mac.Write([]byte(message))
	computed := hex.EncodeToString(mac.Sum(nil))

	return subtle.ConstantTimeCompare([]byte(computed), []byte(hash)) == 1
}

// verifyContactHash проверяет `hash` у вложения `contact`, полученного через кнопку
// request_contact Bot API — ТРЕТЬЯ, отдельная формула, отличная от initData и requestContact.
func verifyContactHash(vcfInfo, hash, botToken string) bool {
	// vcf_info ровно как получено; после разбора JSON в нём уже настоящие переводы строк CRLF.
	mac := hmac.New(sha256.New, []byte(botToken))
	mac.Write([]byte(vcfInfo))
	computed := hex.EncodeToString(mac.Sum(nil))

	return subtle.ConstantTimeCompare([]byte(computed), []byte(hash)) == 1
}

func main() {
	token := os.Getenv("MAX_BOT_TOKEN")
	secret := os.Getenv("MAX_WEBHOOK_SECRET")

	api, err := maxbot.NewApi(token)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	updateHandler := func(_ context.Context, upd model.Update) {
		fmt.Println("received update:", upd.UpdateType)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/webhook", secureWebhook(api.GetHandler(updateHandler, secret), secret))

	mux.HandleFunc("/mini-app/auth", func(w http.ResponseWriter, r *http.Request) {
		// Мини-приложение присылает window.WebApp.initData как сырое тело запроса.
		body, err := io.ReadAll(io.LimitReader(r.Body, 8<<10))
		if err != nil {
			http.Error(w, "bad request", http.StatusBadRequest)
			return
		}
		if ok, err := validateInitData(string(body), token, time.Hour); !ok {
			http.Error(w, "invalid initData: "+err.Error(), http.StatusUnauthorized)
			return
		}
		w.WriteHeader(http.StatusOK)
	})

	if err := http.ListenAndServe(":8443", mux); err != nil {
		fmt.Fprintln(os.Stderr, err)
	}
}
```

```typescript
import { createHmac, timingSafeEqual } from 'node:crypto';
import type { NextFunction, Request, Response } from 'express';

const SECRET_HEADER = 'x-max-bot-api-secret';

/** Проверка секрета за постоянное время для своего маршрута вебхука на Express. Если используешь
 * собственные bot.start({mode:'webhook',...}) / bot.webhookCallback() / bot.createWebhook() из SDK,
 * он уже делает это (и возвращает 404, а не 401, при несовпадении) — этот код только для сырых HTTP-приёмников. */
export function verifyWebhookSecret(secret: string) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const got = Buffer.from(String(req.header(SECRET_HEADER) ?? ''), 'utf8');
    const want = Buffer.from(secret, 'utf8');
    if (got.length !== want.length || !timingSafeEqual(got, want)) {
      res.status(404).end();
      return;
    }
    next();
  };
}

/** Двухшаговый HMAC из https://dev.max.ru/docs/webapps/validation. Передавай window.WebApp.initData
 * ровно так, как его прислал клиент. Проверяет рекомендуемое окно свежести auth_date (по умолчанию 1 час). */
export function validateInitData(
  initData: string,
  botToken: string,
  maxAgeSeconds = 3600,
): boolean {
  // URLSearchParams декодирует каждое значение ровно один раз и понимает и %20, и "+" как пробел.
  const params = new URLSearchParams(initData);

  const hashes = params.getAll('hash');
  if (hashes.length !== 1) return false;
  const receivedHash = hashes[0];
  params.delete('hash');

  const authDate = Number(params.get('auth_date'));
  if (!Number.isFinite(authDate)) return false;
  if (Math.floor(Date.now() / 1000) - authDate > maxAgeSeconds) return false;

  const launchParams = [...params]
    .map(([key, value]) => `${key}=${value}`)
    .sort()
    .join('\n');

  const secretKey = createHmac('sha256', 'WebAppData').update(botToken).digest();
  const computedHash = createHmac('sha256', secretKey).update(launchParams).digest('hex');

  const a = Buffer.from(computedHash, 'hex');
  const b = Buffer.from(receivedHash, 'hex');
  return a.length === b.length && timingSafeEqual(a, b);
}

/** Хеш requestContact() из Bridge — отдельная, более простая формула, чем initData: ключ HMAC —
 * сырой токен бота, без предварительного вывода "WebAppData". У `phone` сначала убирается ведущий "+". */
export function verifyPhoneHash(
  authDate: string,
  phone: string,
  userId: string,
  hash: string,
  botToken: string,
): boolean {
  const normalizedPhone = phone.startsWith('+') ? phone.slice(1) : phone;
  const message = [`authDate=${authDate}`, `phone=${normalizedPhone}`, `userId=${userId}`].join('\n');
  const computed = createHmac('sha256', botToken).update(message).digest('hex');

  const a = Buffer.from(computed, 'hex');
  const b = Buffer.from(hash, 'hex');
  return a.length === b.length && timingSafeEqual(a, b);
}

/** Кнопка request_contact Bot API — ТРЕТЬЯ, отдельная формула: HMAC по тексту vcf_info вложения
 * contact с токеном бота. Годится только для контактов, отправленных кнопкой request_contact;
 * у контактов, пересланных из адресной книги, хеша для проверки нет. */
export function verifyContactHash(vcfInfo: string, hash: string, botToken: string): boolean {
  // vcf_info ровно как получено; после JSON.parse в нём уже настоящие переводы строк CRLF.
  const computed = createHmac('sha256', botToken).update(vcfInfo).digest('hex');

  const a = Buffer.from(computed, 'hex');
  const b = Buffer.from(hash, 'hex');
  return a.length === b.length && timingSafeEqual(a, b);
}
```

## Три формулы HMAC рядом

Их легко перепутать — все три считают HMAC-SHA256 от чего-то с помощью чего-то похожего на токен бота, и две из трёх используются вместе в одном и том же сценарии авторизации мини-приложения.

| Формула | Ключ | Сообщение | Откуда берётся |
|---|---|---|---|
| `initData` (авторизация мини-приложения) | `HMAC_SHA256("WebAppData", botToken)` (два шага: это *производный* ключ) | отсортированные поля `key=value`, соединённые `\n`, без `hash` | `window.WebApp.initData`, проверяется на твоём бэкенде |
| Телефон из `requestContact()` | сырой `botToken` | `authDate=<v>\nphone=<v>\nuserId=<v>` (телефон без `+`) | результат `requestContact()` из Bridge |
| Контакт из кнопки `request_contact` | сырой `botToken` (в Bot API он называется `access_token`, значение то же) | `vcf_info` ровно как получено (после разбора JSON, строки разделены CRLF) — DOCS: `HMAC-SHA256(access_token, vcf_info)` | вложение `contact` в обновлении `message_created` |

Только у `initData` есть дополнительный шаг вывода ключа через `"WebAppData"` — две другие считают HMAC напрямую токеном бота. Путаница между этими двумя формами — самая частая ошибка при реализации проверки мини-приложения и контактов с нуля; в самом `bot.go` Go-клиента формула `initData` сделана верно (сравнение за постоянное время), но его простая проверка секрета вебхука выше показывает, что даже официальный SDK не одинаково аккуратен в этом классе ошибок.

## Long polling против вебхука

- Long polling (`GET /updates`) — **только для разработки и тестов**: у него ограничения по частоте и хранению, для продакшен-трафика он не рекомендуется.
- В продакшене обязателен вебхук. Одновременно то и другое работать не может: подписка на URL вебхука и вызовы `GET /updates` с тем же токеном бота будут мешать друг другу; выбирай одно на окружение (локально опрашивай, в развёрнутых окружениях — вебхук).
- TS SDK это обеспечивает: `bot.start()` в режиме polling удаляет все подписки вебхука, в режиме webhook удаляет подписки по другим URL и оставляет свою. Переключение бота с вебхука обратно на polling молча снимает зарегистрированный вебхук. См. `references/ts-client.md`.

## Подводные камни

- **`maxbot.ValidateInitData` (Go-клиент v2.4.0) делает URL-декодирование дважды** (`url.QueryUnescape` по всей строке, затем `url.ParseQuery`). Корректный initData, в значениях которого есть закодированные `&`, `=` или `%` (например, пользователь с именем `Tom&Jerry`), не проходит проверку. Воспроизведено на v2.4.0. Используй отдельную функцию `validateInitData` выше (одно декодирование) либо заранее проверяй данные своих пользователей.

| Подводный камень | Подробность |
|---|---|
| Доверие `initDataUnsafe` | Это явно клиентские удобные данные — никогда не считай их проверенными; всегда проверяй сырую строку `initData` на сервере. |
| Ожидание 401 при неверном секрете вебхука | Встроенная обработка вебхука в TS SDK отвечает **404**, а не 401 или 403, при несовпадении секрета. |
| Повторное использование формы HMAC от `initData` для хешей телефона и контакта | Оба пропускают шаг вывода ключа через `"WebAppData"` и считают HMAC напрямую токеном бота — см. таблицу выше. |
| Сравнение хешей через `==` или `!=` | Всегда используй сравнение за постоянное время (`subtle.ConstantTimeCompare` в Go, `timingSafeEqual` после проверки равенства длин в Node) — равенство строк утекает информацию о времени. |
| Проверка пересланного контакта из адресной книги формулой `request_contact` | Хеш вообще есть только у контактов, отправленных настоящей кнопкой `request_contact`; для остальных путей передачи контакта проверять нечего. |
