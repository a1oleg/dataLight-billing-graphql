# Решение

Калькулятор биллинга на GraphQL: [a1oleg/deepseek-billing-graphql](https://github.com/a1oleg/deepseek-billing-graphql).

В схеме сущности связаны со статическими данными: строка лога, модель, тарифное
окно, usage, записанные и пересчитанные суммы, разница. Например, по запросу

```graphql
{
  logRow(requestId: "06faa446-23f5-4386-9838-81d847e3405d") {
    modelGroup
    usage { promptTokens completionTokens textTokens }
    recorded { total }
  }
}
```

можно получить данные этой сессии из таблицы логов:

```json
{
  "data": {
    "logRow": {
      "modelGroup": "deepseek-v4-flash",
      "usage": {
        "promptTokens": 1020,
        "completionTokens": 2621,
        "textTokens": 591
      },
      "recorded": {
        "total": 0.0015399512
      }
    }
  }
}
```

Кроме того, в схеме абстрагированы вычисления. Запрос

```graphql
{
  calculateRow(requestId: "99bd4acd-cf50-415d-b263-fb81683bbef0") {
    recorded { total }
    calculated { total lines { code tokens amount } }
    difference { input cachedInput output reasoning total }
  }
}
```

возвращает записанные в таблицу ранее, посчитанные вновь и разницу между ними:

```json
{
  "data": {
    "calculateRow": {
      "recorded": {
        ...
      },
      "calculated": {
        ...     
      },
      "difference": {
        "input": 0,
        "cachedInput": 0,
        "output": 0,
        "reasoning": 0.000313,
        "total": 0.000313
      }
    }
  }
}
```
который показывает что reasoning токенов в таблице больше чем в расчёте *позже мы увидим что это задвоение reasoning токенов.
Далее я попросил DeepSeek посчитать вызывать эту ручку  для всех строк и записать расхождения, но он (как обычно) побежал впереди паровоза и сразу проанализировал причины. Результы расчётов, diff-ы и причины записаны в таблицу. Посмотреть Summary можно через:
```graphql
{
  discrepancySummary {
    requests
    matchedRequests
    discrepantRequests
    groups {      
      title
      requests 		
      sampleRequestIds
    }
  }
}
```
что возвращет группы аномалий:
```json
{
  "data": {
    "discrepancySummary": {
      "requests": 30980,
      "matchedRequests": 24917,
      "discrepantRequests": 6063,
      "groups": [
        {
          "title": "расхождений нет",
          "requests": 24917
        },
        {
          "title": "total_cost = 0 при ненулевых компонентах",
          "requests": 29,
          "sampleRequestIds": [
            "e22a748c-70bc-480f-94af-a0ee7735456f",
            "chatcmpl-7c6058b1-3cd3-929b-8cb1-6797575b968b",
            "chatcmpl-e1ed15bd-d069-9b83-9a91-ee1a5434cf0b",
            "chatcmpl-10364303-780b-9bc2-affd-dff74a365ae9",
            "resp_09afc819-8d1f-923b-bcdf-d984a8b82225"
          ]
        },
        {
          "title": "total_cost не равен сумме колонок",
          "requests": 41,
          "sampleRequestIds": [
            "chatcmpl-6c961de6-b0de-9a91-8835-35a79b0bfff3",
            "358c8278-510a-4101-9f45-311ce30f8ce9",
            "chatcmpl-79969119-89e9-9a99-97f4-68cd369347ca",
            "chatcmpl-9392b138-56f2-9250-9f23-b90f8280ce65",
            "chatcmpl-68fbee25-50b7-9f16-9a7b-d7a73512485a"
          ]
        },
        {
          "title": "reasoning по двойной ставке",
          "requests": 4775,
          "sampleRequestIds": [
            "99bd4acd-cf50-415d-b263-fb81683bbef0",
            "72698c7e-396b-4e80-9413-4fd48c3396f8",
            "af008093-c85e-403e-be3e-c729c087e592",
            "ab7e2e81-9412-4bea-b076-3f9f23851594",
            "b92ae97c-7c85-4953-b4ad-086cc0d87e0b"
          ]
        },
        {
          "title": "off-peak цена в peak-окне",
          "requests": 1218,
          "sampleRequestIds": [
            "chatcmpl-fabd7e24-2b03-986c-9247-5df0fbd1ffa4",
            "resp_82e1aa07-2689-930a-aa95-4407884ac31e",
            "resp_04436d5c-b9ec-92ea-aae4-941c162ea044",
            "resp_df986048-74cd-9412-8ee8-245fcff6460f",
            "resp_3c0bab12-ac5e-9c58-b590-65893d949514"
          ]
        }
      ]
    }
  }
}
```
*Дальше можно захардкодить виды аномалий в схему и получить параметризированную ручку выгрузки всех событий по причинам. 

К очевидным вопросам по результатам этих диагнозов добавлю что ещё копал бы:
1. как работают тарифные окна на пересечении их временнЫх границ? 
2. некоторые ID начинаются с префиксов chatcmpl- и resp_ ,что это означает и оптимальна ли такая структура? (сильно пахнет каким-то костылём)
3. text_tokens = completion_tokens − reasoning_tokens − audio_input_tokens − image_tokens − output_image_tokens. 
Из выходных токенов вычитаются входные.
4. image_cost = image_tokens × input_rate. 
Картинки по входной ставке, отдельной ставки на изображения в прайсе нет.

















Общая стоимость по всей таблице:
```graphql
{
  costTotals {
    requests
    recordedTotal
    calculatedTotal
    differenceTotal
  }
}
```
результат:
```json
{
  "data": {
    "costTotals": {
      "requests": 30980,
      "recordedTotal": 249.8098483731,
      "calculatedTotal": 244.7406233137,
      "differenceTotal": 5.0692250594
    }
  }
}
```