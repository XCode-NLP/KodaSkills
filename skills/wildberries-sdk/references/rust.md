# Rust

Один крейт на область API:

```bash
cargo add wildberries_sdk_finances
```

```rust
use wildberries_sdk_finances::apis::configuration::{ApiKey, Configuration};
use wildberries_sdk_finances::apis::default_api;

let mut configuration = Configuration::new();
configuration.base_path = "https://finance-api.wildberries.ru".to_owned(); // обязательно
configuration.api_key = Some(ApiKey {
    prefix: None,
    key: std::env::var("WB_API_TOKEN")?,
});

let balance = default_api::get_v1_account_balance(&configuration).await?;
```

Путь модуля указан в строке `rust:` сводки — `default_api` для большинства
операций, `wbapi_api` и подобные для остальных.

## Хост: его нужно задать самому

`Configuration::new()` оставляет `base_path` равным `http://localhost`, и
сгенерированные функции подставляют его напрямую. Задай его из строки `host:` сводки
(или `sandbox:`) до первого вызова.

## Ошибки

Функции возвращают `Result<T, Error<SomeOperationError>>`. `Error::ResponseContent`
несёт статус и тело, так что сопоставляй с ним для 429 и делай паузу; типизированное
поле `entity` содержит модель ошибки WB, если её удалось разобрать.

## Асинхронность

Клиенты построены на `reqwest` и асинхронны — каждый вызов это `.await`, поэтому
вызывающему нужен рантайм tokio.
