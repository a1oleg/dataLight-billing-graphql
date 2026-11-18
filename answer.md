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
        "total": 0.00096475
      },
      "calculated": {
        "total": 0.00065175,
        "lines": [
          {
            "code": "input",
            "tokens": 1311,
            "amount": 0.00032775
          },
          {
            "code": "cachedInput",
            "tokens": 0,
            "amount": 0
          },
          {
            "code": "output",
            "tokens": 22,
            "amount": 0.000011
          },
          {
            "code": "reasoning",
            "tokens": 626,
            "amount": 0.000313
          },
          {
            "code": "prediction",
            "tokens": 0,
            "amount": 0
          },
          {
            "code": "image",
            "tokens": 0,
            "amount": 0
          },
          {
            "code": "cacheCreation",
            "tokens": 0,
            "amount": 0
          },
          {
            "code": "webSearch",
            "tokens": null,
            "amount": 0
          }
        ]
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

Полная схема — в [schema.graphql](schema.graphql), запуск и установка — в
[README.md](README.md).
