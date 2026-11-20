# PDF

Документация: <https://pypdf.readthedocs.io/>, <https://pdfplumber.readthedocs.io/>, <https://pymupdf.readthedocs.io/>.

PDF описывает внешний вид страницы, а не структуру документа.
Извлечение текста и таблиц всегда приблизительное, а редактирование ограничено.

## Чтение и извлечение

| Инструмент          | Сильные стороны                                          | Ограничения                     |
|---------------------|----------------------------------------------------------|---------------------------------|
| `pypdf`             | Объединение, разделение, поворот, метаданные, шифрование | Простое извлечение текста       |
| `pdfplumber`        | Текст с координатами, таблицы, линии                     | Медленнее на больших файлах     |
| `PyMuPDF`           | Быстрое извлечение, рендеринг, аннотации, редактирование | Лицензия AGPL или коммерческая  |
| `pdfminer.six`      | Гибкий разбор структуры                                  | Сложный API                     |
| `Camelot`, `tabula` | Таблицы                                                  | Зависимости и качество эвристик |

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
print(len(reader.pages))
print(reader.metadata)

for page in reader.pages:
    print(page.extract_text())
```

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        print(page.extract_text())
        for table in page.extract_tables():
            print(table)
```

`pdfplumber` лучше работает с таблицами, у которых есть линии.
Если линии отсутствуют, попробуй настройки `table_settings` или `Camelot`.

## Порядок текста

PDF не хранит абзацы и колонки так, как DOCX.
Текст может извлекаться в порядке отрисовки, а не чтения.

- Проверяй результат на многоколоночных документах.
- Для сложных макетов используй координаты (`pdfplumber`) и сортировку по `top`, `x0`.
- Не рассчитывай, что пробелы и переносы сохранятся идеально.
- Для сканов сначала выполни OCR.

## OCR

```bash
ocrmypdf --language rus+eng --deskew --clean input.pdf output.pdf
```

- `ocrmypdf` добавляет текстовый слой, сохраняя изображение страницы.
- `Tesseract` можно использовать напрямую для отдельных изображений.
- Качество OCR зависит от разрешения, угла и языка.
- Для русского языка нужен пакет `tesseract-ocr-rus`.
- Проверяй результат: OCR часто путает цифры и похожие буквы.

## Создание PDF

| Инструмент     | Когда выбирать                                 |
|----------------|------------------------------------------------|
| `ReportLab`    | Полный контроль над вёрсткой, таблицы, графики |
| `WeasyPrint`   | HTML и CSS в PDF, удобно для отчётов           |
| `pdf-lib`      | Создание и правка PDF в Node.js                |
| Puppeteer      | Печать HTML-страницы в PDF                     |
| LibreOffice    | Конвертация DOCX, XLSX, PPTX в PDF             |
| Pandoc + LaTeX | Документы с формулами и сложной типографикой   |

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

pdfmetrics.registerFont(TTFont("DejaVu", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))

pdf = canvas.Canvas("report.pdf", pagesize=A4)
pdf.setFont("DejaVu", 12)
pdf.drawString(40, 800, "Отчёт за ноябрь 2026")
pdf.showPage()
pdf.save()
```

Для кириллицы нужен шрифт с поддержкой Unicode. Стандартные шрифты ReportLab не содержат русских букв.

## Объединение и разделение

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages[:3]:
    writer.add_page(page)

with open("first-three.pdf", "wb") as output:
    writer.write(output)
```

- `append` объединяет целые документы.
- `add_page` добавляет отдельную страницу.
- Для разделения создавай отдельный writer на каждый диапазон.
- Проверяй закладки и метаданные после объединения.

## Поворот, обрезка и метаданные

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("document.pdf")
writer = PdfWriter()
page = reader.pages[0]
page.rotate(90)
writer.add_page(page)
writer.add_metadata({"/Title": "Отчёт", "/Author": "Компания"})

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

Обрезка видимой области не удаляет содержимое за её пределами.
Если нужно удалить данные, используй редактирование (redaction), а не обрезку.

## Редактирование и удаление данных

- `PyMuPDF` умеет добавлять аннотации, закрашивать области и удалять текст.
- `pypdf` умеет шифровать и расшифровывать документы с известным паролем.
- Для настоящего удаления конфиденциальных данных используй redaction, а не чёрный прямоугольник.
- После redaction проверь текстовый слой: данные не должны извлекаться.

## Подписи

- `pyHanko` подписывает PDF сертификатом и проверяет подписи.
- Для квалифицированной электронной подписи в России нужны сертификаты и средства криптозащиты, а не только библиотека.
- Не подписывай документ, содержимое которого не проверил.
- После подписи документ нельзя менять без потери подписи.

```python
from pyhanko.sign import signers
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

signer = signers.SimpleSigner.load("key.pem", "cert.pem")
with open("document.pdf", "rb") as source:
    writer = IncrementalPdfFileWriter(source)
    signers.sign_pdf(writer, signers.PdfSignatureMetadata(field_name="Signature1"), signer=signer)
```

## Безопасность

- PDF может содержать JavaScript, вложения, формы и внешние ссылки.
- Не открывай недоверенные PDF в браузере с включённым JavaScript без необходимости.
- Проверяй, не является ли файл полиглотом (PDF + другой формат).
- Ограничивай размер и число страниц при автоматической обработке.
- Не выполняй команды из текста PDF.

## Ограничения

- PDF не предназначен для редактирования как DOCX.
- Конвертация PDF в DOCX не восстанавливает исходную структуру и стили.
- Извлечение таблиц без линий требует эвристик и ручной проверки.
- Шрифты могут быть подмножествами без полного набора символов.
- Защищённые PDF могут запрещать извлечение текста и печать.

## Проверка результата

1. Открой PDF в разных просмотрщиках.
2. Проверь число страниц, порядок и ориентацию.
3. Проверь текст, таблицы и изображения.
4. Проверь метаданные и закладки.
5. Для OCR — выборочно сверь текст с изображением.
6. Для redaction — попробуй извлечь текст и убедись, что данных нет.

## Частые ошибки

| Симптом                     | Причина                               | Решение                                          |
|-----------------------------|---------------------------------------|--------------------------------------------------|
| Пустой текст                | Скан без OCR                          | Выполни OCR                                      |
| Текст в неверном порядке    | Колонки и абсолютное позиционирование | Сортируй по координатам                          |
| Кракозябры                  | Нет шрифта или неверная кодировка     | Используй Unicode-шрифт                          |
| Таблица не извлекается      | Нет линий                             | Настрой `table_settings` или используй `Camelot` |
| Данные видны после удаления | Обрезка вместо redaction              | Используй redaction                              |
| Подпись недействительна     | Документ изменён после подписи        | Подписывай последним шагом                       |
| PDF не открывается          | Повреждён или зашифрован              | Проверь пароль и целостность                     |
