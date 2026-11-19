"""Text descriptions for every GraphQL node.

Applied to the built Strawberry schema so GraphiQL shows them as tooltips and
an agent reading schema.graphql gets the same context.
"""
from __future__ import annotations

TYPE_DESCRIPTIONS = {
    "Query": "Корневые запросы калькулятора: модели и окна, строки логов, пересчёт, сверка и итоги.",
    "Model": "Модель из прайс-листа: набор тарифных окон и ставки для расчёта.",
    "TariffWindow": "Тарифное окно модели: дни недели, интервал в UTC и ставки $/1M токенов.",
    "Usage": "Токены запроса из строки лога.",
    "CostLine": "Постатейная стоимость: код компонента, токены, ставка и сумма.",
    "CostComponent": "Ненулевой компонент стоимости для компактной раскладки.",
    "Calculation": "Результат пересчёта строки по формулам и прайс-листу.",
    "RecordedCost": "Стоимость, записанная в таблицу логов (recorded).",
    "CostDifference": "Разница recorded − calculated по компонентам; положительное значение — таблица завышает.",
    "RowCalculation": "Строка лога, записанная стоимость, пересчёт, разница и результат записи.",
    "LogRow": "Строка листа «Сырые логи»: идентификаторы, токены и записанная стоимость.",
    "DiscrepancyGroup": "Группа строк с одной причиной расхождения.",
    "DiscrepancySummary": "Сводка: сколько строк попало в каждую группу расхождений.",
    "CostTotals": "Итоги по всей таблице: записано, пересчитано, разница.",
    "WriteResult": "Результат записи calculated/difference/reason в xlsx.",
    "LogRowInput": "Данные строки лога для расчёта без чтения таблицы.",
    "UsageInput": "Токены запроса для запроса calculate.",
    "ModelName": "Идентификатор модели в прайс-листе.",
    "PriceTier": "Тип тарифа: peak или off-peak.",
    "DayOfWeek": "День недели тарифного окна (UTC).",
    "WindowKind": "Тип окна: все сутки или интервал.",
}

FIELD_DESCRIPTIONS = {
    "Query": {
        "models": "Все модели из прайс-листа с их окнами и ставками.",
        "model": "Одна модель по идентификатору; null, если модели нет.",
        "discrepancySummary": "Количество строк по группам расхождений (match, reasoning, peak и т.д.).",
        "costTotals": "Общая стоимость по всей таблице: recorded, calculated и difference.",
        "logRow": "Строка лога по requestId или по номеру строки Excel; null, если не найдена.",
        "calculateRow": "Считает строку лога, показывает recorded/calculated/difference и может записать их в xlsx.",
        "calculate": "Считает переданные вручную токены по модели и времени, без чтения таблицы.",
    },
    "Model": {
        "name": "Идентификатор модели (enum).",
        "slug": "Строковый slug модели, как в прайс-листе.",
        "priceList": "Название прайс-листа, к которому относится модель.",
        "windows": "Все тарифные окна модели.",
        "windowAt": "Окно, действующее в указанный момент UTC; null, если окна нет.",
    },
    "TariffWindow": {
        "label": "Метка окна из прайс-листа, например t06-10 или w00-24.",
        "kind": "ALL_DAY или TIME_RANGE.",
        "days": "Дни недели, когда действует окно.",
        "startHour": "Начало окна в UTC, включительно.",
        "endHour": "Конец окна в UTC, исключительно.",
        "tier": "PEAK или OFF_PEAK.",
        "inputPerMillion": "Ставка input, $ за 1M токенов.",
        "outputPerMillion": "Ставка output, $ за 1M токенов.",
        "cacheReadPerMillion": "Ставка cache read, $ за 1M токенов.",
        "rate": "Наценка организации из прайс-листа (справочно, уже включена в цены).",
        "searchContextCostPerQuery": "Стоимость search context за запрос, если задана в прайсе.",
        "covers": "Попадает ли указанный момент UTC в это окно.",
    },
    "Usage": {
        "promptTokens": "Входные токены запроса.",
        "completionTokens": "Все выходные токены, включая reasoning и изображения.",
        "cachedInputTokens": "Входные токены, прочитанные из кэша.",
        "cacheCreationTokens": "Токены, записанные в кэш.",
        "reasoningTokens": "Токены reasoning; вычитаются из completion для text_tokens.",
        "acceptedPredictionTokens": "Принятые токены prediction.",
        "rejectedPredictionTokens": "Отклонённые токены prediction.",
        "imageTokens": "Входные токены изображений.",
        "outputImageTokens": "Выходные токены изображений.",
        "audioInputTokens": "Входные аудиотокены.",
        "audioOutputTokens": "Выходные аудиотокены.",
        "totalTokens": "Суммарные токены запроса из выгрузки.",
        "textTokens": "completion − reasoning − audio_input − image − output_image.",
    },
    "CostLine": {
        "code": "Код компонента: input, cachedInput, output, reasoning, prediction, image, cacheCreation, webSearch.",
        "label": "Человекочитаемое имя компонента.",
        "tokens": "Количество токенов компонента; null для webSearch.",
        "ratePerMillion": "Ставка $/1M; null, если ставки в прайсе нет.",
        "amount": "Стоимость компонента в долларах.",
    },
    "CostComponent": {
        "code": "Код компонента.",
        "label": "Человекочитаемое имя компонента.",
        "tokens": "Токены компонента, если известны.",
        "ratePerMillion": "Эффективная ставка $/1M, если известна.",
        "amount": "Стоимость компонента.",
    },
    "Calculation": {
        "requestId": "requestId строки, если расчёт привязан к логу.",
        "model": "Модель, по которой считали.",
        "window": "Тарифное окно, выбранное по start_time.",
        "usage": "Токены, участвовавшие в расчёте.",
        "textTokens": "Токены текстового вывода после вычитания reasoning/audio/image.",
        "lines": "Все строки расчёта, включая нулевые.",
        "components": "Только ненулевые строки; includeZero=true — все.",
        "total": "Итоговая стоимость по формуле.",
    },
    "RecordedCost": {
        "input": "Записанная стоимость input.",
        "cachedInput": "Записанная стоимость cached input.",
        "output": "Записанная стоимость output.",
        "reasoning": "Записанная стоимость reasoning.",
        "prediction": "Записанная стоимость prediction.",
        "image": "Записанная стоимость изображений.",
        "cacheCreation": "Записанная стоимость создания кэша.",
        "webSearch": "Записанная стоимость web search.",
        "total": "Записанный total_cost.",
        "componentsSum": "Сумма cost-колонок записи; может не совпадать с total.",
        "lines": "Развёртка записанной стоимости; токены берутся из usage строки, ставка эффективная.",
        "components": "Только ненулевые компоненты; includeZero=true — все.",
    },
    "CostDifference": {
        "input": "recorded.input − calculated.input.",
        "cachedInput": "recorded.cachedInput − calculated.cachedInput.",
        "output": "recorded.output − calculated.output.",
        "reasoning": "recorded.reasoning − calculated.reasoning; положительное значение — reasoning в таблице завышен.",
        "prediction": "recorded.prediction − calculated.prediction.",
        "image": "recorded.image − calculated.image.",
        "cacheCreation": "recorded.cacheCreation − calculated.cacheCreation.",
        "webSearch": "recorded.webSearch − calculated.webSearch.",
        "total": "recorded.total − calculated.total.",
        "components": "Только ненулевые расхождения; includeZero=true — все.",
    },
    "RowCalculation": {
        "row": "Исходная строка лога.",
        "recorded": "Стоимость, записанная в таблицу.",
        "calculated": "Стоимость, пересчитанная по формулам.",
        "difference": "Разница recorded − calculated.",
        "written": "Результат записи в xlsx; null, если запись не запрашивалась.",
    },
    "LogRow": {
        "requestId": "Идентификатор запроса из выгрузки.",
        "rowNumber": "Номер строки в Excel-листе «Сырые логи» (первая строка данных — 5).",
        "startTime": "Момент запроса в UTC.",
        "organizationId": "Идентификатор организации.",
        "client": "Название клиента.",
        "modelGroup": "Группа модели, по которой выбирается прайс-лист.",
        "model": "Модель из строки лога.",
        "modelName": "Модель как enum; null, если её нет в прайс-листе.",
        "realModel": "Реальная модель/алиас из строки лога.",
        "callType": "Тип вызова (acompletion, aresponses и т.п.).",
        "status": "Статус запроса: success или failure.",
        "httpStatus": "HTTP-код ответа.",
        "usage": "Токены запроса.",
        "recorded": "Стоимость, записанная в таблицу.",
        "calculated": "Стоимость, пересчитанная по формулам.",
        "difference": "Разница recorded − calculated.",
    },
    "DiscrepancyGroup": {
        "code": "Код группы: match, reasoning_double_billing, off_peak_rate_in_peak_window, zero_total, total_not_sum_of_components, other.",
        "title": "Человекочитаемое название группы.",
        "requests": "Сколько строк попало в группу.",
        "recordedTotal": "Сумма recorded по группе.",
        "calculatedTotal": "Сумма calculated по группе.",
        "differenceTotal": "Сумма recorded − calculated по группе.",
        "sampleRequestIds": "До пяти requestId для примеров.",
        "recorded": "То же, что recordedTotal, для кратких запросов.",
        "calculated": "То же, что calculatedTotal, для кратких запросов.",
        "difference": "То же, что differenceTotal, для кратких запросов.",
    },
    "DiscrepancySummary": {
        "requests": "Всего строк в выборке.",
        "matchedRequests": "Строк без расхождений (match).",
        "discrepantRequests": "Строк хотя бы с одним расхождением.",
        "groups": "Разбивка по причинам расхождений.",
    },
    "CostTotals": {
        "requests": "Всего строк в выборке.",
        "recordedTotal": "Сумма total_cost по всей таблице.",
        "calculatedTotal": "Сумма пересчитанных total по всей таблице.",
        "differenceTotal": "recordedTotal − calculatedTotal.",
    },
    "WriteResult": {
        "workbook": "Путь к xlsx, в который записали.",
        "calculatedWritten": "Записаны ли calculated_* колонки.",
        "differenceWritten": "Записаны ли difference_* колонки.",
        "reasonWritten": "Записана ли колонка discrepancy_reason.",
    },
    "LogRowInput": {
        "startTime": "Момент запроса в UTC; по нему выбирается тарифное окно.",
        "model": "Модель из прайс-листа.",
        "usage": "Токены запроса.",
        "requestId": "Необязательный requestId для результата.",
        "organizationId": "Необязательный organizationId.",
        "status": "Необязательный статус (на расчёт не влияет).",
        "cacheCreationCost": "Стоимость создания кэша из выгрузки.",
        "webSearchCost": "Стоимость web search из выгрузки.",
    },
    "UsageInput": {
        "promptTokens": "Входные токены.",
        "completionTokens": "Выходные токены, включая reasoning.",
        "cachedInputTokens": "Входные токены из кэша.",
        "cacheCreationTokens": "Токены создания кэша.",
        "reasoningTokens": "Токены reasoning.",
        "acceptedPredictionTokens": "Принятые токены prediction.",
        "rejectedPredictionTokens": "Отклонённые токены prediction.",
        "imageTokens": "Входные токены изображений.",
        "outputImageTokens": "Выходные токены изображений.",
        "audioInputTokens": "Входные аудиотокены.",
        "audioOutputTokens": "Выходные аудиотокены.",
        "totalTokens": "Суммарные токены (справочно).",
    },
}

ARG_DESCRIPTIONS = {
    "Query": {
        "model": {"name": "Идентификатор модели."},
        "logRow": {
            "requestId": "requestId строки лога.",
            "rowNumber": "Номер строки Excel (первая строка данных — 5).",
        },
        "calculateRow": {
            "requestId": "requestId строки лога.",
            "rowNumber": "Номер строки Excel (первая строка данных — 5).",
            "writeCalculated": "Записать calculated_* колонки в xlsx.",
            "writeDifference": "Записать difference_* колонки в xlsx.",
            "writeReason": "Записать колонку discrepancy_reason.",
        },
        "calculate": {"row": "Токены и модель для расчёта."},
    },
    "Model": {"windowAt": {"at": "Момент UTC для выбора окна."}},
    "TariffWindow": {"covers": {"at": "Момент UTC для проверки окна."}},
    "Calculation": {"components": {"includeZero": "Включить нулевые компоненты."}},
    "RecordedCost": {"components": {"includeZero": "Включить нулевые компоненты."}},
    "CostDifference": {"components": {"includeZero": "Включить нулевые компоненты."}},
}

ENUM_VALUE_DESCRIPTIONS = {
    "ModelName": {
        "DEEPSEEK_FLASH": "deepseek-flash.",
        "DEEPSEEK_V3_2": "deepseek-v3.2.",
        "DEEPSEEK_V4_FLASH": "deepseek-v4-flash.",
        "DEEPSEEK_V4_FLASH_0731": "deepseek-v4-flash-0731.",
        "DEEPSEEK_V4_FLASH_VISION_EXP": "deepseek-v4-flash-vision-exp.",
        "DEEPSEEK_V4_PRO": "deepseek-v4-pro.",
        "DEEPSEEK_V4_PRO_0813": "deepseek-v4-pro-0813.",
        "DEEPSEEK_V4_1_FLASH": "deepseek-v4.1-flash.",
        "DEEPSEEK_V4_1_FLASH_1017_ALI": "deepseek-v4.1-flash-1017-ali.",
    },
    "PriceTier": {"PEAK": "Пиковый тариф.", "OFF_PEAK": "Внепиковый тариф."},
    "DayOfWeek": {
        "MON": "Понедельник.",
        "TUE": "Вторник.",
        "WED": "Среда.",
        "THU": "Четверг.",
        "FRI": "Пятница.",
        "SAT": "Суббота.",
        "SUN": "Воскресенье.",
    },
    "WindowKind": {
        "ALL_DAY": "Одна цена на все сутки.",
        "TIME_RANGE": "Окно с началом и концом.",
    },
}


def apply_descriptions(schema) -> None:
    """Attach descriptions to the built GraphQL schema (tooltips + SDL)."""
    type_map = schema._schema.type_map
    for name, description in TYPE_DESCRIPTIONS.items():
        gql_type = type_map.get(name)
        if gql_type is not None:
            gql_type.description = description

    for type_name, fields in FIELD_DESCRIPTIONS.items():
        gql_type = type_map.get(type_name)
        if gql_type is None:
            continue
        for field_name, description in fields.items():
            field = gql_type.fields.get(field_name)
            if field is not None:
                field.description = description

    for type_name, fields in ARG_DESCRIPTIONS.items():
        gql_type = type_map.get(type_name)
        if gql_type is None:
            continue
        for field_name, args in fields.items():
            field = gql_type.fields.get(field_name)
            if field is None:
                continue
            for arg_name, description in args.items():
                arg = field.args.get(arg_name)
                if arg is not None:
                    arg.description = description

    for enum_name, values in ENUM_VALUE_DESCRIPTIONS.items():
        gql_type = type_map.get(enum_name)
        if gql_type is None:
            continue
        for value_name, description in values.items():
            value = gql_type.values.get(value_name)
            if value is not None:
                value.description = description
