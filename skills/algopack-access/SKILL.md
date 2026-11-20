---
name: algopack-access
description: "Доступ к ALGOPACK Московской биржи: бесплатные и платные API-ключи, подписка, авторизация ключом, подписка на продукты, настройка DataShop, токен Bearer, `session.TOKEN` в `.env` для moexalgo, заголовки прямого REST, бесплатный доступ с задержкой, ошибки 401, 403, 429, лимиты запросов и границы продукта."
license: MIT
metadata:
  author: moexalgo
  source: https://github.com/moexalgo/algopack-skills
---

# Доступ к ALGOPACK

## Обзор

Этот навык помогает получить авторизованный доступ к ALGOPACK и разобрать сбои подписки, ключа, прав и лимитов запросов, не раскрывая секреты.

## Основной порядок работы

1. Уточни, использует ли пользователь прямой REST и curl или библиотеку Python.
2. Объясни, что Data MOEX и DataShop дают бесплатный доступ по API-токену в тарифе «Стартовый», а `Promo` — платный доступ по подписке.
3. Скажи, что набор продуктов, задержка и покрытие полей зависят от тарифа аккаунта; данные в реальном времени или полностью актуальные требуют валидного токена и нужной подписки.
4. Для прямого REST показывай `Authorization: Bearer ${APIKEY}` к `https://apim.moex.com/iss`.
5. Для работы через библиотеку Python храни `APIKEY` в `.env`, вызывай `load_dotenv()`, затем ставь `session.TOKEN` из `os.environ["APIKEY"]`.
6. Сопоставь симптом с отсутствующим или истёкшим ключом, отсутствием подписки на продукт, неверным хостом, покрытием рынка и даты или ограничением частоты.
7. Называй границы продукта: ALGOPACK даёт рыночные данные и аналитику, но не выставляет заявки.

## Быстрый старт

Прямой REST:

```bash
curl -L "https://apim.moex.com/iss/datashop/algopack/eq/obstats.json?date=2025-01-10" \
  -H "Authorization: Bearer ${APIKEY}"
```

Библиотека Python:

```bash
python -m pip install "moexalgo[dataframe]" python-dotenv
```

```python
import os
from dotenv import load_dotenv
from moexalgo import session, Market

load_dotenv()
session.TOKEN = os.environ["APIKEY"]

eq = Market("EQ")
rows = eq.obstats(date="2025-01-10")
```

## Справочники

Читай `references/access-troubleshooting.md` про настройку подписки, уровни доступа, диагностику ошибок, лимиты и эскалацию.

## Границы

Не проси пользователей присылать реальные API-ключи. Не включай реальные ключи в код, историю команд, ноутбуки, логи или ответы.
