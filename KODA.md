# KodaSkills — репозиторий агентских навыков

## Обзор проекта

**KodaSkills** — это официальная коллекция переиспользуемых навыков (skills) для AI-ассистента [Koda](https://kodacode.ru).
Каждый навык представляет собой Markdown-файл (`SKILL.md`) с YAML frontmatter, содержащий инструкции для модели на конкретную тему или задачу.

Репозиторий совмещает в себе:
- **Библиотеку навыков** — директория `skills/` с Markdown-документами.
- **Генератор метаданных** — Python-скрипт `generator.py`, который собирает метаданные из всех `SKILL.md` и формирует `metadata.json`.
- **CI/CD автоматизацию** — GitHub Actions workflow для автоматического обновления `metadata.json` при изменениях.

## Технологии и архитектура

- **Язык генератора:** Python 3.11+
- **Зависимости:** `pyyaml>=6.0`
- **Формат навыков:** Markdown с YAML frontmatter
- **Схема метаданных:** JSON Schema (`metadata-schema.json`)
- **Автоматизация:** GitHub Actions, Makefile
- **Форматирование:** EditorConfig (`.editorconfig`)

### Структура репозитория

```
.
├── skills/                          # Директория с навыками
│   └── koda-*/SKILL.md
├── generator.py                     # Скрипт генерации metadata.json
├── metadata.json                    # Автоматически сгенерированные метаданные
├── metadata-schema.json             # JSON Schema для валидации metadata.json
├── requirements.txt                 # Python-зависимости
├── Makefile                         # Команды сборки и обслуживания
├── README.md                        # Пользовательская документация
├── LICENSE                          # Лицензия MIT
├── .editorconfig                    # Настройки форматирования
├── .github/workflows/               # CI/CD
│   └── update-metadata.yml          # Workflow автообновления метаданных
└── media/                           # Медиа-ресурсы (логотипы и т.п.)
```

### Формат SKILL.md

Каждый навык содержит YAML frontmatter с обязательными полями:

```yaml
---
name: skill-name              # Идентификатор в kebab-case, 1–64 символов
description: "Описание"       # Когда срабатывает навык, 1–1024 символа
license: MIT                  # Лицензия (опционально)
metadata:
  author: koda                # Автор
  version: "1.0.0"            # Версия
---
```

## Сборка и запуск

### Подготовка окружения

```bash
make install
```

Создаёт виртуальное окружение `.venv`, обновляет `pip` и устанавливает зависимости из `requirements.txt`.

### Генерация metadata.json

```bash
make metadata
```

Запускает `generator.py`, который:
1. Рекурсивно находит все `skills/*/SKILL.md` (только первый уровень вложенности).
2. Парсит YAML frontmatter из каждого файла.
3. Формирует `metadata.json` со списком навыков, их версиями и URL.

### Очистка окружения

```bash
make clean
```

Удаляет виртуальное окружение `.venv`.

### Ручной запуск генератора

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generator.py
```

Переменная окружения `REPO_URL` позволяет переопределить URL репозитория (по умолчанию `https://github.com/XCode-NLP/KodaSkills`).

### CI/CD

При пуше в ветку `main` или слиянии Pull Request срабатывает workflow `.github/workflows/update-metadata.yml`:
1. Устанавливает Python 3.11 и зависимости.
2. Запускает `generator.py`.
3. Если `metadata.json` изменился, создаёт коммит от имени `github-actions[bot]` и пушит обратно.

## Правила разработки

### Добавление нового навыка

1. Создать директорию `skills/<имя-навыка>/`.
2. Добавить файл `SKILL.md` с корректным YAML frontmatter.
   - `name`: только строчные буквы, цифры и дефисы; без заглавных букв, без двойных дефисов, без дефисов в начале/конце.
   - `description`: чётко описывать, когда навык срабатывает.
3. Убедиться, что frontmatter валиден — `generator.py` пропускает файлы без обязательных полей `name` и `description`.
4. После пуша в `main` `metadata.json` обновится автоматически.

### Форматирование

- `.editorconfig` требует:
  - `charset = utf-8`
  - `end_of_line = lf`
  - `insert_final_newline = true`
  - `indent_style = space`, `indent_size = 4` (для общих файлов)
  - `indent_size = 2` (для `*.yml`, `*.yaml`)
  - `indent_style = tab` (для `Makefile`)

### Тестирование

Явных тестов в репозитории нет. Корректность работы проверяется запуском `make metadata` и валидацией полученного `metadata.json` по схеме `metadata-schema.json`.

## Использование навыков

Навыки предназначены для установки в продукты Koda:

| Продукт                   | Путь установки                          |
| ------------------------- | --------------------------------------- |
| Плагин (VSCode/JetBrains) | `.koda/skills/<имя_навыка>/SKILL.md`    |
| CLI                       | `.kodacli/skills/<имя_навыка>/SKILL.md` |
| Универсальный             | `.agents/skills/<имя_навыка>/SKILL.md`  |
| Глобально (все проекты)   | `~/.koda/skills/<имя_навыка>/SKILL.md`  |

После установки навык необходимо активировать через интерфейс продукта (панель «Навыки» в режиме Агент или команды `/skill enable` / `/skill reload` в CLI).

## Ключевые файлы

| Файл                                    | Назначение                                                     |
| --------------------------------------- | -------------------------------------------------------------- |
| `generator.py`                          | Python-скрипт парсинга frontmatter и генерации `metadata.json` |
| `metadata.json`                         | Автогенерируемый индекс всех навыков с URL для установки       |
| `metadata-schema.json`                  | JSON Schema для валидации структуры `metadata.json`            |
| `Makefile`                              | Команды: `install`, `metadata`, `clean`, `help`                |
| `README.md`                             | Пользовательская документация по установке и формату навыков   |
| `.github/workflows/update-metadata.yml` | CI workflow для автокоммита обновлённого `metadata.json`       |
