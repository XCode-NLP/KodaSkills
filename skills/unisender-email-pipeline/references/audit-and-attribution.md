# Аудит и атрибуция

## Содержание

1. Источники истины
2. Статусы данных
3. Окна и сопоставимость
4. Нормализованный контракт
5. amoCRM
6. Формулы
7. Карта ссылок
8. Сила выводов

## 1. Источники истины

| Уровень | Источник | Использование |
|---|---|---|
| Отправка | UniSender | sent, delivered, opens, clickers, отписки, жалобы |
| Карта письма | UniSender UI/Browser или MCP | клики по размещениям |
| Поведение после клика | Яндекс Метрика | визиты, вовлечённость, цели |
| Бизнес-результат | amoCRM | заявки, квалификация, сделки, продажи, выручка |

Matomo считать только необязательным источником сверки. Не требовать его для полного отчёта, если Метрика и amoCRM покрывают согласованную воронку.

## 2. Статусы данных

Для каждого источника использовать:

- `complete` — обязательные строки и поля реально получены и проверены;
- `partial` — часть данных доступна, но вывод ограничен;
- `missing` — источник отсутствует или не ответил;
- `not_applicable` — допустимо только там, где источник действительно не нужен.

Итог `complete` разрешён, если для выбранного охвата полны:

- UniSender;
- link stats;
- UTM;
- Метрика;
- amoCRM;
- resend dedup для resend, если resend входит в вывод.

Browser не превращает UI-данные в API. В ручном отчёте указывать, что link map получена из интерфейса, и дату просмотра.

## 3. Окна и сопоставимость

- D+1 — ранний сигнал, не включать в финальный baseline.
- D+3 — оперативный provisional.
- D+7 — основной финальный срез.
- D+14 — дополнительный срез для доказанного длинного цикла сделки.

Primary включать в baseline, если совпадают окно, назначение, аудитория и методика. Тестовые и технические кампании исключать. Аномалии не удалять молча.

Resend анализировать отдельно. Не считать его чистым A/B-тестом темы. Для пары показывать инкрементальные открытия, клики, визиты, заявки, продажи, отписки и жалобы. Без дедупликации не складывать уникальные показатели original и resend.

Уровни уверенности:

- 1 кампания — наблюдение;
- 3+ сопоставимых повторения — вероятный паттерн;
- 8–10 кампаний — диагностический baseline;
- 25–30 — рабочая база;
- причинный вывод — контролируемый тест или сильный квазиэксперимент.

## 4. Нормализованный контракт

Синтетический пример контракта (все значения вымышлены):

```json
{
  "as_of": "2026-01-25T09:00:00+07:00",
  "maturity_days": 7,
  "required_sources": [
    "unisender",
    "link_stats",
    "utm",
    "web_analytics",
    "crm",
    "resend_dedup"
  ],
  "campaigns": [
    {
      "campaign_id": "123",
      "subject": "Тема",
      "campaign_type": "primary",
      "sent_at": "2026-01-17T10:00:00+07:00",
      "observation_window": "D+7",
      "comparable": true,
      "utm_campaign": "digest_2026_01_17_sample",
      "web_analytics_source": "metrika",
      "crm_source": "amoCRM",
      "source_status": {
        "unisender": "complete",
        "link_stats": "complete",
        "utm": "complete",
        "web_analytics": "complete",
        "web_analytics_comparison": "missing",
        "crm": "complete",
        "resend_dedup": "not_applicable"
      },
      "link_unique_clickers_status": "unavailable",
      "sent": 100,
      "delivered": 90,
      "unique_opens": 30,
      "unique_clickers": 9,
      "unsubscribes": 2,
      "complaints": 0,
      "sessions": 8,
      "engaged_sessions": 5,
      "leads": 2,
      "qualified_leads": 1,
      "sales": 1,
      "revenue": 1000,
      "expected_link_count": 1,
      "link_map_total_clicks": 10,
      "links": [
        {
          "utm_content": "article_01_button",
          "url": "https://example.com/news/synthetic-material/?utm_source=unisender&utm_medium=email&utm_campaign=digest_2026_01_17_sample&utm_content=article_01_button",
          "element": "button",
          "position": "article_01",
          "all_clicks": 10,
          "unique_clickers": null,
          "sessions": 8,
          "engaged_sessions": 5,
          "leads": 2,
          "qualified_leads": 1,
          "sales": 1,
          "revenue": 1000
        }
      ]
    }
  ]
}
```

Для совместимости со скриптом сохранять поле `web_analytics_comparison` даже при отсутствии Matomo, но не включать его в `required_sources`.

Неизвестные значения задавать `null`, не нулём. Снапшот идентифицировать по `campaign_id + observation_window + as_of`.

## 5. amoCRM

До первой атрибуции обнаружить через MCP:

- реальные названия/ID полей `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`;
- воронки и статусы новой, квалифицированной, успешной и нецелевой заявки;
- поле суммы и валюту;
- связь лида/сделки с контактом;
- правила дублей;
- часовой пояс дат.

Считать точной кампанийной атрибуцией совпадение `utm_source=unisender`, `utm_medium=email`, `utm_campaign`. Срез по `utm_content` считать полным только при фактическом заполнении поля.

Если UTM отсутствуют:

- не присваивать заявку письму только по близкой дате;
- разрешать временное сопоставление только как явно помеченную гипотезу;
- ставить `crm=partial` или `missing`;
- указать, какие формы/интеграции должны передавать UTM.

CRM — источник истины для статуса и выручки. Метрика не заменяет CRM-заявки, а CRM не заменяет визиты.

## 6. Формулы

- `delivery_rate = delivered / sent`
- `open_rate = unique_opens / delivered`
- `ctr = unique_clickers / delivered`
- `ctor = unique_clickers / unique_opens`
- `unsubscribe_rate = unsubscribes / delivered`
- `complaint_rate = complaints / delivered`
- `sessions_per_clicker = sessions / unique_clickers`
- `engaged_rate = engaged_sessions / sessions`
- `lead_cr = leads / sessions`
- `leads_per_1000_delivered = leads / delivered × 1000`
- `sales_cr = sales / leads`
- `revenue_per_1000_delivered = revenue / delivered × 1000`

Показывать знаменатель. Для baseline рассчитывать weighted rate по суммам и медиану campaign-level rate.

Если значение поля отсутствует хотя бы у одной кампании выбранного baseline,
агрегат этого поля неизвестен (null), а зависимый weighted rate не рассчитывается.
Не делить сумму частично доступных заявок/выручки на полный объём доставок/визитов.
Медиану campaign-level rate можно считать по доступным парам, явно показывая охват.

## 7. Карта ссылок

Для каждого размещения разделять:

1. all clicks;
2. unique clickers, если доступны;
3. визиты;
4. вовлечённые визиты;
5. цели;
6. заявки;
7. квалифицированные заявки;
8. продажи и выручку.

Один URL в разных элементах должен иметь разные `utm_content`. Без этого запрещать вывод о сравнительной эффективности изображения, заголовка и кнопки.

Расхождение кликов и визитов нормально из-за повторов, ботов, блокировщиков, редиректов и согласия на аналитику. Объяснять динамику, не складывать величины.

## 8. Сила выводов

Всегда разделять:

- факты;
- вероятные драйверы;
- гипотезы;
- рекомендации.

Для следующего письма давать не более трёх приоритетов и один главный тест. У каждого теста указывать механизм, целевую метрику, guardrail, критерий успеха и окно.
