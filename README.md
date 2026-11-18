# DeepSeek billing — GraphQL-калькулятор

Калькулятор стоимости запроса: на вход — строка лога, на выходе — постатейный
расчёт. Модели и их тарифные окна берутся из `data/prices.csv`, формулы общие
для всех моделей и окон.

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
| Сверка | `billing/comparison.py` | разница `recorded − calculated` по компонентам |
| Запись | `billing/writer.py` | колонки `calculated_*` и `difference_*` в оригинальный файл |
| Сводка | `billing/summary.py` | количество строк по группам расхождений |
| Схема | `billing/schema.py` | GraphQL-типы и `Query` |
| HTTP | `billing/http_app.py` | GraphiQL на `/`, консоль на `/console`, `POST /graphql` |
| UI | `web/` | GraphiQL 4.0.0 + React 18.3.1 (UMD) |
| Данные | `data/prices.csv`, `data/…xlsx` | прайс-лист и исходная выгрузка логов |

## Схема

Полная GraphQL-схема — в [schema.graphql](schema.graphql); README не дублирует
типы. Пересобрать файл из кода:

```powershell
$env:PYTHONPATH = (Resolve-Path deps).Path
python tools/export_schema.py
```


В лист «Сырые логи» справа от старых колонок добавлены две группы
и колонка причины:

```
calculated_input_cost … calculated_total_cost
difference_input_cost  … difference_total_cost
discrepancy_reason
```

```powershell
python tools/recalculate_all.py
```



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

