# XLSX

Документация: <https://openpyxl.readthedocs.io/>, <https://xlsxwriter.readthedocs.io/>, <https://exceljs.readthedocs.io/>.

XLSX — это ZIP-архив с XML-файлами Office Open XML.
Электронная таблица хранит не только значения, но и формулы, стили, связи и кэш вычислений.

## Что внутри

| Путь                       | Назначение                      |
|----------------------------|---------------------------------|
| `xl/workbook.xml`          | Список листов и настройки книги |
| `xl/worksheets/sheet*.xml` | Данные листов                   |
| `xl/sharedStrings.xml`     | Общие строки                    |
| `xl/styles.xml`            | Стили, шрифты, заливки, границы |
| `xl/calcChain.xml`         | Цепочка вычислений              |
| `xl/charts/`               | Диаграммы                       |
| `xl/media/`                | Изображения                     |

Не редактируй эти файлы вручную: легко потерять стили и связи.

## openpyxl

```bash
pip install openpyxl
```

Создание книги:

```python
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

workbook = Workbook()
sheet = workbook.active
sheet.title = "Смета"

sheet.append(["Наименование", "Количество", "Цена", "Сумма"])
sheet.append(["Болты", 100, 12.5, "=B2*C2"])
sheet.append(["Гайки", 200, 8.0, "=B3*C3"])

header_fill = PatternFill("solid", fgColor="DDEBF7")
thin = Side(style="thin", color="999999")
for cell in sheet[1]:
    cell.font = Font(bold=True)
    cell.fill = header_fill
    cell.alignment = Alignment(horizontal="center")
    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)

for column in range(1, 5):
    sheet.column_dimensions[get_column_letter(column)].width = 18

sheet.freeze_panes = "A2"
sheet.auto_filter.ref = "A1:D3"
workbook.save("estimate.xlsx")
```

Чтение:

```python
from openpyxl import load_workbook

workbook = load_workbook("estimate.xlsx", data_only=False)
sheet = workbook["Смета"]

for row in sheet.iter_rows(min_row=2, values_only=True):
    print(row)
```

`data_only=False` возвращает формулы, `data_only=True` — закэшированные значения.
Если файл создан программно и не открывался в Excel, кэша может не быть и `data_only=True` вернёт `None`.

## Формулы

- `openpyxl` сохраняет формулу как строку, начинающуюся с `=`.
- Формулы не пересчитываются при сохранении.
- Для пересчёта открой файл в Excel или выполни конвертацию в LibreOffice.
- При чтении проверяй, что формула и значение — разные вещи.
- Не подставляй пользовательский ввод в формулу без экранирования: это риск формул-инъекций (`=`, `+`, `-`, `@` в начале строки).

Пересчёт через LibreOffice:

```bash
soffice --headless --convert-to xlsx --outdir recalculated estimate.xlsx
```

## Стили и оформление

- Стили применяй к ячейкам, а не к диапазону целиком.
- Ширину столбцов задавай через `column_dimensions`.
- Высоту строк — через `row_dimensions`.
- Объединение ячеек: `sheet.merge_cells("A1:D1")`.
- Условное форматирование: `openpyxl.formatting.rule`.
- Диаграммы: `openpyxl.chart`.
- Закрепление областей: `freeze_panes`.
- Автофильтр: `auto_filter.ref`.
- Печать: `sheet.page_setup`, `sheet.print_area`, `sheet.print_title_rows`.

## xlsxwriter

`xlsxwriter` умеет только запись, зато даёт больше возможностей для оформления.

```python
import xlsxwriter

workbook = xlsxwriter.Workbook("report.xlsx")
sheet = workbook.add_worksheet("Отчёт")

header = workbook.add_format({"bold": True, "bg_color": "#DDEBF7", "border": 1})
money = workbook.add_format({"num_format": "#,##0.00"})

sheet.write_row(0, 0, ["Наименование", "Сумма"], header)
sheet.write_row(1, 0, ["Болты", 1250.0], money)
sheet.set_column(0, 0, 30)
sheet.freeze_panes(1, 0)
workbook.close()
```

Не используй `xlsxwriter` для чтения или правки существующего файла: он этого не умеет.

## pandas

`pandas` удобен для анализа и преобразования данных.

```python
import pandas as pd

frame = pd.read_excel("input.xlsx", sheet_name="Данные")
summary = frame.groupby("Категория", as_index=False)["Сумма"].sum()
summary.to_excel("summary.xlsx", index=False)
```

Помни:

- `pandas` теряет стили, формулы, объединённые ячейки и диаграммы.
- `read_excel` по умолчанию читает только первый лист.
- Для больших файлов используй `usecols`, `dtype` и `nrows`.
- Для записи без стилей `to_excel` достаточно; для отчёта с оформлением — `openpyxl` или `xlsxwriter`.

## ExcelJS (Node.js)

```js
import ExcelJS from 'exceljs';

const workbook = new ExcelJS.Workbook();
const sheet = workbook.addWorksheet('Смета');

sheet.columns = [
  { header: 'Наименование', key: 'name', width: 30 },
  { header: 'Количество', key: 'quantity', width: 14 },
  { header: 'Цена', key: 'price', width: 14 },
  { header: 'Сумма', key: 'total', width: 16 },
];

sheet.addRow({ name: 'Болты', quantity: 100, price: 12.5, total: { formula: 'B2*C2' } });
sheet.getRow(1).font = { bold: true };
sheet.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFDDEBF7' } };

await workbook.xlsx.writeFile('estimate.xlsx');
```

Для больших файлов используй streaming reader/writer, а не загрузку всей книги в память.

## Большие файлы

- `openpyxl` не читает старый бинарный формат `.xls`: сначала конвертируй его в `.xlsx` через LibreOffice.
- XLSX поддерживает до 1 048 576 строк и 16 384 столбцов на лист.
- Для чтения больших файлов в `openpyxl` используй `read_only=True`.
- Для записи — `write_only=True` и `append`.
- Не держи в памяти все строки, если можно обрабатывать потоково.
- Для анализа больших данных сначала преобразуй в CSV или Parquet.

```python
from openpyxl import load_workbook

workbook = load_workbook("big.xlsx", read_only=True)
sheet = workbook["Данные"]
for row in sheet.iter_rows(values_only=True):
    process(row)
workbook.close()
```

## Безопасность

- Не открывай недоверенные файлы с макросами (`.xlsm`) без необходимости.
- Проверяй внешние ссылки и подключения к данным.
- Экранируй пользовательский ввод, который попадает в формулы.
- Не выполняй команды из ячеек.
- Ограничивай размер загружаемых файлов.

## Проверка результата

1. Открой файл в Excel или LibreOffice.
2. Проверь формулы и их значения.
3. Проверь ширину столбцов, перенос текста и печать.
4. Проверь, что стили и объединённые ячейки сохранились.
5. Проверь пустые строки и `None` в данных.

## Частые ошибки

| Симптом                            | Причина                                | Решение                                     |
|------------------------------------|----------------------------------------|---------------------------------------------|
| Формула есть, значения нет         | `openpyxl` не пересчитывает            | Открой в Excel или пересчитай в LibreOffice |
| `data_only=True` возвращает `None` | Нет кэша значений                      | Читай формулы или пересчитай файл           |
| Пропали стили                      | Использован `pandas.to_excel`          | Используй `openpyxl` или `xlsxwriter`       |
| Файл не открывается в Excel        | Некорректный XML или стиль             | Не редактируй XLSX вручную                  |
| Не хватает памяти                  | Большой файл загружен целиком          | `read_only` / `write_only`                  |
| Формула-инъекция                   | Пользовательский ввод начинается с `=` | Проверяй и экранируй ввод                   |
| Диаграмма исчезла                  | Библиотека не поддерживает диаграммы   | Проверь поддержку или используй шаблон      |
