---
name: laravel-dusk-skill
description: "Написание браузерных тестов Laravel Dusk на PHP: переходы, работа с формами, утверждения, ожидания и объекты страниц для сквозного тестирования приложений Laravel в Chrome. Используй, когда речь идёт о Dusk, Laravel Dusk, DuskTestCase или браузерных тестах приложения на Laravel."
license: MIT
metadata:
  author: TestMu AI
  source: https://github.com/LambdaTest/agent-skills
---

# Тестирование на Laravel Dusk

## Основные шаблоны

### Базовый тест

```php
<?php
namespace Tests\Browser;

use Laravel\Dusk\Browser;
use Tests\DuskTestCase;

class LoginTest extends DuskTestCase
{
    public function testLoginWithValidCredentials(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->type('email', 'user@test.com')
                ->type('password', 'password123')
                ->press('Login')
                ->assertPathIs('/dashboard')
                ->assertSee('Welcome');
        });
    }

    public function testLoginWithInvalidCredentials(): void
    {
        $this->browse(function (Browser $browser) {
            $browser->visit('/login')
                ->type('email', 'wrong@test.com')
                ->type('password', 'wrong')
                ->press('Login')
                ->assertPathIs('/login')
                ->assertSee('Invalid credentials');
        });
    }
}
```

### Методы браузера

```php
// Навигация
$browser->visit('/path');
$browser->back();
$browser->forward();
$browser->refresh();

// Формы
$browser->type('name', 'value');
$browser->clear('name');
$browser->select('select', 'option');
$browser->check('checkbox');
$browser->uncheck('checkbox');
$browser->radio('radio', 'value');
$browser->attach('file', '/path/to/file');
$browser->press('Button Text');
$browser->click('.selector');

// Утверждения
$browser->assertSee('text');
$browser->assertDontSee('text');
$browser->assertPathIs('/expected');
$browser->assertUrlIs('http://full-url');
$browser->assertInputValue('name', 'value');
$browser->assertChecked('checkbox');
$browser->assertVisible('.element');
$browser->assertMissing('.element');
$browser->assertTitle('Page Title');
$browser->assertPresent('.selector');

// Ожидания
$browser->waitFor('.element');
$browser->waitFor('.element', 10); // 10 секунд
$browser->waitUntilMissing('.loading');
$browser->waitForText('Loaded');
$browser->waitForLink('Click Me');
$browser->pause(1000); // миллисекунды
```

### Объекты страниц

```php
<?php
namespace Tests\Browser\Pages;

use Laravel\Dusk\Page;

class LoginPage extends Page
{
    public function url(): string { return '/login'; }

    public function assert(Browser $browser): void
    {
        $browser->assertPathIs($this->url());
    }

    public function login(Browser $browser, string $email, string $password): void
    {
        $browser->type('email', $email)
            ->type('password', $password)
            ->press('Login');
    }
}

// Использование
$browser->visit(new LoginPage)
    ->login($browser, 'user@test.com', 'password123');
```

## Установка и запуск

- Установка: `composer require --dev laravel/dusk && php artisan dusk:install`
- Запуск: `php artisan dusk` или `php artisan dusk tests/Browser/LoginTest.php`

## Практика

- Оформляй повторяющиеся шаги в методы объекта страницы, а не копируй цепочки вызовов между тестами.
- Для асинхронного интерфейса используй `waitFor` и `waitUntilMissing`, а не `pause` с угаданной задержкой.
- Проверяй результат по видимому состоянию страницы и адресу, а не по внутреннему состоянию приложения.
- Перед проверкой текста убедись, что элемент уже отрисован: `assertSee` не ждёт появления.
- Данные для теста создавай фабриками и убирай за собой миграциями, чтобы тесты не зависели от порядка запуска.
