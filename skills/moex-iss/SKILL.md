---
name: moex-iss
description: "Механика MOEX ISS и ISS+ для прямых REST-запросов: публичный iss.moex.com, авторизованный apim.moex.com, форматы вывода, iss.only, iss.json, пагинация через start по числу возвращённых строк, нормализация блоков ответа, маршруты поиска и истории, календари, группы режимов и понятия websocket и STOMP. Используй при работе с Московской биржей напрямую, без готового клиента."
license: MIT
metadata:
  author: moexalgo
  source: https://github.com/moexalgo/algopack-skills
---

# MOEX ISS

## Обзор

Этот навык — про общую механику MOEX ISS и ISS+, не привязанную к конкретному набору данных ALGOPACK. Для SuperCandles, FUTOI, HI2, Mega Alerts и примеров рыночных данных предпочитай навыки под конкретный набор.

## Основной порядок работы

1. Выбери хост: `https://iss.moex.com/iss` для публичного ISS или `https://apim.moex.com/iss` для авторизованных маршрутов в реальном времени, полностью актуальных или доступных только подписчикам.
2. Выбери суффикс формата: `.json`, `.csv`, `.xml` или `.html`.
3. Используй `iss.only` и фильтры по столбцам, чтобы ответ оставался маленьким.
4. Приведи массивы `columns` и `data` из ISS к строкам, прежде чем фильтровать, соединять, писать таблицы или строить графики.
5. Пагинируй через `start`, пока целевой блок не вернёт пустой результат, сдвигая смещение на число возвращённых строк.
6. Подбирай вывод под задачу: таблицы CSV или JSON для передачи, простые HTML-графики для браузера, Matplotlib или pandas для ноутбука и скрипта, а внутри приложения — уже принятый там стек графиков.

## Быстрый старт

```bash
curl -L "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?iss.only=marketdata&marketdata.columns=SECID,LAST,UPDATETIME"
```

С авторизацией:

```bash
curl -L "https://apim.moex.com/iss/datashop/algopack/eq/tradestats/SBER.json?from=2025-01-01&till=2025-01-31&start=0" \
  -H "Authorization: Bearer ${APIKEY}"
```

## Справочники

Читай по мере необходимости:

- `references/rest-iss.md` — шаблоны REST, разбор ответов, пагинация, поиск, история и параметры запросов.
- `references/calendars.md` — торговые календари, сессии, приостановки и эндпоинты расчётов.
- `references/issplus.md` — понятия websocket и STOMP в ISS+ и облик локального бета-клиента.

## Границы

Никогда не раскрывай реальные ключи в адресах, примерах кода, логах, скриншотах или ответах. Используй переменные окружения или заглушки.
