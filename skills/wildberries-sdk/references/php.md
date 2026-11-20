# PHP

```bash
composer require eslazarev/wildberries-sdk
```

```php
<?php
use Wildberries\Sdk\Finances\Api\DefaultApi;
use Wildberries\Sdk\Finances\Configuration;

$config = Configuration::getDefaultConfiguration()
    ->setApiKey('Authorization', getenv('WB_API_TOKEN'))
    ->setHost('https://finance-api.wildberries.ru');   // обязательно — см. ниже

$api = new DefaultApi(new GuzzleHttp\Client(), $config);
$balance = $api->getV1AccountBalance();
```

Полное имя класса указано в строке `php:` сводки.

## Хост: его нужно задать самому

`Configuration` по умолчанию берёт `http://localhost`. Настоящий хост есть только в
docblock метода, так что бери его из строки `host:` сводки и вызывай
`setHost()`. Строй отдельную `Configuration` на каждый хост, когда задача охватывает
несколько сервисов.

## Ошибки

`ApiException` несёт `getCode()` (HTTP-статус) и
`getResponseBody()`. Считай 429 ограничением частоты и делай паузу; 401 и 403 указывают
на категорию токена, а не на код.

## Формы

Методы в camelCase и возвращают сгенерированные объекты моделей с геттерами
(`$balance->getData()->getCurrent()`). У каждого метода есть вариант `…WithHttpInfo`,
когда нужны код статуса или заголовки.
