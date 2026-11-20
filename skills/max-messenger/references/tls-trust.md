> Источник: https://dev.max.ru/docs-api + живая проверка TLS хостов (openssl, 21.09.2026) ·
> сверено 21.09.2026. Если это выглядит устаревшим, повтори `openssl s_client -connect platform-api2.max.ru:443 -showcerts` и перепроверь ссылки на скачивание ниже.

# Доверие TLS: `platform-api2.max.ru` и корневой CA Минцифры

Базовый URL и доверие к CA для каждого вызова MAX API на любом языке.

## Что изменилось и почему это ломается

- Базовый URL всех вызовов Bot API: **`https://platform-api2.max.ru`**. Старый `https://platform-api.max.ru` устарел; обязательный переход состоялся 19.07.2026.
- Цепочка сертификатов: конечный `*.max.ru` → **Russian Trusted Sub CA** → **Russian Trusted Root CA** (O = Министерство цифрового развития, связи и массовых коммуникаций Российской Федерации, «Минцифры»). Сервер присылает конечный сертификат и Sub CA; в твоём хранилище доверия нужен только **корневой**.
- Старый `platform-api.max.ru` выстраивал цепочку к HARICA, глобально доверенному CA, — поэтому код, написанный до перехода, «просто работал» без дополнительной настройки.
- Russian Trusted Root CA **отсутствует** в хранилищах доверия по умолчанию у Mozilla, Go, Node и стандартных базовых образов Docker: любой исходящий вызов `platform-api2.max.ru` из непропатченного окружения падает на проверке TLS.
- **Sub CA истекает 06.03.2027** — не пинь его. Доверяй только **корневому**: присылаемый сервером Sub CA продолжает работать, пока доверен корень, и MAX, как ожидается, сменит Sub CA до истечения.

## Чему дополнительный CA не нужен

| Хост | Для чего | CA |
|---|---|---|
| `platform-api2.max.ru` | Bot API (все методы) | Russian Trusted Root — **обязателен** |
| `iu.oneme.ru`, `fu.oneme.ru` | загрузка изображений и файлов | Let's Encrypt — доверен глобально |
| `omub.okcdn.ru`, `omu.okcdn.ru` | загрузка видео и аудио | HARICA — доверен глобально |
| `st.max.ru` | скрипт Bridge с CDN (`max-web-app.js`) | HARICA — доверен глобально |

Добавлять корневой сертификат Минцифры нужно только для вызовов `platform-api2.max.ru`. Трафик загрузок и скрипт Bridge — нет.

## Где взять сертификат

- Корневой: `https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt` — CN `Russian Trusted Root CA`, истекает 27.02.2032, отпечаток SHA-256 `D2:6D:2D:02:31:B7:C3:9F:92:CC:73:85:12:BA:54:10:35:19:E4:40:5D:68:B5:BD:70:3E:97:88:CA:8E:CF:31`.
- Промежуточный (не пинь, для справки): `https://gu-st.ru/content/lending/russian_trusted_sub_ca_pem.crt` — CN `Russian Trusted Sub CA`, истекает 06.03.2027.
- Страница-витрина (может быть ограничена по региону или сети): `https://www.gosuslugi.ru/crt`.

Проверь отпечаток, прежде чем доверять скачанному файлу:

```bash
curl -fsSL -o russian_trusted_root_ca.pem \
  https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt
openssl x509 -in russian_trusted_root_ca.pem -noout -fingerprint -sha256
# сверь с D2:6D:2D:02:31:B7:C3:9F:92:CC:73:85:12:BA:54:10:35:19:E4:40:5D:68:B5:BD:70:3E:97:88:CA:8E:CF:31
```

## Go: доверие корню через `WithHTTPClient`

У клиента нет встроенной опции CA — собери `*http.Client` с корнем в пуле и передай его через `maxbot.WithHTTPClient`:

```go
package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"net/http"
	"os"

	maxbot "github.com/max-messenger/max-bot-api-client-go/v2"
)

func newTrustedApi(token string) (*maxbot.Api, error) {
	pemBytes, err := os.ReadFile(os.Getenv("MAX_ROOT_CA_PATH"))
	if err != nil {
		return nil, fmt.Errorf("read root CA: %w", err)
	}

	pool, err := x509.SystemCertPool()
	if err != nil || pool == nil {
		pool = x509.NewCertPool()
	}
	if ok := pool.AppendCertsFromPEM(pemBytes); !ok {
		return nil, fmt.Errorf("no valid certificates found in %s", os.Getenv("MAX_ROOT_CA_PATH"))
	}

	httpClient := &http.Client{
		Transport: &http.Transport{
			TLSClientConfig: &tls.Config{RootCAs: pool},
		},
	}

	return maxbot.NewApi(token, maxbot.WithHTTPClient(httpClient))
}

func main() {
	api, err := newTrustedApi(os.Getenv("MAX_BOT_TOKEN"))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	info, err := api.Bots.GetMyInfo(context.Background())
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println(info.UserID)
}
```

`x509.SystemCertPool()` берёт за основу хранилище ОС, чтобы остальные HTTPS-вызовы бота продолжали работать; `AppendCertsFromPEM` добавляет корень Минцифры поверх — никогда не заменяй пул целиком. Чтобы не зависеть от файла во время выполнения, встрой PEM:

```go
//go:embed russian_trusted_root_ca.pem
var rootCAPEM []byte
```

(`//go:embed` требует `import _ "embed"`, а файл PEM должен лежать рядом с исходником — здесь показано отдельное объявление, а не целая программа.)

## Node и TS: в SDK опции CA нет — два способа добавить доверие

У `@maxhub/max-bot-api` нет опции `ca`, `agent` или `tls` (`ClientOptions` содержит только `baseUrl` и `fetch`). Настраивай доверие на уровне процесса или транспорта.

**Проще всего — переменная окружения на процесс** (работает для `fetch` и для большинства других HTTP-клиентов Node):

```bash
NODE_EXTRA_CA_CERTS=/etc/ssl/certs/russian_trusted_root_ca.pem node bot.js
```

**Альтернатива — подставить свой `fetch`** через `clientOptions.fetch` с `Agent` из `undici`, закреплённым на корне (полезно, когда нельзя задать переменные окружения процесса, например на общем хостинге):

```typescript
import { readFileSync } from 'node:fs';
import { Agent, fetch as undiciFetch } from 'undici';
import { Bot, type FetchFn } from '@maxhub/max-bot-api';

const agent = new Agent({
  connect: { ca: readFileSync(process.env.MAX_ROOT_CA_PATH ?? '/etc/ssl/certs/russian_trusted_root_ca.pem') },
});

const trustedFetch = ((input: Parameters<FetchFn>[0], init?: Parameters<FetchFn>[1]) =>
  undiciFetch(input as string, { ...(init as Record<string, unknown>), dispatcher: agent })) as unknown as FetchFn;

const bot = new Bot(process.env.MAX_BOT_TOKEN ?? '', {
  clientOptions: { fetch: trustedFetch },
});

void bot.start();
```

Этот свой `fetch` покрывает только JSON-вызовы Bot API (`/me`, `/updates`, `/messages`, вызов `/uploads`, выдающий URL). Байты файлов идут отдельным сырым транспортом `node:http`/`https` вообще без хука CA — но этот транспорт говорит с хостами загрузки из таблицы выше, и ни одному из них дополнительный корень не нужен.

## Docker

Базовые образы Debian и Ubuntu (для Alpine сначала добавь `RUN apk add --no-cache ca-certificates`):

```dockerfile
COPY russian_trusted_root_ca.pem /usr/local/share/ca-certificates/russian_trusted_root_ca.crt
RUN update-ca-certificates
ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/russian_trusted_root_ca.crt
```

`update-ca-certificates` обновляет хранилище ОС, которое Go подхватывает автоматически, — но встроенный стек `fetch` и TLS в Node игнорирует хранилище ОС и всё равно требует явного `NODE_EXTRA_CA_CERTS` (для образов только под Go эту строку убери).

## curl и Python

```bash
curl --cacert /path/russian_trusted_root_ca.pem https://platform-api2.max.ru/me \
  -H "Authorization: $MAX_BOT_TOKEN"
```

```python
import os
import requests

resp = requests.get(
    "https://platform-api2.max.ru/me",
    headers={"Authorization": os.environ["MAX_BOT_TOKEN"]},
    verify=os.environ["MAX_ROOT_CA_PATH"],  # путь к russian_trusted_root_ca.pem
)
```

`SSL_CERT_FILE=/path/russian_trusted_root_ca.pem` работает как общепроцессный эквивалент для стандартного хранилища доверия `ssl` и `requests` в Python — аналогично `NODE_EXTRA_CA_CERTS` в Node.

## Входящие вебхуки: обратное направление

Правила выше — для случая, когда твой бот вызывает *наружу* `platform-api2.max.ru`. Приёмнику вебхуков тоже нужен валидный TLS-сертификат, чтобы MAX мог вызвать *внутрь*, — требования к доставке, порту и таймауту в `references/webhooks-and-security.md`. Сертификат, выпущенный Минцифры, **тоже** подходит для входящей стороны (там он не обязан быть «глобально доверенным» CA — MAX принимает как свои сертификаты Минцифры, так и обычные сертификаты доверенных CA).

## Диагностика по точной строке ошибки

| Строка ошибки | Причина | Исправление |
|---|---|---|
| `x509: certificate signed by unknown authority` (Go) | Корневого CA нет в пуле, переданном HTTP-клиенту | Добавь корень через `WithHTTPClient`, как выше; проверь валидность PEM через `openssl x509 -in ... -noout -text` |
| `unable to get local issuer certificate` / `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` (Node) | Корневого CA нет в хранилище доверия Node | Задай `NODE_EXTRA_CA_CERTS` либо передай свой `fetch` на `undici.Agent` с `connect.ca` |
| Код выхода curl `60` (`SSL certificate problem: unable to get local issuer certificate`) | Корневого CA нет в системном наборе curl | Передай `--cacert /path/russian_trusted_root_ca.pem` |
| `CERTIFICATE_VERIFY_FAILED` (Python) | Корневого CA нет в `certifi` или системном наборе Python | Передай `verify=<путь-к-pem>` в `requests` либо задай `SSL_CERT_FILE` |
| `x509: certificate signed by unknown authority` сразу после `update-ca-certificates` | PEM фактически не попал в `/usr/local/share/ca-certificates/` либо Node игнорирует хранилище ОС | Перепроверь путь и расширение (`.crt`) в `COPY` Dockerfile и задай `NODE_EXTRA_CA_CERTS` явно для Node — он не читает хранилище ОС так, как Go |

## Чего делать нельзя

**Не** обходи ни одну из ошибок выше через `InsecureSkipVerify: true` (Go), `NODE_TLS_REJECT_UNAUTHORIZED=0` (Node), `verify=False` (Python `requests`) или `curl -k`. Каждый из этих вариантов полностью отключает проверку сертификатов — для всех хостов, с которыми говорит процесс, а не только для `platform-api2.max.ru` — и обесценивает TLS. Чини хранилище доверия: это копирование одного файла или одна переменная окружения, а не повод отключать проверку, даже «временно» и «только локально».
