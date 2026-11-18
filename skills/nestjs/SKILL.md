---
name: nestjs
description: "Разработка серверных приложений на NestJS: модули, провайдеры и внедрение зависимостей, контроллеры и порядок конвейера запроса (middleware, guards, interceptors, pipes, filters), валидация DTO, конфигурация, работа с базами, аутентификация, GraphQL, WebSocket и микросервисы. Используй при работе с пакетами `@nestjs/*`, CLI `nest` и любой задачей внутри приложения на NestJS."
license: MIT
metadata:
  author: iamursky
  source: https://github.com/iamursky/nestjs-skill
---

# NestJS — прогрессивный серверный фреймворк

NestJS — фреймворк для **эффективных и масштабируемых серверных приложений на Node.js**. Он ориентирован на **TypeScript**, строго **модульный** и построен вокруг **внедрения зависимостей**. Внизу работает сменная HTTP-платформа — **Express** (по умолчанию, `@nestjs/platform-express`) или **Fastify** (`@nestjs/platform-fastify`), — и те же строительные блоки обслуживают приложения на **GraphQL**, **WebSocket** и **микросервисах**. Архитектура во многом повторяет Angular: декораторы + внедрение зависимостей + модули.

## Модель мышления — три строительных блока

1. **Модули** организуют приложение. У каждого есть корневой `AppModule`; у функции — свой модуль. `@Module({ imports, controllers, providers, exports })` объявляет, чем модуль владеет и что отдаёт наружу.
2. **Провайдеры** держат логику и связываются через **внедрение зависимостей**. Помечай класс `@Injectable()`, перечисляй его в `providers` модуля и внедряй через конструктор. Большинство «сервисов», репозиториев, фабрик и помощников — провайдеры.
3. **Контроллеры** принимают запросы и возвращают ответы. Декораторы сопоставляют маршруты с методами-обработчиками.

```typescript
// cats.controller.ts
import { Controller, Get } from '@nestjs/common';
import { CatsService } from './cats.service';

@Controller('cats')
export class CatsController {
  constructor(private readonly catsService: CatsService) {} // внедрение по типу

  @Get()
  findAll() {
    return this.catsService.findAll();
  }
}
```

```typescript
// cats.module.ts
import { Module } from '@nestjs/common';

@Module({
  controllers: [CatsController],
  providers: [CatsService],   // доступен для внедрения внутри модуля
  exports: [CatsService],     // доступен модулям, которые импортируют этот
})
export class CatsModule {}
```

## Настройка и точка входа

```bash
npm i -g @nestjs/cli      # CLI Nest
nest new project-name     # создание проекта (спросит менеджер пакетов; --strict для строгого TS)
nest g resource cats      # генерация CRUD: модуль, контроллер, сервис, DTO
```

`main.ts` поднимает приложение через `NestFactory`:

```typescript
// main.ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  await app.listen(process.env.PORT ?? 3000);
}
bootstrap();
```

Для приложения без HTTP (CLI, cron, воркер) используй `NestFactory.createApplicationContext`.

## Конвейер запроса (канонический порядок)

Это самое важное, что нужно не перепутать. Запрос проходит сквозные компоненты в **фиксированном порядке**: сначала глобальные, затем привязанные к контроллеру, затем к маршруту (исключение — фильтры: они разрешаются от маршрута к контроллеру и глобальным):

1. **Middleware** — глобальные, затем привязанные к модулю; работают до guards.
2. **Guards** — «можно ли это пропустить»: аутентификация и авторизация.
3. **Interceptors (до)** — оборачивают обработчик, могут преобразовывать и наблюдать.
4. **Pipes** — валидируют и преобразуют входные данные (параметры, тело, строка запроса).
5. **Обработчик маршрута** — метод контроллера вызывает провайдеров.
6. **Interceptors (после)** — преобразуют ответ (RxJS, последний пришёл — первый вышел).
7. **Exception filters** — только при необработанной ошибке; формируют ответ.

Любой из них привязывается на трёх уровнях: **глобально** (`app.useGlobalX()` или провайдер с токеном `APP_*`), **на контроллере** (декоратор на классе) и **на маршруте** (декоратор на методе). Порядок привязки pipes и interceptors не просто сверху вниз: параметрические pipes разрешаются от последнего параметра к первому.

Свою логику, зависящую от запроса, строй на **пользовательских декораторах** и **контексте выполнения** (`ExecutionContext`, `Reflector` для чтения метаданных, выставленных через `@SetMetadata`).

## Внедрение зависимостей и основы

Внедрение разрешается **по типу** (класс параметра конструктора) или **по токену** (`@Inject(TOKEN)`). Провайдер виден только внутри своего модуля, если он не указан в `exports`, а модуль потребителя не импортирует модуль-владелец.

- **Пользовательские провайдеры** — `useClass`, `useValue`, `useFactory` (с `inject`), `useExisting`, а также токены не-классы.
- **Асинхронные провайдеры** — `useFactory`, возвращающая Promise (например, ожидание соединения с базой).
- **Динамические модули** — `Module.forRoot()` и `forFeature()` для настраиваемых модулей.
- **Области внедрения** — `DEFAULT` (синглтон), `REQUEST`, `TRANSIENT`. Request-область стоит производительности и «пузырится» вверх по цепочке.
- **Циклическая зависимость** — разрывается через `forwardRef()` с обеих сторон.
- **Ссылка на модуль** — императивное получение провайдеров через `ModuleRef`.
- **Хуки жизненного цикла** — `OnModuleInit`, `OnApplicationBootstrap`, `OnModuleDestroy`, `OnApplicationShutdown` (для последнего включи shutdown-хуки).

## Валидация, конфигурация и базы данных

- **Валидация** — глобальный `ValidationPipe` плюс декораторы `class-validator` и `class-transformer` на DTO (`whitelist`, `transform`, `forbidNonWhitelisted`).
- **Конфигурация** — `ConfigModule.forRoot()` из `@nestjs/config` и `ConfigService`, файлы `.env`, схема валидации, конфигурация по пространствам имён.
- **SQL (TypeORM или Sequelize)** — `forRoot` и `forFeature`, репозитории, сущности. Для Prisma и MikroORM есть отдельные рецепты.
- **MongoDB (Mongoose)** — `@nestjs/mongoose`, схемы, модели.

## Приёмы, которые нужны регулярно

Кэширование · очереди на BullMQ · планировщик задач и cron · события · логгер · сериализация (`ClassSerializerInterceptor`) · версионирование API · загрузка файлов · потоковая отдача файлов · Server-Sent Events · cookies · сессии · сжатие · HTTP-модуль (`HttpService` на axios) · MVC · производительность на Fastify.

## Безопасность

Аутентификация (стратегии Passport, JWT, `@nestjs/passport` и `@nestjs/jwt`) · авторизация (RBAC, claims, CASL) · ограничение частоты запросов (`@nestjs/throttler`) · Helmet · CORS · CSRF · шифрование и хеширование. Аутентификация обычно реализуется **guard**; авторизация — guard плюс метаданные, прочитанные через `Reflector`.

## GraphQL, WebSocket и микросервисы

- **GraphQL** — `@nestjs/graphql` с драйвером Apollo (или Mercurius); **code-first** (декораторы и сгенерированная SDL) или **schema-first**. Резолверы, мутации, подписки, федерация.
- **WebSocket** — шлюзы `@WebSocketGateway()` (socket.io или ws) с той же моделью guards, pipes, interceptors и filters.
- **Микросервисы** — `@nestjs/microservices`: выбери транспорт (TCP, Redis, NATS, MQTT, RabbitMQ, Kafka, gRPC) и используй `@MessagePattern` для «запрос — ответ» либо `@EventPattern` для события.

## OpenAPI, тесты и развёртывание

- **OpenAPI / Swagger** — `SwaggerModule` из `@nestjs/swagger`, декораторы `@ApiProperty()` и CLI-плагин, который выводит схемы автоматически.
- **Тесты** — `Test.createTestingModule(...)` из `@nestjs/testing`, `.overrideProvider(...)`, юнит-тесты и e2e на `supertest`.
- **Развёртывание** — обычный Node-процесс или serverless; для графа зависимостей есть Devtools.

## Грабли

- **«Nest can't resolve dependencies of X»** — зависимость не объявлена в `providers` текущего модуля, либо её модуль не экспортирует её и не импортируется. Сначала смотри граф модулей.
- **Декораторам нужен TS-конфиг** — `experimentalDecorators` и `emitDecoratorMetadata`, плюс однократный импорт `reflect-metadata`. Внедрение по типу опирается на испускаемые метаданные.
- **Глобальные pipes, guards и прочее через `app.useGlobalX()` не умеют внедрять зависимости** — чтобы внедрение работало, регистрируй их провайдерами `APP_PIPE`, `APP_GUARD`, `APP_INTERCEPTOR`, `APP_FILTER`.
- **`ValidationPipe` бесполезен без DTO**, размеченных `class-validator`, и требует `transform: true`, чтобы создавать экземпляры классов DTO и приводить типы. `whitelist` отбрасывает неизвестные свойства.
- **Циклические `imports` и провайдеры** — `forwardRef()` с обеих сторон; лучше перестроить структуру.
- **Провайдеры с request-областью** делают всю цепочку внедрения request-областной — заметные накладные расходы, держи её короткой.
- **Держи версии `@nestjs/*` согласованными** — core, common, platform и пакеты экосистемы переходят между мажорами вместе.
