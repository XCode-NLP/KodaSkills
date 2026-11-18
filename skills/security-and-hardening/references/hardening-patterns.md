# Шаблоны укрепления

Шаблоны кода и подспорья для решений в навыке `security-and-hardening`. Навык формулирует каждое
правило; этот файл показывает одну конкретную его реализацию. Открывай нужный раздел, когда
добираешься до этого кода: читать его сверху донизу не предполагается.

Общие контрольные списки (моделирование угроз, проверки перед коммитом, заголовки безопасности,
CORS, матрица пакетных менеджеров, барьер для скриптов установки и таблицы краткой справки по
OWASP) лежат в `../../../references/security-checklist.md`.

## Шаблоны предотвращения по OWASP Top 10

Это шаблоны предотвращения, а не рейтинг. Порядок 2021 года см. в таблице краткой справки в
`../../../references/security-checklist.md#краткая-справка-по-owasp-top-10`.

### Внедрение

```typescript
// BAD: SQL injection via string concatenation
const query = `SELECT * FROM users WHERE id = '${userId}'`;

// GOOD: Parameterized query
const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);

// GOOD: ORM with parameterized input
const user = await prisma.user.findUnique({ where: { id: userId } });
```

### Нарушенная аутентификация

```typescript
// Password hashing
import { hash, compare } from 'bcrypt';

const SALT_ROUNDS = 12;
const hashedPassword = await hash(plaintext, SALT_ROUNDS);
const isValid = await compare(plaintext, hashedPassword);

// Session management
const SESSION_SECRET = process.env.SESSION_SECRET;  // From environment, not code
if (!SESSION_SECRET) throw new Error('SESSION_SECRET not configured');
app.use(session({
  secret: SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,     // Not accessible via JavaScript
    secure: true,       // HTTPS only
    sameSite: 'lax',    // CSRF protection
    maxAge: 24 * 60 * 60 * 1000,  // 24 hours
  },
}));
```

### Межсайтовый скриптинг (XSS)

```typescript
// BAD: Rendering user input as HTML
element.innerHTML = userInput;

// GOOD: Use framework auto-escaping (React does this by default)
return <div>{userInput}</div>;

// If you MUST render HTML, sanitize first
import DOMPurify from 'dompurify';
const clean = DOMPurify.sanitize(userInput);
```

### Нарушение контроля доступа

```typescript
// Always check authorization, not just authentication
app.patch('/api/tasks/:id', authenticate, async (req, res) => {
  const task = await taskService.findById(req.params.id);
  if (!task) {
    return res.status(404).json({
      error: { code: 'NOT_FOUND', message: 'Task not found' }
    });
  }

  // Check that the authenticated user owns this resource
  if (task.ownerId !== req.user.id) {
    return res.status(403).json({
      error: { code: 'FORBIDDEN', message: 'Not authorized to modify this task' }
    });
  }

  // Proceed with update
  const updated = await taskService.update(req.params.id, req.body);
  return res.json(updated);
});
```

### Небезопасная конфигурация

```typescript
// Security headers (use helmet for Express)
import helmet from 'helmet';
app.use(helmet());

// Content Security Policy
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'"],
    styleSrc: ["'self'", "'unsafe-inline'"],  // Tighten if possible
    imgSrc: ["'self'", 'data:', 'https:'],
    connectSrc: ["'self'"],
  },
}));

// CORS — restrict to known origins
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || 'http://localhost:3000',
  credentials: true,
}));
```

### Раскрытие чувствительных данных

```typescript
// Never return sensitive fields in API responses
function sanitizeUser(user: UserRecord): PublicUser {
  const { passwordHash, resetToken, ...publicFields } = user;
  return publicFields;
}

// Use environment variables for secrets
const API_KEY = process.env.STRIPE_API_KEY;
if (!API_KEY) throw new Error('STRIPE_API_KEY not configured');
```

### Подделка серверных запросов (SSRF)

Каждый раз, когда сервер загружает URL, на который повлиял пользователь (вебхуки, «импорт по
URL», прокси изображений, предпросмотр ссылок), атакующий может нацелить его на внутренние сервисы
(метаданные облака, `localhost`, частные IP).

```typescript
// BAD: fetch whatever the user gives you
await fetch(req.body.webhookUrl);

// GOOD: allowlist scheme + host, reject if ANY resolved IP is private, forbid redirects
import { lookup } from 'node:dns/promises';
import ipaddr from 'ipaddr.js';

const ALLOWED_HOSTS = new Set(['hooks.example.com']);

async function assertSafeUrl(raw: string): Promise<URL> {
  const url = new URL(raw);
  if (url.protocol !== 'https:') throw new Error('https only');
  if (!ALLOWED_HOSTS.has(url.hostname)) throw new Error('host not allowed');
  // Resolve ALL records; a single private/reserved address fails the check.
  const addrs = await lookup(url.hostname, { all: true });
  if (addrs.some((a) => ipaddr.parse(a.address).range() !== 'unicast')) {
    throw new Error('private/reserved IP');
  }
  return url;
}

await fetch(await assertSafeUrl(req.body.webhookUrl), { redirect: 'error' });
```

Проверка `range() !== 'unicast'` покрывает loopback, link-local `169.254.169.254` (метаданные
облака — цель SSRF номер один), частные и уникальные локальные диапазоны в IPv4 и IPv6.

**Оговорка: здесь остаётся разрыв TOCTOU.** `fetch` разрешает DNS заново после проверки, поэтому
атакующий с записью с малым TTL может перепривязаться к внутреннему IP между проверкой и
соединением. Для поверхностей высокого риска разреши адрес один раз и подключайся к закреплённому
IP либо поставь впереди фильтрующий агент (`request-filtering-agent` или `ssrf-req-filter`).

## Шаблоны проверки ввода

### Проверка по схеме на границах

```typescript
import { z } from 'zod';

const CreateTaskSchema = z.object({
  title: z.string().max(200).trim().min(1),
  description: z.string().max(2000).optional(),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  dueDate: z.string().datetime().optional(),
});

// Validate at the route handler
app.post('/api/tasks', async (req, res) => {
  const result = CreateTaskSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(422).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid input',
        details: result.error.flatten(),
      },
    });
  }
  // result.data is now typed and validated
  const task = await taskService.create(result.data);
  return res.status(201).json(task);
});
```

### Безопасность загрузки файлов

```typescript
// Restrict file types and sizes
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_SIZE = 5 * 1024 * 1024; // 5MB

function validateUpload(file: UploadedFile) {
  if (!ALLOWED_TYPES.includes(file.mimetype)) {
    throw new ValidationError('File type not allowed');
  }
  if (file.size > MAX_SIZE) {
    throw new ValidationError('File too large (max 5MB)');
  }
  // Don't trust the file extension — check magic bytes if critical
}
```

### Разрушительные операции с производными путями

Удаление, перемещение или перезапись безопасны настолько, насколько безопасно значение, называющее
цель. Чтение этого значения из ядра, полезной нагрузки задачи или соседнего сервиса доказывает,
откуда оно *пришло*, но не кто его *записал*: командная строка другого процесса так же подвластна
атакующему, как поле формы. Проверка формы («абсолютный путь, минимум на одну директорию вглубь»)
доказывает корректность записи и ошибочно принимается за авторизацию — так процедура очистки
удаляет корень вместо листа.

Перед разрушительным вызовом требуй все три условия: разрешённая цель лежит под **корнем из белого
списка** (сравнивай после разрешения символических ссылок, никогда по сырой строке); она как
минимум на один уровень **ниже** этого корня, чтобы корень никогда не был самой целью; и она несёт
**доказательство, что она твоя**, прочитанное *до* операции и до любого сноса, который его удалит,
иначе «отсутствует» и «не моя» неразличимы. При отказе логируй отклонённую цель и остановись:
очистка, которая откатывается к более широкому пути по умолчанию, — именно тот отказ, от которого
это защищает. Разобранный пример см. в
`../../../references/security-checklist.md#разрушительные-операции-с-путями`.

Два ограничения, потому что проверка выглядит строже, чем она есть. Маркер внутри дерева — это
самоаттестация: всё, что может туда писать, может записать и маркер, поэтому ожидаемый владелец
должен приходить из аутентифицированного состояния, а маркеру нужна защита целостности
(ограничительные права владельца или MAC), прежде чем он станет авторизацией. И разрешение пути с
последующей работой по *имени* — гонка между проверкой и использованием везде, где недоверенный
процесс может подменить предка: на общем томе держи цель по дескриптору и используй операции без
перехода по ссылкам, «внутри корня», либо убедись, что иерархия не может измениться за это время.

## Разбор находок аудита зависимостей

Аудит пакетных менеджеров сообщает об известных уязвимостях; он не доказывает, что пакет заслуживает
доверия или что уязвимый код достижим. Используй это дерево решений:

```
The native package-manager audit reports a vulnerability
├── Severity: critical or high
│   ├── Is the vulnerable code reachable in runtime, build, test, or deployment paths?
│   │   ├── YES --> Fix immediately (update, patch, or replace the dependency)
│   │   └── NO (confirmed unused across those paths) --> Fix soon, but not a blocker
│   └── Is a fix available?
│       ├── YES --> Update to the patched version
│       └── NO --> Check for workarounds, consider replacing the dependency, or add to allowlist with a review date
├── Severity: moderate
│   ├── Reachable in production? --> Fix in the next release cycle
│   └── Dev-only? --> Fix when convenient, track in backlog
└── Severity: low
    └── Track and fix during regular dependency updates
```

**Ключевые вопросы:**

- действительно ли уязвимая функция вызывается в твоём пути кода?
- зависимость нужна во время работы или только при разработке?
- эксплуатируема ли уязвимость в твоём контексте развёртывания (например, серверная уязвимость в
  приложении только для клиента)?

Когда откладываешь исправление, документируй причину и поставь дату пересмотра.

## Ограничение частоты

```typescript
import rateLimit from 'express-rate-limit';

// General API rate limit
app.use('/api/', rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,                   // 100 requests per window
  standardHeaders: true,
  legacyHeaders: false,
}));

// Stricter limit for auth endpoints
app.use('/api/auth/', rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10,  // 10 attempts per 15 minutes
}));
```

**Считай в общем хранилище, как только процессов больше одного.** `express-rate-limit` по умолчанию
держит счётчики в памяти процесса. За балансировщиком каждый экземпляр ведёт свой счёт, поэтому
действующий лимит — `max × число экземпляров`; в бессерверных и граничных средах новый вызов
начинается с нуля, так что лимит для аутентификации выше может не сработать никогда. Передай общий
`store` (Redis через `rate-limit-redis`) или используй ограничитель на HTTP, который работает там,
где не работает долгоживущее TCP-соединение (например, `@upstash/ratelimit`):

```typescript
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

const authLimiter = new Ratelimit({
  redis: Redis.fromEnv(),                       // UPSTASH_REDIS_REST_URL + _TOKEN
  limiter: Ratelimit.slidingWindow(10, '15 m'), // 10 attempts per 15 minutes, across all instances
});
const { success } = await authLimiter.limit(`login:${req.ip}`);
if (!success) return res.status(429).end();
```

## Управление секретами

```
.env files:
  ├── .env.example  → Committed (template with placeholder values)
  ├── .env          → NOT committed (contains real secrets)
  └── .env.local    → NOT committed (local overrides)

.gitignore must include:
  .env
  .env.local
  .env.*.local
  *.pem
  *.key
```

**Всегда проверяй перед коммитом:**

```bash
# Check for accidentally staged secrets — prints only the names of files whose
# staged diff matches, so the raw value never lands in terminal output or agent
# tool logs. Any output means review those files before committing.
git diff --cached -i -G'password|secret|api_key|token' --name-only
```

**Если секрет когда-либо попал в коммит, смени его.** Удалить строку или переписать историю
недостаточно: считай его скомпрометированным с момента, как он достиг удалённого репозитория.
Сначала отзови и перевыпусти ключ, затем вычисти его из истории.

## Классификация данных

Классифицируй персональные данные, добавляя поля, чтобы запросы на экспорт и удаление могли найти
их позже:

| Класс | Примеры | Обращение |
|---|---|---|
| **Неперсональные** | Агрегаты, анонимизированные счётчики | Обычное обращение |
| **Персональные (PII)** | Имя, email, IP, идентификаторы устройства и пользователя | Минимизация, контроль доступа, включать в экспорт и удаление |
| **Чувствительные** | Здоровье, финансы, местоположение, биометрия, государственные идентификаторы, всё о несовершеннолетних | Дополнительное основание для сбора, строже доступ, часто шифрование и журнал аудита |

## Обработка вывода LLM

```typescript
// BAD: trusting model output as a command or as markup
const sql = await llm.generate(`Write SQL for: ${userQuestion}`);
await db.query(sql);                                   // arbitrary query execution
container.innerHTML = await llm.reply(userMessage);   // stored XSS, via the model

// GOOD: model output is data — parse defensively, then validate, then encode
let intent;
try {
  intent = CommandSchema.parse(JSON.parse(await llm.replyJson(userMessage)));
} catch {
  throw new ValidationError('unexpected model output'); // JSON.parse or schema failed
}
await runAllowlistedAction(intent.action, intent.params);
container.textContent = await llm.reply(userMessage);
```
