---
name: regru-domains
description: "Управление доменами, поддоменами и DNS-записями на личном аккаунте reg.ru через локальный CLI `regru.py`: добавить или удалить A/AAAA/CNAME/MX/TXT/NS-записи, сменить name-серверы, посмотреть зону или сведения о домене, проверить доступность домена. Используй при просьбах «добавь поддомен», «настрой DNS», «смени NS», «пропиши A-запись», «add subdomain», «set DNS», «point domain to», «manage reg.ru domain». Срабатывай, даже если reg.ru не назван: если контекст про DNS или домены и нет указания на другого регистратора (Cloudflare, GoDaddy, Namecheap), по умолчанию считай, что речь про аккаунт reg.ru."
license: MIT
metadata:
  author: Dmitriy-deov
  source: https://github.com/Dmitriy-deov/regru-cli
  tags: [regru, dns, домены, cli]
---

# regru-domains

Навык для управления доменами на аккаунте reg.ru через самодостаточный Python CLI [`regru-cli`](https://github.com/Dmitriy-deov/regru-cli).

CLI обёрнут вокруг [REG.API 2.0](https://www.reg.ru/reseller/api2doc), авторизуется через `.env` рядом со скриптом. Перед использованием навыка пользователь должен:

1. Склонировать `regru-cli` (по умолчанию ожидается `~/Desktop/regru-cli/`).
2. Заполнить `.env` (`REGRU_USERNAME` + альтернативный API-пароль).
3. Добавить свой внешний IP в белый список в кабинете reg.ru: <https://www.reg.ru/user/account/settings/api/>.

Если `whoami` падает с ошибкой про IP или аутентификацию — отправь пользователя в README репозитория за инструкциями.

## Когда использовать

Любой запрос про DNS-записи, поддомены или NS-серверы для доменов на reg.ru. Если пользователь говорит «добавь api.example.com → 1.2.3.4», «смени NS на Cloudflare для example.com», «покажи DNS-зону example.com», «удали поддомен blog», «проверь, свободен ли домен X» — это сюда.

Если пользователь явно говорит про другого регистратора (Cloudflare, GoDaddy, Namecheap, Dynadot и т. п.) — этот навык не применять.

## Где искать CLI

Стандартный путь: `~/Desktop/regru-cli/regru.py`. Если там его нет — попробуй найти:

```bash
find ~ -maxdepth 4 -name regru.py -path "*regru-cli*" 2>/dev/null | head -1
```

Если CLI не найден, попроси пользователя склонировать репозиторий (см. README навыка).

## Как работать

Запускай скрипт **из его папки**, чтобы подхватился `.env`:

```bash
cd ~/Desktop/regru-cli && ./regru.py <команда> [аргументы]
```

Все команды печатают JSON в stdout. При ошибке — код выхода 1 и JSON с ошибкой.

### Подкоманды

| Команда | Что делает |
|---|---|
| `whoami` | проверить аутентификацию (статистика аккаунта) |
| `domains` | список всех доменов на аккаунте |
| `info <domain>` | детали по домену (даты, автопродление, состояние) |
| `check <domain>` | доступен ли домен для регистрации |
| `nss <domain> <ns1> <ns2> [...]` | сменить NS-серверы |
| `dns <domain>` | все DNS-записи зоны |
| `dns-add <domain> <sub> <type> <value>` | добавить запись (A/AAAA/CNAME/MX/TXT/NS) |
| `dns-remove <domain> <sub> <type> [value]` | удалить запись |
| `raw <category> <method> [k=v ...]` | произвольный вызов API (запасной путь) |

`<sub>` — поддомен (`www`, `api`, `mail`) или `@` для корня. `<type>` — `A`, `AAAA`, `CNAME`, `MX`, `TXT`, `NS`.

### Типичные сценарии

```bash
# Сначала всегда проверь, что доступ работает
cd ~/Desktop/regru-cli && ./regru.py whoami

# Посмотреть текущую зону
./regru.py dns example.com

# Добавить A-запись поддомена
./regru.py dns-add example.com api A 1.2.3.4

# CNAME на внешний сервис
./regru.py dns-add example.com blog CNAME ghost.io

# MX (приоритет и хост через пробел в кавычках)
./regru.py dns-add example.com @ MX "10 mail.example.com"

# TXT (например, SPF)
./regru.py dns-add example.com @ TXT "v=spf1 include:_spf.google.com ~all"

# Удалить все A-записи поддомена
./regru.py dns-remove example.com api A

# Удалить конкретное значение (если несколько A с одним именем)
./regru.py dns-remove example.com api A 1.2.3.4

# Перевести домен на NS Cloudflare
./regru.py nss example.com lia.ns.cloudflare.com tom.ns.cloudflare.com
```

## Извлечение полей из ответа

Если нужно вытащить конкретное поле, используй `jq`:

```bash
# Список доменов с датами окончания
./regru.py domains | jq -r '.services[] | "\(.dname)\t\(.expiration_date)"'

# Все A-записи зоны
./regru.py dns example.com | jq '.domains[0].rrs[] | select(.rectype == "A")'
```

## Что делать НЕ нужно

- **Не вызывать `domain/create`, `domain/renew`, `service/renew`, `domain/transfer`** через `raw` без явного подтверждения пользователя — эти методы списывают деньги с баланса. Текущий баланс смотри через `./regru.py whoami` (поле `balance_total`).
- **Не показывать содержимое `.env`** в чате — там логин и API-пароль.
- **Не править `regru.py`** ради разовой задачи — для одноразовых вызовов используй `raw`. Менять скрипт стоит только если новая команда регулярная и пользователь готов это закоммитить.

## Если что-то сломалось

- `whoami` → ошибка про IP → внешний IP сменился (другой Wi-Fi или VPN). `curl ifconfig.me`, обновить белый список в <https://www.reg.ru/user/account/settings/api/>.
- `whoami` → `PASSWORD_AUTH_FAILED` или `NO_AUTH` → проверь, что в `.env` именно **альтернативный** API-пароль, а не пароль от личного кабинета.
- `NO_SUCH_COMMAND` от API → метод изменился. Документация: <https://www.reg.ru/reseller/api2doc>.

## Полезные ссылки

- Папка с CLI (по умолчанию): `~/Desktop/regru-cli/`
- README с инструкцией для людей: внутри той же папки, `README.md`
- Настройки API в кабинете: <https://www.reg.ru/user/account/settings/api/>
- Документация REG.API 2.0: <https://www.reg.ru/reseller/api2doc>
