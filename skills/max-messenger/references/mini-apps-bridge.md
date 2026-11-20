# MAX Bridge — справочник по SDK мини-приложений

**Содержание:** [Подключение](#подключение) · [Свойства верхнего уровня](#свойства-верхнего-уровня) · [Методы верхнего уровня](#методы-верхнего-уровня) · [Подобъекты](#подобъекты) · [Формат ошибки](#формат-ошибки) · [initData и initDataUnsafe](#initdata-и-initdataunsafe) · [Проверка initData](#проверка-initdata) · [Подтверждение телефона через requestContact](#подтверждение-телефона-через-requestcontact) · [Настройка и регистрация мини-приложения](#настройка-и-регистрация-мини-приложения) · [Диплинки](#диплинки) · [Чего не существует](#чего-не-существует) · [Ambient-объявление TypeScript](#ambient-объявление-typescript)

> Источник: BRIDGE https://dev.max.ru/docs/webapps/bridge · сверено 21.09.2026. Если это выглядит устаревшим, сначала проверь первоисточник.

Мини-приложения — это статические веб-приложения (HTML/JS/CSS), которые работают только внутри чат-бота MAX и не существуют отдельно. `window.WebApp` — мост между страницей и клиентом MAX.

## Подключение

Загрузи SDK с CDN один раз, до первого обращения к `window.WebApp`:

```html
<script src="https://st.max.ru/js/max-web-app.js"></script>
```

`window.WebApp` создаётся автоматически при каждом запуске и предзагружает свои данные — отдельного вызова `init()`/`ready()` нет. Все свойства и методы ниже доступны сразу после загрузки скрипта.

## Свойства верхнего уровня

| Свойство | Тип | Заметки |
|---|---|---|
| `initData` | `string` | Сырая строка в URL-кодировке, UTF-8. Единственное значение, безопасное для серверной проверки — см. [Проверка `initData`](#проверка-initdata). |
| `initDataUnsafe` | `InitData` | Разобранный объект для удобства, собранный на клиенте из `initData`. **Никогда не используй для проверки или авторизации** — см. структуру ниже. |
| `platform` | `'ios' \| 'android' \| 'desktop' \| 'web'` | Платформа, с которой запущено мини-приложение. |
| `version` | `string` | Версия клиентского приложения MAX в формате `<year>.<build_number>.<patch_version>`, например `25.9.16`. Это не «версия Bridge SDK» — отдельной такой версии в документации нет. В хэш проверки не входит. |
| `deviceName` | `string` | Человекочитаемая строка устройства или клиента, например `iPhone 16, iOS 26.5`, `Chrome, macOS`. |

## Методы верхнего уровня

Все методы, возвращающие `Promise`, при ошибке отклоняются с `{ error: { code: string } }` — см. [Формат ошибки](#формат-ошибки).

| Метод | Параметры | Возвращает | Платформа | Жест и ограничения |
|---|---|---|---|---|
| `getLaunchContext()` | — | `Promise<{ entryPoint: 'tabbar' \| 'default' }>` | Android ≥26.19.2, iOS ≥26.20.0 | `tabbar` — запуск с панели вкладок; `default` — из чата, списка чатов или экрана настроек. |
| `requestScreenMaxBrightness()` | — | `Promise<{ maxBrightness: boolean }>` | все | Максимальная яркость держится 30 с, затем восстанавливается автоматически. |
| `restoreScreenBrightness()` | — | `Promise<{ maxBrightness: boolean }>` | все | Немедленно возвращает исходную яркость. |
| `getViewportSize()` | — | `Promise<{ height: string; width: string }>` | все | Фиксированной или объявленной константы вьюпорта не существует — всегда читай этот метод и подстраивай вёрстку динамически. |
| `requestContact()` | — | `Promise<{ phone: string; authDate: string; hash: string }>` | все | Открывает нативное модальное окно. Данные годятся только внутри запросившего мини-приложения. См. [Подтверждение телефона через `requestContact`](#подтверждение-телефона-через-requestcontact). Отклоняется с `client.request_phone.user_refused_provide_phone_number` или `client.request_phone.request_error`. |
| `enableClosingConfirmation()` | — | — (односторонний вызов, без ответа) | все | Включает предупреждение о несохранённых данных при попытке пользователя закрыть мини-приложение. |
| `disableClosingConfirmation()` | — | — | все | Отключает это предупреждение. |
| `openLink(url)` | `url: string` | — | все | Открывает `url` во внешнем браузере. **Требуется непосредственно предшествующий клик или жест пользователя** — Bridge проверяет его и без него молча ничего не делает. |
| `openMaxLink(url)` | `url: string` | — | все | Открывает диплинк `https://max.ru/...` внутри MAX в новом листе. Неподходящие URL уходят во внешний браузер. |
| `downloadFile(url, file_name)` | `url: string` (любой хост по HTTPS), `file_name: string` | Promise, отклоняется при ошибке | Только в среде выполнения мини-приложения — **не работает** при открытии в обычной вкладке браузера | Нужен `url` по HTTPS (`http://` отклоняется) и **предшествующий клик пользователя**. Скачивание через `<a download>` и href не поддерживается — используй только этот метод. Отклоняется с `client.download_file.invalid_params` или `client.download_file.request_timeout` (таймаут нативного клиента 60 с). |
| `shareContent(params)` | `{ text?: string; link?: string }` (нужно хотя бы одно поле) | — | **Не поддерживается в web** (только iOS и Android) | Открывает системный лист «Поделиться». |
| `shareMaxContent(params)` | `{ text?: string; link?: string }` \| `{ mid: string; chatType: 'DIALOG' \| 'CHAT' }` | — | все | **Требуется предшествующий клик пользователя.** Открывает экран отправки внутри MAX. Два режима: отправка текста или ссылки либо пересылка сообщения, отправленного ботом (`mid` — id сообщения из ответа `POST /messages`; `chatType` — `DIALOG` для личного чата, `CHAT` для группы, где пользователь состоит). Если передать обе формы сразу, `text` и `link` игнорируются. |
| `openCodeReader(fileSelect?)` | `fileSelect?: boolean` (по умолчанию `true`) | `Promise<string>` (раскодированное содержимое QR) | все | При `fileSelect=true` дополнительно предлагается выбор из галереи или файлов; `fileSelect=false` — только камера. |

## Подобъекты

### BackButton

| Член | Сигнатура | Заметки |
|---|---|---|
| `isVisible` | `boolean` | По умолчанию `false`. |
| `show()` | `(): void` | Делает кнопку «Назад» в шапке видимой и активной. |
| `hide()` | `(): void` | Скрывает её. |
| `onClick(callback)` | `(callback: () => void): void` | Сохрани ссылку на `callback`, чтобы потом отписаться. |
| `offClick(callback)` | `(callback: () => void): void` | Убирает обработчик. |

`BackButton.onClick` и `offClick` — **единственная** пара «подписка/отписка», описанная на всей странице Bridge — см. [Чего не существует](#чего-не-существует).

### DeviceStorage

Локальное хранилище устройства в расчёте на пользователя, привязанное к мини-приложению. **Не поддерживается в web.**

| Член | Сигнатура |
|---|---|
| `setItem(key, value)` | `(key: string, value: string): Promise<void>` |
| `getItem(key)` | `(key: string): Promise<string>` |
| `removeItem(key)` | `(key: string): Promise<void>` |
| `clear()` | `(): Promise<void>` — очищает все ключи, ранее сохранённые ботом. |

### SecureStorage

Та же структура, что у `DeviceStorage`, но с шифрованием — подходит для токенов, секретов и состояния авторизации. **Не поддерживается в web. Жёсткий предел: 10 ключей на бота на пользователя** — проектируй схему хранения (пространства имён, переиспользование) с учётом этого, это не безлимитное key-value хранилище.

| Член | Сигнатура |
|---|---|
| `setItem(key, value)` | `(key: string, value: string): Promise<void>` |
| `getItem(key)` | `(key: string): Promise<string>` |
| `removeItem(key)` | `(key: string): Promise<void>` |
| `clear()` | `(): Promise<void>` |

### BiometricManager

**Не поддерживается на desktop и в web.** Вызови `init()` один раз до любого другого члена.

| Член | Сигнатура | Заметки |
|---|---|---|
| `init()` | `(): Promise<BiometryInfo>` | Проверяет возможности устройства и выдан ли доступ. |
| `isInited` | `boolean` | Запускался ли `init()`. |
| `isBiometricAvailable` | `boolean` | `false`, если пользователь отказал в доступе. |
| `isAccessRequested` | `boolean` | `false`, если пользователь отказал. |
| `isAccessGranted` | `boolean` | `false`, если пользователь отказал. |
| `isBiometricTokenSaved` | `boolean` | Есть ли уже токен авторизации в защищённом хранилище. |
| `biometricType` | `Array<'finger' \| 'face' \| 'unknown'>` | `["unknown"]` при отказе; на Android всегда `["unknown"]`. |
| `deviceId` | `string \| null` | `null` при отказе в доступе; используй, чтобы привязать токен к этому устройству. |
| `requestAccess(reason?)` | `(reason?: string): Promise<BiometryInfo>` | `reason` — от 1 до 128 символов, длиннее обрезается. |
| `authenticate(reason?)` | `(reason?: string): Promise<void>` | Запускает биометрическую аутентификацию; что именно возвращается помимо факта успеха или неудачи, не описано — не рассчитывай на конкретную структуру. |
| `updateBiometricToken(token?, reason?)` | `(token?: string, reason?: string): Promise<void>` | Вызов без `token` удаляет сохранённый токен. |
| `openSettings()` | `(): Promise<{ status: 'opened' }>` | Открывает нативные настройки приватности MAX. **Закрывает мини-приложение.** |

`BiometryInfo` = `{ isInited, isBiometricAvailable, isAccessRequested, isAccessGranted, isBiometricTokenSaved, biometricType, deviceId }` (те же поля, что и свойства выше).

### HapticFeedback

**Не поддерживается на desktop и в web.**

| Член | Сигнатура | Заметки |
|---|---|---|
| `impactOccurred(impactStyle, disableVibrationFallback?)` | `(impactStyle: 'soft'\|'light'\|'medium'\|'heavy'\|'rigid', disableVibrationFallback?: boolean): void` | Для отклика на нажатие и взаимодействие. `disableVibrationFallback` по умолчанию `false`. |
| `notificationOccurred(notificationType, disableVibrationFallback?)` | `(notificationType: 'error'\|'success'\|'warning', disableVibrationFallback?: boolean): void` | |
| `selectionChanged(disableVibrationFallback?)` | `(disableVibrationFallback?: boolean): void` | Используй только когда выбор пользователя *меняется*, а не когда он подтверждает уже сделанный выбор. |

### NfcManager

**Только Android.** Вызови `init()` до любого другого члена.

| Член | Сигнатура | Заметки |
|---|---|---|
| `init()` | `(): Promise<{ available: boolean; enabled: boolean; accessRevoked?: boolean }>` | |
| `isInited` | `boolean` | |
| `openSystemSettings()` | `(): Promise<{ status: 'opened' }>` | Открывает системные настройки NFC. **Закрывает мини-приложение.** Ничего не делает, если пользователь никогда не отключал NFC. |
| `emulateNfcTag(nfctag?)` | `(nfctag?: string): void` | Передаёт данные по NFC; вызов без метки прекращает передачу. |

### ScreenCapture

| Член | Сигнатура |
|---|---|
| `enableScreenCapture()` | `(): Promise<{ isScreenCaptureEnabled: boolean }>` — разрешает скриншоты и запись экрана |
| `disableScreenCapture()` | `(): Promise<{ isScreenCaptureEnabled: boolean }>` — запрещает их |

## Формат ошибки

Все отклонения Promise в Bridge имеют одну общую структуру:

```
{ error: { code: string } }
```

Описаны только эти коды: `client.download_file.invalid_params`, `client.download_file.request_timeout`, `client.request_phone.user_refused_provide_phone_number`, `client.request_phone.request_error`. Других кодов в документации нет — не выдумывай коды для остальных методов.

## `initData` и `initDataUnsafe`

```typescript
interface InitData {
  query_id: string;
  ip?: string;
  auth_date: number;
  hash: string;
  user: {
    id: number;
    first_name: string;
    last_name: string;
    username: string;
    language_code: string;
    photo_url: string;
  };
  chat: {
    id: number;
    type: 'DIALOG' | 'CHAT' | 'CHANNEL';
  };
  start_param: string;
}
```

`query_id` — уникальный идентификатор сессии. `ip?` — IP пользователя. `auth_date` — время выдачи в секундах Unix (рекомендуемое окно валидности — 1 час). `hash` — подпись для проверки. `user.*` — профиль пользователя, открывшего мини-приложение. `chat.id` и `chat.type` — чат, в котором открыто мини-приложение. `start_param` — значение, переданное через `?startapp=` в диплинке, которым открыли мини-приложение (см. [Диплинки](#диплинки)).

`initDataUnsafe` — тот же объект, разобранный на клиенте для удобства. Для твоего кода это **не** подписанные и не проверенные данные, и их нельзя использовать для аутентификации.

## Проверка `initData`

`initData` подписан через `HMAC-SHA256`: ключ выводится из литеральной строки `"WebAppData"` и токена бота, а затем этим производным ключом подписываются отсортированные пары `key=value`, соединённые `\n`. Полный алгоритм с проверенными валидаторами на Go и TypeScript — в [`webhooks-and-security.md`](./webhooks-and-security.md).

## Подтверждение телефона через `requestContact`

Поле `hash` у `requestContact()` считается по **другой, более простой** формуле, чем у `initData`: HMAC берётся сразу от отсортированных полей `authDate`, `phone` и `userId` с сырым токеном бота (без предварительного вывода ключа из `"WebAppData"`), а у `phone` перед хэшированием нужно убрать ведущий `+`. Полная формула и код — в [`webhooks-and-security.md`](./webhooks-and-security.md).

## Настройка и регистрация мини-приложения

Мини-приложения регистрируются для каждого бота отдельно на `business.max.ru/self`: **Чат-боты → выбери бота → ⋮ → Настройки → вставь URL мини-приложения → выбери подпись кнопки (Открыть / Старт / Играть / без подписи) → Сохранить.** Отдельной регистрации мини-приложения вне бота нет.

Требования к URL: не длиннее 1024 символов, протокол **обязательно `https://`**, допустимые символы — латинские буквы, цифры, `.` и `-` (без пробелов), строка должна быть корректным URL. Само приложение — статические HTML/JS/CSS и ресурсы, отдаваемые по HTTPS с любого хоста (GitHub Pages, Yandex Cloud, VK Cloud и т. п.). Повторный деплой на тот же URL обновляет мини-приложение на месте; при смене URL владельцу бота придётся обновить его в настройках бота ещё раз. Одновременно может быть открыто только одно мини-приложение — открытие нового закрывает текущее.

Чтобы открыть мини-приложение с клавиатуры бота, используй кнопку `open_app`. Помощник в TS-клиенте — `openApp(text, webApp, contactId?, payload?)`. В Go-клиенте `KeyboardRow.AddOpenApp(text, botID)` записывает в JSON-поле `web_app` кнопки её отображаемый `text`, а не URL — это помечено в исходниках комментарием `// ignored, required`. Считай Go-билдер `open_app` подозрительным: сверь точное поле со схемой API (см. [`bot-api.md`](./bot-api.md)) прежде чем на него полагаться, а при сомнениях собери JSON кнопки вручную.

## Диплинки

Два разных формата, которые легко перепутать:

| Ссылка | Параметр нагрузки | Максимальная длина | Назначение |
|---|---|---|---|
| `https://max.ru/<botName>?start=<payload>` | `start` | 128 символов | Открывает только чат с ботом (не мини-приложения). |
| `https://max.ru/<botName>?startapp=<payload>` | `startapp` | 512 символов | Запускает мини-приложение бота, а `payload` попадает в `start_param`. |

Допустимые символы нагрузки `startapp`: только `A-Za-z0-9_-`. Если нагрузка длиннее 512 символов или содержит недопустимые символы, она **молча вырезается из URL** — разработчику никакой ошибки не показывают, поэтому проверяй формат нагрузки до сборки ссылок. Оба типа ссылок требуют клиента MAX iOS ≥2.7.0 и Android ≥2.9.0.

Нагрузка доходит до мини-приложения и как `initDataUnsafe.start_param`, и внутри сырой строки `initData`.

Есть ещё отдельный диплинк для отправки контента: `https://max.ru/:share?text=<текст сообщения>` открывает выбор чата MAX с уже заполненным `text` (текст нужно URL-кодировать). Доступен на iOS, Android и в web; поддержка на desktop на дату сверки этой документации «в разработке» — не предполагай одинакового поведения для всех четырёх значений `platform` ни для этой возможности, ни для любой другой, не проверив её собственную пометку об ограничениях платформы выше.

## Чего не существует

- **API темы и CSS-переменных нет.** Bridge не отдаёт ни `themeParams`, ни CSS-переменные вида `--*-theme-*`, ни какой-либо сигнал о цветовой схеме. Не переноси подходы к темизации из Telegram. Если мини-приложение должно визуально совпадать с клиентом MAX, это делается средствами компонентов и гайдлайнов MAX UI ([`max-ui.md`](./max-ui.md)), а не через Bridge.
- **Универсальной шины событий нет.** Нет `onEvent`, `offEvent` и какого-либо pub-sub API. Единственная пара «подписка/отписка», описанная на этой странице, — `BackButton.onClick` и `offClick`.

## Ambient-объявление TypeScript

Минимальные ambient-типы для всего описанного выше — скопируй в файл `.d.ts` (или в начало модуля), чтобы получить поддержку `window.WebApp` в редакторе и компиляторе.

```typescript
export {};

declare global {
  interface MaxWebAppInitDataUser {
    id: number; first_name: string; last_name: string;
    username: string; language_code: string; photo_url: string;
  }
  interface MaxWebAppInitDataChat { id: number; type: 'DIALOG' | 'CHAT' | 'CHANNEL'; }
  interface MaxWebAppInitData {
    query_id: string; ip?: string; auth_date: number; hash: string;
    user: MaxWebAppInitDataUser; chat: MaxWebAppInitDataChat; start_param: string;
  }

  interface MaxWebAppBiometryInfo {
    isInited: boolean; isBiometricAvailable: boolean; isAccessRequested: boolean;
    isAccessGranted: boolean; isBiometricTokenSaved: boolean;
    biometricType: Array<'finger' | 'face' | 'unknown'>; deviceId: string | null;
  }

  interface MaxWebAppBackButton {
    readonly isVisible: boolean;
    show(): void;
    hide(): void;
    onClick(callback: () => void): void;
    offClick(callback: () => void): void;
  }

  interface MaxWebAppKeyValueStorage {
    setItem(key: string, value: string): Promise<void>;
    getItem(key: string): Promise<string>;
    removeItem(key: string): Promise<void>;
    clear(): Promise<void>;
  }

  interface MaxWebAppBiometricManager extends MaxWebAppBiometryInfo {
    init(): Promise<MaxWebAppBiometryInfo>;
    requestAccess(reason?: string): Promise<MaxWebAppBiometryInfo>;
    authenticate(reason?: string): Promise<void>;
    updateBiometricToken(token?: string, reason?: string): Promise<void>;
    openSettings(): Promise<{ status: 'opened' }>;
  }

  interface MaxWebAppHapticFeedback {
    impactOccurred(impactStyle: 'soft' | 'light' | 'medium' | 'heavy' | 'rigid', disableVibrationFallback?: boolean): void;
    notificationOccurred(notificationType: 'error' | 'success' | 'warning', disableVibrationFallback?: boolean): void;
    selectionChanged(disableVibrationFallback?: boolean): void;
  }

  interface MaxWebAppNfcManager {
    readonly isInited: boolean;
    init(): Promise<{ available: boolean; enabled: boolean; accessRevoked?: boolean }>;
    openSystemSettings(): Promise<{ status: 'opened' }>;
    emulateNfcTag(nfctag?: string): void;
  }

  interface MaxWebAppScreenCapture {
    enableScreenCapture(): Promise<{ isScreenCaptureEnabled: boolean }>;
    disableScreenCapture(): Promise<{ isScreenCaptureEnabled: boolean }>;
  }

  interface MaxWebAppShareContentParams { text?: string; link?: string; }
  type MaxWebAppShareMaxContentParams =
    | MaxWebAppShareContentParams
    | { mid: string; chatType: 'DIALOG' | 'CHAT' };
  interface MaxWebAppRequestContactResult { phone: string; authDate: string; hash: string; }

  interface MaxWebApp {
    readonly initData: string;
    readonly initDataUnsafe: MaxWebAppInitData;
    readonly platform: 'ios' | 'android' | 'desktop' | 'web';
    readonly version: string;
    readonly deviceName: string;

    readonly BackButton: MaxWebAppBackButton;
    readonly DeviceStorage: MaxWebAppKeyValueStorage;
    readonly SecureStorage: MaxWebAppKeyValueStorage;
    readonly BiometricManager: MaxWebAppBiometricManager;
    readonly HapticFeedback: MaxWebAppHapticFeedback;
    readonly NfcManager: MaxWebAppNfcManager;
    readonly ScreenCapture: MaxWebAppScreenCapture;

    getLaunchContext(): Promise<{ entryPoint: 'tabbar' | 'default' }>;
    requestScreenMaxBrightness(): Promise<{ maxBrightness: boolean }>;
    restoreScreenBrightness(): Promise<{ maxBrightness: boolean }>;
    getViewportSize(): Promise<{ height: string; width: string }>;
    requestContact(): Promise<MaxWebAppRequestContactResult>;
    enableClosingConfirmation(): void;
    disableClosingConfirmation(): void;
    openLink(url: string): void;
    openMaxLink(url: string): void;
    downloadFile(url: string, file_name: string): Promise<void>;
    shareContent(params: MaxWebAppShareContentParams): Promise<void>;
    shareMaxContent(params: MaxWebAppShareMaxContentParams): Promise<void>;
    openCodeReader(fileSelect?: boolean): Promise<string>;
  }

  interface Window { WebApp: MaxWebApp; }
}
```
