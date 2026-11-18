# Синтаксис диаграмм

Короткие рабочие примеры каждого типа диаграмм. Каждый пример здесь рендерится в тестах этого
репозитория. Полная документация: https://mermaid.js.org/intro/,
https://d2lang.com/tour/intro, https://plantuml.com/.

## Mermaid

### Блок-схема и архитектура

```mermaid
flowchart LR
  user([Customer]) -->|HTTPS| web[Web app]
  subgraph platform [Shop platform]
    web -->|REST| api[Orders API]
    api -->|SQL| db[(Postgres)]
    api -->|publishes OrderPlaced| bus{{Event bus}}
  end
  bus --> mail[Email worker]
```

Направления: `TD` (сверху вниз), `LR`, `BT`, `RL`. Фигуры: `[прямоугольник]`, `(скруглённый)`,
`([стадион])`, `[(база данных)]`, `{решение}`, `{{шестиугольник}}`, `((круг))`. Рёбра: `-->`,
`-.->` (пунктир), `==>` (толстое), `-->|подпись|`.

### Последовательности

```mermaid
sequenceDiagram
  autonumber
  actor U as User
  participant A as API
  participant P as Payments
  U->>A: POST /checkout
  A->>P: charge(card, total)
  alt card accepted
    P-->>A: ok
    A-->>U: 201 Created
  else declined
    P-->>A: declined
    A-->>U: 402 Payment Required
  end
  Note over A,P: retried up to 3 times
```

Стрелки: `->>` вызов, `-->>` ответ, `-x` сбой, `-)` асинхронно. Блоки: `alt/else`, `opt`,
`loop`, `par/and`, `critical`, `break`.

### Классы

```mermaid
classDiagram
  class Order {
    +String id
    +Money total
    +place() void
  }
  class LineItem {
    +int quantity
  }
  Order "1" *-- "1..*" LineItem : contains
  Order --> Customer : placed by
  PaymentMethod <|.. Card
```

Отношения: `<|--` наследование, `<|..` реализация, `*--` композиция, `o--` агрегация,
`-->` ассоциация, `..>` зависимость.

### Состояния

```mermaid
stateDiagram-v2
  [*] --> Draft
  Draft --> Submitted : submit()
  Submitted --> Approved : approve
  Submitted --> Draft : request changes
  Approved --> [*]
```

### ER

```mermaid
erDiagram
  CUSTOMER ||--o{ ORDER : places
  ORDER ||--|{ LINE_ITEM : contains
  PRODUCT ||--o{ LINE_ITEM : "appears in"
  ORDER {
    uuid id PK
    uuid customer_id FK
    timestamp placed_at
  }
```

Кардинальность: `||` ровно один, `|o` ноль или один, `}|` один или больше, `}o` ноль или больше.

### Гант

```mermaid
gantt
  title Release plan
  dateFormat YYYY-MM-DD
  section Build
    API changes   :a1, 2026-01-05, 10d
    UI            :after a1, 7d
  section Ship
    Beta          :milestone, 2026-01-26, 0d
```

### Интеллект-карта

```mermaid
mindmap
  root((Whiteboard))
    Languages
      Mermaid
      D2
      PlantUML
    Outputs
      SVG
      PNG
```

### ZenUML (последовательности, записанные как код)

```mermaid
zenuml
  title Orders
  @Actor User
  User->Shop.order(id) {
    if(inStock) {
      Shop->Warehouse.ship(id)
    } else {
      return backordered
    }
  }
```

### Другие типы Mermaid

Каждый из них рендерится; используй их, когда они подходят к вопросу лучше блок-схемы.

```mermaid
C4Context
  Person(user, "Customer")
  System(shop, "Shop", "Takes orders")
  System_Ext(pay, "Payments")
  Rel(user, shop, "Orders from")
  Rel(shop, pay, "Charges via")
```

```mermaid
architecture-beta
  group api(cloud)[Platform]
  service web(internet)[Web] in api
  service app(server)[Orders API] in api
  service db(database)[Postgres] in api
  web:R -- L:app
  app:R -- L:db
```

```mermaid
gitGraph
  commit
  branch feature
  commit
  checkout main
  merge feature
  commit
```

```mermaid
timeline
  title Releases
  2025 Q1 : Beta
  2025 Q3 : 1.0
  2026 Q1 : 2.0
```

```mermaid
journey
  title Checkout
  section Cart
    Add item: 5: Customer
    Review cart: 3: Customer
  section Pay
    Enter card: 2: Customer
```

```mermaid
pie title Requests by service
  "Orders" : 45
  "Search" : 35
  "Accounts" : 20
```

```mermaid
quadrantChart
  title Effort vs impact
  x-axis Low effort --> High effort
  y-axis Low impact --> High impact
  Caching: [0.2, 0.8]
  Rewrite: [0.9, 0.6]
```

```mermaid
xychart-beta
  title "Latency (ms)"
  x-axis [Mon, Tue, Wed, Thu]
  bar [120, 95, 140, 80]
  line [120, 95, 140, 80]
```

```mermaid
sankey-beta
  Visits,Signups,30
  Visits,Bounced,70
  Signups,Paid,10
```

```mermaid
block-beta
  columns 3
  web["Web"] api["API"] db[("DB")]
```

```mermaid
kanban
  todo[To do]
    t1[Write docs]
  doing[In progress]
    t2[Sandbox renderer]
```

```mermaid
requirementDiagram
  requirement offline {
    id: 1
    text: Renders without network
    risk: low
    verifymethod: test
  }
```

```mermaid
packet-beta
  0-15: "Source port"
  16-31: "Destination port"
  32-63: "Sequence number"
```

```mermaid
radar-beta
  axis speed, safety, coverage
  curve v1{2, 3, 3}
  curve v2{4, 5, 4}
```

```mermaid
treemap-beta
  "Repo"
    "src": 60
    "tests": 25
    "docs": 15
```

## D2

Хорош для больших архитектурных диаграмм: контейнеры вкладываются, раскладка автоматическая.

```d2
direction: right
customer: Customer {shape: person}
platform: Shop platform {
  web: Web app
  api: Orders API
  db: Postgres {shape: cylinder}
  web -> api: REST
  api -> db: SQL
}
customer -> platform.web: HTTPS
```

## PlantUML

Оборачивай каждую диаграмму в `@startuml` / `@enduml`.

```plantuml
@startuml
actor User
participant API
database DB
User -> API: GET /orders
API -> DB: SELECT
DB --> API: rows
API --> User: 200 OK
@enduml
```

## Частые ошибки и исправления

| Ошибка | Исправление |
|---|---|
| `Parse error on line N` с `(`, `)`, `[`, `]`, `{`, `}` или `:` в подписи | Возьми подпись в кавычки: `A["calls f(x)"]`. В сообщениях последовательностей избегай `;` и `#`. |
| `No diagram type detected` | Первая строка должна быть типом диаграммы (`flowchart TD`, `sequenceDiagram` и т. д.), и перед ней ничего не должно быть. |
| Узел с именем `end` ломает блок-схему | `end` — ключевое слово: используй `End` или `finish[end]`. |
| `-->` внутри диаграммы последовательностей | Стрелки последовательностей — `->>` и `-->>`. |
| Член класса с дженериком не проходит | Используй `~`: `List~Order~ items`. |
| Атрибут ER не проходит | Каждый атрибут — `тип имя` с необязательным `PK`, `FK` или `UK`; пробелов нет ни там, ни там. |
| Заголовки подграфов с пробелами | `subgraph id [Title with spaces]`. |
| D2 `err: ... unexpected text` | Возьми ключи и подписи со спецсимволами в кавычки: `"user (admin)"`. |
| PlantUML `Syntax Error?` | Проверь `@startuml`/`@enduml` и написание стрелок (`->`, `-->`). |
