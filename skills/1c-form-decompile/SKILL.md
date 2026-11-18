---
name: 1c-form-decompile
description: Декомпиляция управляемой формы 1С (Form.xml) в JSON-черновик в формате form-compile. Используй для scaffold новой формы по образцу или структурного рефакторинга. Не для точечных правок
disable-model-invocation: true
allowed-tools: "run_terminal_command read_file create_new_file"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
---

# /1c-form-decompile — JSON-черновик из Form.xml управляемой формы

Читает Form.xml и эмитит компактный JSON в формате `1c-form-compile`. **Результат — черновик**, а не обратимое представление: см. раздел «Что получаешь».

## Когда использовать

- **Scaffold новой формы по образцу** — взять существующую форму, получить JSON, поправить и скомпилировать в новую.
- **Структурный рефакторинг** — перебрать дерево элементов, реквизиты, команды.

## Когда **не** использовать

- **Точечные правки готовой формы** (добавить элемент, реквизит, команду; переставить элемент, перенести в другую группу, поменять заголовок или видимость, удалить) → `/1c-form-edit`. Цикл «декомпиляция → правка JSON → компиляция» переписывает форму целиком, может терять непокрытые конструкции и даёт большой diff. `/1c-form-edit` правит адресно.

## Параметры

| Параметр | Описание |
|----------|----------|
| `FormPath` | Путь к Form.xml (обязательный) |
| `OutputPath` | Путь к выходному JSON. Если не задан — JSON в stdout |

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/form-decompile.ps1" -FormPath "<Form.xml>" -OutputPath "<out.json>"
```

## Что получаешь

JSON-черновик в формате `/1c-form-compile` — **не полное обратимое представление**: раундтрип `xml → json → xml` не гарантируется, часть конструкций DSL не покрывает и **теряет молча**.

Критичные конструкции (`ConditionalAppearance` со scope, design-time диаграммы/планировщики на реквизите, неизвестный тип элемента, не-Form root) → скрипт падает с ненулевым кодом и сообщением в stderr; для правок такой формы — `/1c-form-edit`.

## Workflow

1. `/1c-form-decompile <Form.xml> -OutputPath draft.json` — получить черновик.
2. Поправить JSON под задачу.
3. `/1c-form-compile -JsonPath draft.json -OutputPath new/Form.xml` — собрать обратно.
4. `/1c-form-validate` + `/1c-form-info` — проверить результат.
