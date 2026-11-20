---
name: tilda
description: "Сборка и настройка сайтов на Tilda — конструкторе сайтов без кода с расширенной кастомизацией. Используй, когда просят «сделать сайт на Tilda», «Tilda Publishing», «настроить сайт на Tilda», «API Tilda», «конструктор лендингов», «сайт без кода», «свой код на Tilda» или «интегрировать Tilda с внешними сервисами». Покрывает блочную сборку, свой HTML/CSS/JS, API Tilda, обработку форм, электронную коммерцию и интеграции."
license: Apache-2.0
compatibility: "Редактор в браузере. Свой код: HTML/CSS/JS. API: REST."
metadata:
  author: terminal-skills
  source: https://github.com/TerminalSkills/skills
---

# Tilda Publishing

## Обзор

Tilda — блочный конструктор сайтов: перетаскивай блоки на страницу, настраивай их визуально и публикуй. Ни бэкенда, ни хостинга настраивать не нужно. Для разработчика: вставляй свой HTML/CSS/JS в любой блок, используй API Tilda только для чтения, чтобы синхронизировать опубликованные страницы со своим сервером, подключай формы к любому бэкенду и собирай свои интеграции. Хорошо подходит для маркетинговых сайтов, лендингов и небольших интернет-магазинов, где контент обновляют сотрудники без технической подготовки.

## Когда использовать

- Нужно быстро собрать маркетинговый сайт или лендинг.
- Нужна CMS, которую легко обновлять без разработчика.
- Небольшая или средняя электронная коммерция (встроенный магазин Tilda).
- Кастомные лендинги с продвинутыми анимациями.
- Сайты, где нужны и визуальный редактор, и свой код.

## Инструкции

### Структура сайта

Сайт на Tilda устроен так:
- **Проект** → содержит страницы.
- **Страница** → содержит блоки (секции).
- **Блок** → готовый дизайн секции (первый экран, преимущества, тарифы, галерея и т. д.).
- **Zero Block** — свой блок, где дизайн полностью в твоих руках.

### Свой HTML/CSS/JS в блоках

Код для `<head>` (CSS, метатеги) кладётся в «Настройки сайта → Ещё → HTML-код для вставки внутрь head» (для всех страниц) либо в «Настройки страницы → Дополнительно → HTML-код для вставки внутрь head» (для одной страницы). Код для тела страницы кладётся в блок T123 «HTML-код» (Библиотека блоков → Другое) или в HTML-элемент внутри Zero Block. Редактор и предпросмотр показывают вставленный код как текст, он выполняется только на опубликованной странице.

```html
<!-- Секция head: переопределяем стили Tilda; nw-reveal — твой собственный класс в твоей разметке -->
<style>
  .t-title { font-family: 'Inter', sans-serif !important; }
  .nw-reveal { opacity: 0; transform: translateY(20px); transition: all 0.6s ease; }
  .nw-reveal.is-visible { opacity: 1; transform: translateY(0); }
  @media (max-width: 640px) { .t-cover__wrapper { min-height: 60vh !important; } }
</style>

<!-- Блок T123: показываем элементы .nw-reveal при попадании в область видимости -->
<script>
  document.addEventListener('DOMContentLoaded', () => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) entry.target.classList.add('is-visible');
      });
    }, { threshold: 0.1 });
    document.querySelectorAll('.nw-reveal').forEach((el) => observer.observe(el));
  });
</script>
```

### Zero Block (свой дизайн)

Zero Block даёт полный контроль в духе графического редактора: расставляй элементы точно, задавай свои позиции, анимации и контрольные точки адаптивности.

```html
<!-- Вставь в HTML-элемент Zero Block (или в блок T123) -->
<div class="custom-calculator" id="price-calc">
  <h3>Калькулятор стоимости</h3>
  <div class="calc-row">
    <label>Количество пользователей</label>
    <input type="range" id="users" min="1" max="1000" value="10">
    <span id="users-count">10</span>
  </div>
  <div class="calc-row">
    <label>Тариф</label>
    <select id="plan">
      <option value="starter">Starter — 5 $ за пользователя</option>
      <option value="pro">Pro — 12 $ за пользователя</option>
      <option value="enterprise">Enterprise — 25 $ за пользователя</option>
    </select>
  </div>
  <div class="calc-result">
    Итого: <span id="total">$50</span> в месяц
  </div>
</div>

<script>
  const prices = { starter: 5, pro: 12, enterprise: 25 };
  const usersInput = document.getElementById('users');
  const planSelect = document.getElementById('plan');

  function updatePrice() {
    const users = parseInt(usersInput.value);
    const price = prices[planSelect.value];
    document.getElementById('users-count').textContent = users;
    document.getElementById('total').textContent = '$' + (users * price).toLocaleString();
  }

  usersInput.addEventListener('input', updatePrice);
  planSelect.addEventListener('change', updatePrice);
</script>
```

### API Tilda

API доступно только на тарифе Business, ключи лежат в «Настройки сайта → Экспорт → API-интеграция». Каждый запрос — это GET с обоими ключами в строке запроса, поэтому вызывай API с сервера и никогда из кода в браузере.

```typescript
// api/tilda.ts — читаем проекты и страницы через API Tilda
const TILDA_PUBLIC_KEY = process.env.TILDA_PUBLIC_KEY;
const TILDA_SECRET_KEY = process.env.TILDA_SECRET_KEY;
const BASE_URL = "https://api.tildacdn.info/v1";

// Все проекты
async function getProjects() {
  const res = await fetch(
    `${BASE_URL}/getprojectslist/?publickey=${TILDA_PUBLIC_KEY}&secretkey=${TILDA_SECRET_KEY}`
  );
  return res.json(); // { status: "FOUND", result: [{ id, title, ... }] }
}

// Все страницы проекта
async function getPages(projectId: number) {
  const res = await fetch(
    `${BASE_URL}/getpageslist/?publickey=${TILDA_PUBLIC_KEY}&secretkey=${TILDA_SECRET_KEY}&projectid=${projectId}`
  );
  return res.json();
}

// Настройки проекта: пути экспорта, заданные в «Настройки сайта → Экспорт»
// (export_imgpath, export_jspath, export_csspath), и изображения, общие для всех страниц
async function getProjectInfo(projectId: number) {
  const res = await fetch(
    `${BASE_URL}/getprojectinfo/?publickey=${TILDA_PUBLIC_KEY}&secretkey=${TILDA_SECRET_KEY}&projectid=${projectId}`
  );
  return (await res.json()).result;
}

// Экспорт страницы на свой хостинг. getpagefullexport возвращает полный HTML-документ
// с переписанными на пути экспорта ссылками и файлы для копирования в виде пар { from, to }.
// (getpagefull возвращает тот же документ, но со ссылками на ресурсы, размещённые у Tilda;
// getpage и getpageexport возвращают только HTML тела — для вставки в свой шаблон.)
async function exportPage(pageId: number, project: any, outDir: string) {
  const { mkdir, writeFile } = await import("node:fs/promises");
  const res = await fetch(
    `${BASE_URL}/getpagefullexport/?publickey=${TILDA_PUBLIC_KEY}&secretkey=${TILDA_SECRET_KEY}&pageid=${pageId}`
  );
  const page = (await res.json()).result;   // { id, title, filename: "page1001.html", html, images, ... }
  await writeFile(`${outDir}/${page.filename}`, page.html);
  const groups = [[page.images, project.export_imgpath], [page.js, project.export_jspath], [page.css, project.export_csspath]];
  for (const [files, dir] of groups) {
    await mkdir(`${outDir}/${dir}`, { recursive: true });
    for (const file of files ?? []) {
      const body = Buffer.from(await (await fetch(file.from)).arrayBuffer());
      await writeFile(`${outDir}/${dir}/${file.to}`, body);
    }
  }
}
```

`project.images` копируй так же; `getprojectinfo` с параметром `&webconfig=htaccess` (или `nginx`) дополнительно вернёт правила для сервера. Чтобы узнавать о переопубликации страницы, задай URL вебхука в той же панели API-интеграции: Tilda пришлёт GET с полями `pageid`, `projectid`, `published` и `publickey`, ждёт в ответ тело `ok` в течение 5 секунд и повторит запрос дважды.

### Обработка форм и вебхуки

```typescript
// webhook/tilda-form.ts — принимаем отправки форм Tilda
/**
 * Настройка в Tilda: «Настройки сайта → Формы → Вебхук» (URL скрипта должен быть HTTPS),
 * затем отметь WEBHOOK в панели «Контент» каждого блока с формой и переопубликуй страницу.
 * Tilda отправляет POST с form-encoded телом при каждой отправке и ждёт ответ 5 секунд;
 * после таймаута повторяет запрос дважды с интервалом в минуту, поэтому обработчик должен быть быстрым.
 */
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID;

export async function handleTildaForm(req: Request) {
  const data = Object.fromEntries(await req.formData());
  // data: { Name: "Кай Чэнь", Email: "kai@riverside.io", Phone: "+14155550142",
  //         tranid: "467251:8442970", formid: "form48844953" }  — ключи равны именам переменных полей

  // Сохраняем в CRM
  await fetch("https://api.riverside.io/leads", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: data.Name, email: data.Email, phone: data.Phone, source: "tilda-landing",
    }),
  });

  // Уведомляем отдел продаж в Telegram
  await fetch(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: TELEGRAM_CHAT_ID,
      text: `Новая заявка\nИмя: ${data.Name}\nEmail: ${data.Email}\nТелефон: ${data.Phone}`,
    }),
  });

  return new Response("OK");
}
```

### Электронная коммерция (магазин Tilda)

- Блоки магазина лежат в категории «Магазин» библиотеки блоков, товары — в каталоге товаров.
- Корзина — блок ST100 «Корзина с формой заказа». На многостраничном сайте ставь её в шапку или подвал, чтобы она была на каждой странице; значок корзины появляется только после добавления товара.
- Платёжные и доставочные сервисы можно проверить только на опубликованной странице, не в предпросмотре.
- Заказы приходят на твой бэкенд через тот же вебхук форм; в настройках вебхука включи «передавать данные о товарах массивами» (и `externalid`), чтобы получать заказанные товары в структурированном виде.
- Продажи, заказы и конверсия — в «Настройки сайта → Аналитика → Статистика сайта → Онлайн-магазин».
- Каталог товаров не входит в экспорт кода; он продолжает работать только при активной подписке.

### SEO и аналитика

Заголовок страницы, описание и превью для соцсетей задаются отдельно для каждой страницы в настройках страницы (вкладки «Основное», «SEO» и «Социальные сети»). Google Analytics и Google Tag Manager не требуют кода: укажи идентификатор тега Google (GA4) или идентификатор контейнера GTM в «Настройки сайта → Аналитика» (для GA4 дополнительно отметь «Включить gtag.js» в настройках счётчика) и опубликуй все страницы. Тогда Tilda передаёт отправки форм как виртуальные просмотры страниц вида `/tilda/form31751802/submitted`, а клики по кнопкам и открытия попапов — если это включено в настройках блока. Используй только один способ — встроенный счётчик, GTM или вставленный фрагмент, — иначе визиты посчитаются дважды. Любой другой тег или фрагмент ниже со своим Measurement ID ставь в «Настройки сайта → Ещё → HTML-код для вставки внутрь head».

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-7PK2D9QLMS"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){ dataLayer.push(arguments); }
  gtag('js', new Date());
  gtag('config', 'G-7PK2D9QLMS');
</script>
```

## Примеры

### Пример 1: маркетинговый лендинг

**Запрос пользователя:** «Сделай лендинг для SaaS-продукта: первый экран, преимущества, тарифы, FAQ и форма обратной связи — текст и картинки сотрудники должны менять сами».

Агент соберёт страницу из блоков Tilda, настроит вебхуки форм, добавит свой CSS для соответствия брендбуку и подключит аналитику.

### Пример 2: свои интерактивные элементы на Tilda

**Запрос пользователя:** «Добавь на сайт калькулятор стоимости и интерактивную таблицу сравнения товаров».

Агент сделает макеты в Zero Block со своим HTML/JS для калькулятора и таблицы сравнения и оформит их в стиле темы Tilda.

### Пример 3: подключение форм Tilda к CRM

**Запрос пользователя:** «Отправляй каждую заявку из формы в нашу CRM и уведомляй отдел продаж в Telegram».

Агент настроит вебхуки Tilda, сделает серверную функцию приёма заявок и пересылки данных в CRM и Telegram.

## Рекомендации

- **Блоки для структуры, Zero Block для нестандартного** — готовые блоки дают скорость, Zero Block — полный контроль.
- **Свой код** — код для head (CSS, метатеги) в «Настройки сайта → Ещё»; HTML/JS для тела — в блок T123 или HTML-элемент Zero Block.
- **У форм есть встроенные вебхуки** — отправляй заявки на любой HTTPS-URL, отвечающий за 5 секунд.
- **API Tilda только для чтения** — оно перечисляет и экспортирует проекты и страницы, но не создаёт и не редактирует их. Только тариф Business, 150 запросов в час; синхронизируй страницы на свой сервер, а не вызывай API при каждом визите.
- **SEO настраивается постранично** — заголовок, описание и OG-теги в настройках страницы.
- **Свой домен** — направь DNS на Tilda, затем включи бесплатный сертификат Let's Encrypt в «Настройки сайта → SEO → Настройки HTTPS».
- **Электронная коммерция встроена** — каталог товаров, корзина, оформление заказа, платежи.
- **Адаптивность по умолчанию** — блоки подстраиваются, но контрольные точки надо проверять и править.
- **Сотрудники правят всё сами** — текст, изображения, блоки и порядок страниц через визуальный редактор.
- **Экспорт для своего хостинга** — только тариф Business (архив в «Настройки сайта → Экспорт» или через API); экспортированному сайту нужен собственный SSL-сертификат, он должен сохранять подпись «Made on Tilda», а формы и каталог по-прежнему требуют активной подписки.
- **Не переопределяй критичные классы Tilda** — добавляй к своему CSS собственный префикс.
- **Google Tag Manager** — для сложной аналитики используй GTM, а не инлайновые скрипты.
