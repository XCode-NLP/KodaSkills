# Справочник по элементам LCL

Расширенный справочник по частым элементам LCL (Lazarus Component Library): в каком модуле
каждый живёт, какие свойства и события задают чаще всего, и пара готовых примеров, где блок `.lfm`
и соответствующее объявление в `.pas` показаны рядом.

## Содержание
- [Стандартные элементы (StdCtrls)](#стандартные-элементы-stdctrls)
- [Дополнительные элементы (ExtCtrls)](#дополнительные-элементы-extctrls)
- [Общие элементы (ComCtrls)](#общие-элементы-comctrls)
- [Диалоги](#диалоги)
- [Меню](#меню)
- [Таблицы](#таблицы)
- [Готовые примеры](#готовые-примеры)

## Стандартные элементы (StdCtrls)

| Элемент | Частые свойства | Частые события | Замечания |
|---|---|---|---|
| `TLabel` | `Caption`, `Font`, `Alignment`, `WordWrap` | — | Без пользовательского ввода; `ParentColor` и `ParentFont` обычно остаются `True`, если не задаёшь оформление. |
| `TButton` | `Caption`, `Default`, `Cancel`, `Enabled`, `ModalResult` | `OnClick` | `Default` и `Cancel` привязывают Enter и Esc на диалоге. `ModalResult` (например, `mrOK`) закрывает модальную форму без кода. |
| `TEdit` | `Text`, `MaxLength`, `PasswordChar`, `ReadOnly`, `NumbersOnly` | `OnChange`, `OnKeyPress`, `OnEditingDone` | `PasswordChar = '*'` для полей пароля. |
| `TMemo` | `Lines` (TStrings), `ScrollBars`, `ReadOnly`, `WordWrap` | `OnChange` | Из кода — `Lines.Add('...')` и `Lines.Text := '...'`; в `.lfm` начальное содержимое идёт блоком `Lines.Strings = (...)`, обычно проще оставить пустым и заполнить в `FormCreate`. |
| `TCheckBox` | `Caption`, `Checked`, `State` (для трёх состояний) | `OnChange` | |
| `TRadioButton` | `Caption`, `Checked`, `TabStop` | `OnChange` | Переключатели в одном родителе (например, в одном `TPanel` или `TGroupBox`) взаимоисключающи автоматически. |
| `TComboBox` | `Items` (TStrings), `Text`, `ItemIndex`, `Style` (`csDropDown` или `csDropDownList`) | `OnChange`, `OnSelect` | `csDropDownList` запрещает свободный ввод. |
| `TListBox` | `Items`, `ItemIndex`, `MultiSelect` | `OnClick`, `OnSelectionChange` | |
| `TGroupBox` | `Caption` | — | Обычный контейнер группировки с рамкой и заголовком; другие элементы кладутся внутрь. |
| `TScrollBox` | — | — | Прокручиваемый контейнер; клади элементы внутрь, когда содержимое может выйти за видимую область. |

## Дополнительные элементы (ExtCtrls)

| Элемент | Частые свойства | Частые события | Замечания |
|---|---|---|---|
| `TPanel` | `Caption`, `BevelOuter`, `Align`, `Color` | — | Очень частый контейнер раскладки; задавай `BevelOuter = bvNone` для невидимой панели, нужной только для раскладки. |
| `TTimer` | `Interval` (мс), `Enabled` | `OnTimer` | В рантайме не виден; кладётся куда угодно в дерево объектов формы. |
| `TImage` | `Picture`, `Stretch`, `Center`, `Proportional` | — | `Picture` обычно оставляют пустым в `.lfm` и загружают из кода через `Picture.LoadFromFile(...)`, если изображение не должно встраиваться ресурсом. |
| `TBevel` | `Shape`, `Style` | — | Чисто декоративный разделитель или рамка. |
| `TShape` | `Shape`, `Brush.Color`, `Pen.Color` | — | Простые геометрические фигуры. |

## Общие элементы (ComCtrls)

| Элемент | Частые свойства | Частые события | Замечания |
|---|---|---|---|
| `TStatusBar` | `SimpleText`, `Panels` | — | Для одного сообщения используй `SimpleText`; для нескольких секций — `Panels`. |
| `TProgressBar` | `Min`, `Max`, `Position` | — | |
| `TTrackBar` | `Min`, `Max`, `Position`, `Frequency` | `OnChange` | |
| `TPageControl` | `ActivePage`, `TabIndex` | `OnChange` | Контейнер для `TTabSheet`. |
| `TTabSheet` | `Caption` | — | Живёт внутри `TPageControl`; в `.lfm` объявляется вложенным `object`. |
| `TTreeView` | `Items` (TTreeNodes) | `OnSelectionChanged` | Динамическое содержимое заполняй из кода через `Items.AddChild(...)`. |
| `TListView` | `ViewStyle`, `Columns`, `Items` | `OnSelectItem` | |

## Диалоги

Все они не визуальны во время разработки — в IDE показываются иконкой, а в `.lfm` — обычным блоком
`object Name: TXxxDialog ... end` без координат. Вызывай `.Execute` из кода; он возвращает
логическое значение.

| Элемент | Модуль | Ключевые свойства |
|---|---|---|
| `TOpenDialog` | `Dialogs` | `Filter`, `FileName`, `InitialDir`, `Options` |
| `TSaveDialog` | `Dialogs` | То же, что выше |
| `TSelectDirectoryDialog` | `Dialogs` | `FileName` (после `.Execute` содержит выбранную папку) |
| `TColorDialog` | `Dialogs` | `Color` |
| `TFontDialog` | `Dialogs` | `Font` |
| `TMessageDlg` (функция, не компонент) | `Dialogs` | Вызывается напрямую: `MessageDlg('text', mtInformation, [mbOK], 0);` — запись в `.lfm` не нужна. |

Синтаксис `Filter`: `'Text files (*.txt)|*.txt|All files (*.*)|*.*'` — пары «отображаемое имя» и
шаблон, разделённые `|`.

## Меню

`TMainMenu` лежит на форме невизуально; каждое меню и каждый пункт — вложенный объект `TMenuItem`
в `.lfm`:

```
object MainMenu1: TMainMenu
  object mnuFile: TMenuItem
    Caption = '&File'
    object mnuFileOpen: TMenuItem
      Caption = '&Open...'
      OnClick = mnuFileOpenClick
    end
    object mnuFileExit: TMenuItem
      Caption = 'E&xit'
      OnClick = mnuFileExitClick
    end
  end
end
```

`&` перед буквой задаёт мнемонику по Alt. Каждому `TMenuItem` с `OnClick` нужны соответствующее
поле и обработчик в `.pas`, как любому другому элементу.

## Таблицы

`TStringGrid` (модуль `Grids`) — обычный выбор для простых табличных данных: `RowCount`,
`ColCount`, `FixedRows` и `FixedCols` (строки и столбцы заголовков), а `Cells[col, row]` служит для
чтения и записи значений из кода. Для данных из базы уместнее `TDBGrid` (модуль `DBGrids`),
привязанный к `TDataSource`, — но это тянет весь стек доступа к данным (`TDataSource`, компонент
набора данных, соединение), что выходит за рамки базовой раскладки интерфейса.

## Готовые примеры

**Поле ввода с подписью и кнопкой отправки**, `.lfm`:

```
object EditName: TEdit
  Left = 16
  Height = 23
  Top = 40
  Width = 200
  TabOrder = 0
end
object BtnSubmit: TButton
  Left = 16
  Height = 25
  Top = 72
  Width = 90
  Caption = 'Submit'
  OnClick = BtnSubmitClick
  TabOrder = 1
end
```

соответствующие поля класса и обработчик в `.pas`:

```pascal
type
  TForm1 = class(TForm)
    EditName: TEdit;
    BtnSubmit: TButton;
    procedure BtnSubmitClick(Sender: TObject);
  private
  public
  end;

implementation

{$R *.lfm}

procedure TForm1.BtnSubmitClick(Sender: TObject);
begin
  ShowMessage('Hello, ' + EditName.Text);
end;
```

**Флажок, включающий и выключающий другой элемент**, `.lfm`:

```
object ChkEnable: TCheckBox
  Left = 16
  Height = 19
  Top = 16
  Width = 90
  Caption = 'Enable'
  OnChange = ChkEnableChange
  TabOrder = 0
end
```

`.pas`:

```pascal
procedure TForm1.ChkEnableChange(Sender: TObject);
begin
  EditName.Enabled := ChkEnable.Checked;
end;
```
