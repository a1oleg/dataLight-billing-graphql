# DeepSeek billing — GraphQL-калькулятор

Калькулятор стоимости запроса: на вход — строка лога, на выходе — постатейный
расчёт. Модели и их тарифные окна берутся из `data/prices.csv`, формулы общие
для всех моделей и окон.

Аналитический слой (сверки, тоталы, аудит) из схемы убран: сначала калькулятор,
потом — постепенно — сверка.

## Запуск

```cmd
run.cmd
```

GraphiQL: <http://127.0.0.1:8765/> · простая консоль: `/console` ·
эндпоинт: `POST /graphql`.

Вручную:

```powershell
$env:PYTHONPATH = (Resolve-Path deps).Path
$env:PORT = "8765"
python server.py
```

## Структура

| Слой | Файл | Назначение |
|---|---|---|
| Enum-ы | `billing/enums.py` | `ModelName`, `PriceTier`, `DayOfWeek`, `WindowKind` |
| Тарифы | `billing/tariffs.py` | CSV → `Model` + `TariffWindow`, нормализация цен, поиск окна по UTC |
| Формулы | `billing/formulas.py` | `Usage`, `CostLine`, `compute_lines` — единая реализация расчёта |
| Калькулятор | `billing/calculator.py` | `LogRow` → `Calculation` (модель → окно → формулы) |
| Логи | `billing/logs.py` | строки выгрузки по `request_id` / номеру строки Excel |
| Сверка | `billing/comparison.py` | разница `calculated − recorded` по компонентам |
| Запись | `billing/writer.py` | колонки `calculated_*` и `difference_*` в оригинальный файл |
| Сводка | `billing/summary.py` | количество строк по группам расхождений |
| Схема | `billing/schema.py` | GraphQL-типы и `Query` |
| HTTP | `billing/http_app.py` | GraphiQL на `/`, консоль на `/console`, `POST /graphql` |
| UI | `web/` | GraphiQL 4.0.0 + React 18.3.1 (UMD) |
| Данные | `data/prices.csv`, `data/…xlsx` | прайс-лист и исходная выгрузка логов |

## Схема

```graphql
enum ModelName { DEEPSEEK_FLASH DEEPSEEK_V3_2 DEEPSEEK_V4_FLASH … }
enum PriceTier { PEAK OFF_PEAK }
enum DayOfWeek { MON TUE WED THU FRI SAT SUN }
enum WindowKind { ALL_DAY TIME_RANGE }

type Model {
  name: ModelName!
  slug: String!
  priceList: String!
  windows: [TariffWindow!]!
  windowAt(at: DateTime!): TariffWindow
}

type TariffWindow {
  label: String!
  kind: WindowKind!
  days: [DayOfWeek!]!
  startHour: Int!
  endHour: Int!
  tier: PriceTier!
  inputPerMillion: Float!
  outputPerMillion: Float!
  cacheReadPerMillion: Float!
  rate: Float!
  searchContextCostPerQuery: Float
  covers(at: DateTime!): Boolean!
}

type Usage {
  promptTokens: Int!
  completionTokens: Int!
  cachedInputTokens: Int!
  cacheCreationTokens: Int!
  reasoningTokens: Int!
  acceptedPredictionTokens: Int!
  rejectedPredictionTokens: Int!
  imageTokens: Int!
  outputImageTokens: Int!
  audioInputTokens: Int!
  audioOutputTokens: Int!
  totalTokens: Int!
  textTokens: Int!
}

type CostComponent {
  code: String!
  label: String!
  tokens: Int
  ratePerMillion: Float
  amount: Float!
}

type CostLine {
  code: String!
  label: String!
  tokens: Int
  ratePerMillion: Float
  amount: Float!
}

type Calculation {
  requestId: ID
  model: Model!
  window: TariffWindow!
  usage: Usage!
  textTokens: Int!
  lines: [CostLine!]!
  components(includeZero: Boolean = false): [CostComponent!]!
  total: Float!
}

type RecordedCost {
  input: Float!  cachedInput: Float!  output: Float!  reasoning: Float!
  prediction: Float!  image: Float!  cacheCreation: Float!  webSearch: Float!
  total: Float!  componentsSum: Float!
  components(includeZero: Boolean = false): [CostComponent!]!
}

type CostDifference {
  input: Float!  cachedInput: Float!  output: Float!  reasoning: Float!
  prediction: Float!  image: Float!  cacheCreation: Float!  webSearch: Float!
  total: Float!
  components(includeZero: Boolean = false): [CostComponent!]!
}

type RowCalculation {
  row: LogRow!
  recorded: RecordedCost!
  calculated: Calculation!
  difference: CostDifference!
  written: WriteResult
}

type WriteResult {
  workbook: String!
  calculatedWritten: Boolean!
  differenceWritten: Boolean!
  reasonWritten: Boolean!
}

type DiscrepancyGroup {
  code: String!
  title: String!
  requests: Int!
  recordedTotal: Float!
  calculatedTotal: Float!
  differenceTotal: Float!
  sampleRequestIds: [String!]!
}

type DiscrepancySummary {
  requests: Int!
  matchedRequests: Int!
  discrepantRequests: Int!
  groups: [DiscrepancyGroup!]!
}

type LogRow {
  requestId: ID!
  rowNumber: Int!
  startTime: DateTime!
  organizationId: String!
  client: String!
  modelGroup: String!
  model: String!
  modelName: ModelName
  realModel: String!
  callType: String!
  status: String!
  httpStatus: Int!
  usage: Usage!
  recorded: RecordedCost!
  calculated: Calculation!
  difference: CostDifference!
}

input UsageInput {
  promptTokens: Int!
  completionTokens: Int!
  cachedInputTokens: Int = 0
  cacheCreationTokens: Int = 0
  reasoningTokens: Int = 0
  acceptedPredictionTokens: Int = 0
  rejectedPredictionTokens: Int = 0
  imageTokens: Int = 0
  outputImageTokens: Int = 0
  audioInputTokens: Int = 0
  audioOutputTokens: Int = 0
  totalTokens: Int = 0
}

input LogRowInput {
  startTime: DateTime!
  model: ModelName!
  usage: UsageInput!
  requestId: ID
  organizationId: ID
  status: String
  cacheCreationCost: Float = 0
  webSearchCost: Float = 0
}

type Query {
  models: [Model!]!
  model(name: ModelName!): Model
  discrepancySummary: DiscrepancySummary!
  logRow(requestId: ID, rowNumber: Int): LogRow
  calculateRow(
    requestId: ID
    rowNumber: Int
    writeCalculated: Boolean = false
    writeDifference: Boolean = false
    writeReason: Boolean = false
  ): RowCalculation
  calculate(row: LogRowInput!): Calculation!
}
```

## Строка лога по id или номеру

`logRow` принимает **либо** `requestId`, **либо** `rowNumber`. `rowNumber` —
это номер строки в Excel-листе «Сырые логи»: первая строка данных — `5`,
последняя — `30984`. Если переданы оба аргумента, приоритет у `requestId`;
если ни одного — вернётся `null`.

По id:

```graphql
{
  logRow(requestId: "06faa446-23f5-4386-9838-81d847e3405d") {
    requestId
    rowNumber
    startTime
    organizationId
    client
    modelGroup
    modelName
    status
    usage { promptTokens completionTokens cachedInputTokens reasoningTokens textTokens }
    recorded { input cachedInput output reasoning total }
  }
}
```

По номеру строки Excel:

```graphql
{
  logRow(rowNumber: 5) {
    requestId
    rowNumber
    modelGroup
    usage { promptTokens completionTokens textTokens }
    recorded { total }
  }
}
```

`rowNumber` в ответе — тот же номер строки Excel. Неизвестный id или номер
возвращает `null`.

## Расчёт по строке и разница

`calculateRow` берёт строку по `requestId`/`rowNumber`, считает её по формулам
и показывает записанные в таблицу суммы и разницу:

```graphql
{
  calculateRow(rowNumber: 5) {
    row { requestId rowNumber modelGroup }
    recorded { components { code label amount } total }
    calculated { window { label tier } components { code tokens ratePerMillion amount } total }
    difference { components { code label amount } total }
  }
}
```

`components` по умолчанию отдаёт только ненулевые строки; чтобы увидеть все,
передайте `components(includeZero: true)`. `total` у `difference` выводится
всегда, даже если он `0`.

`difference = calculated − recorded`. Для первой строки разница нулевая;
для `99bd4acd…` — `reasoning = -0.000313`, итог `-0.000313`; для
`resp_04436d5c…` — `+0.023231494`.

## Запись в таблицу

`calculateRow` умеет записывать результат в книгу:

```graphql
{
  calculateRow(
    rowNumber: 9
    writeCalculated: true
    writeDifference: true
    writeReason: true
  ) {
    row { requestId rowNumber }
    recorded { total }
    calculated { total }
    difference { components { code amount } total }
    written { workbook calculatedWritten differenceWritten reasonWritten }
  }
}
```

В лист «Сырые логи» справа от старых колонок добавляются две группы
и колонка причины:

```
calculated_input_cost … calculated_total_cost
difference_input_cost  … difference_total_cost
discrepancy_reason
```

Старые колонки (включая `total_cost`, столбец AH) не меняются. Запись идёт
в оригинальный `data/DeepSeek_peak_offpeak_октябрь_2026_Тест.xlsx` — копия
не создаётся. Для разового пересчёта всех строк:

```powershell
python tools/recalculate_all.py
```

Скрипт проходит все 30 980 строк, пишет обе группы и сохраняет книгу один раз;
`written.workbook` возвращает фактический путь. Сохранение книги занимает
несколько секунд.

Сейчас оригинальный файл уже пересчитан: `calculated_total_cost` и
`difference_total_cost` заполнены для всех 30 980 строк.

## Сводка по группам расхождений

```graphql
{
  discrepancySummary {
    requests
    matchedRequests
    discrepantRequests
    groups { code title requests recordedTotal calculatedTotal differenceTotal sampleRequestIds }
  }
}
```

Текущий результат:

| Группа | Строк | difference, $ |
|---|---:|---:|
| `match` — расхождений нет | 24 917 | 0 |
| `zero_total` — total_cost = 0 | 29 | +0.632824 |
| `total_not_sum_of_components` — total ≠ сумме колонок | 41 | +0.015480 |
| `reasoning_double_billing` — reasoning ×2 | 4 775 | −10.983384 |
| `off_peak_rate_in_peak_window` — off-peak в peak | 1 218 | +5.265855 |
| `other` — прочие | 0 | 0 |

Всего 30 980 строк, из них с расхождением — 6 063.

## Пример

```graphql
{
  calculate(row: {
    requestId: "06faa446-23f5-4386-9838-81d847e3405d"
    startTime: "2026-10-13T00:00:27.467Z"
    model: DEEPSEEK_V4_FLASH
    usage: {
      promptTokens: 1020
      completionTokens: 2621
      cachedInputTokens: 128
      reasoningTokens: 2030
    }
  }) {
    model { name }
    window { label tier }
    textTokens
    lines { code tokens ratePerMillion amount }
    total
  }
}
```

Ответ: `textTokens = 591`, строки `input=0.000223`, `cachedInput=0.0000064512`,
`output=0.0002955`, `reasoning=0.001015`, итог **0.0015399512**.

## Формулы

Одна функция `billing.formulas.compute_lines` для всех моделей:

```
text_tokens       = completion − reasoning − audio_input − image − output_image
input             = (prompt − cached) × input_rate
cachedInput       = cached × cache_read_rate
output            = text_tokens × output_rate
reasoning         = reasoning_tokens × output_rate
prediction        = (accepted + rejected) × output_rate
image             = image_tokens × input_rate
cacheCreation     = из выгрузки (ставки в прайсе нет)
webSearch         = из выгрузки (ставки в прайсе нет)
total             = сумма строк
```

Ставки в прайсе — `$/1M`, поэтому `rate = per_million / 1_000_000`.
Окно ищется по `start_time` в UTC: день недели из `days`, интервал
`[start_hour, end_hour)`.

## Особенность CSV

В `data/prices.csv` цены записаны в 1/10 000 доллара и с разделителями тысяч:
`"1,950"` = `0.195 $/1M`, `"39"` = `0.0039 $/1M`. `rate` и
`search_context_cost_per_query` используют десятичную запятую (`"1,3"` = 1.3).
`load_models()` нормализует всё к `$/1M`; это покрыто тестами
(`tests/test_calculator.py`, проверка `0.195 / 0.78 / 0.0039`).

## Проверка на реальных строках

`python tools/verify_calculator.py`:

| request_id | модель | окно | расчёт | выгрузка |
|---|---|---|---:|---:|
| 06faa446… | deepseek-v4-flash | все сутки | 0.001539951 | 0.001539951 |
| 7e42a397… | deepseek-v4-flash | все сутки | 0.001428006 | 0.001428006 |
| 99bd4acd… | deepseek-v4-flash | все сутки | 0.000651750 | 0.000964750 |
| resp_04436d5c… | deepseek-v4-flash-0731 | t00-01 peak | 0.046462988 | 0.023231494 |
| e22a748c… | deepseek-flash | t01-04 peak | 0.015315191 | 0.000000000 |

Первые две строки совпадают с выгрузкой; остальные показывают расхождения
(двойной reasoning, off-peak в peak-окне, обнулённый итог) — это уже предмет
следующего слоя, сверки, а не калькулятора.

## Следующие шаги

1. Организации и наценка `rate` — если понадобится считать по клиентам.
2. Пакетный расчёт: резолвер `calculateMany(rows: [LogRowInput!]!)`.
3. Слой сверки (сравнение `calculated` с `recorded`) — после стабилизации
   калькулятора, отдельными шагами.
