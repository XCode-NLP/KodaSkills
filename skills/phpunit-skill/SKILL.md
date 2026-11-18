---
name: phpunit-skill
description: "Написание тестов на PHPUnit для PHP: утверждения, поставщики данных, моки и тестовые двойники, жизненный цикл теста, типичные ошибки и настройка запуска. Используй, когда речь идёт о PHPUnit, TestCase, assertEquals, поставщиках данных или юнит-тестах на PHP."
license: MIT
metadata:
  author: TestMu AI
  source: https://github.com/LambdaTest/agent-skills
---

# Тестирование на PHPUnit

## Основные шаблоны

### Базовый тест

```php
<?php
use PHPUnit\Framework\TestCase;

class CalculatorTest extends TestCase
{
    private Calculator $calculator;

    protected function setUp(): void
    {
        $this->calculator = new Calculator();
    }

    public function testAddition(): void
    {
        $this->assertEquals(5, $this->calculator->add(2, 3));
    }

    public function testDivideByZero(): void
    {
        $this->expectException(\DivisionByZeroError::class);
        $this->calculator->divide(10, 0);
    }

    public function testMultipleAssertions(): void
    {
        $this->assertSame(4, $this->calculator->add(2, 2));
        $this->assertSame(0, $this->calculator->subtract(2, 2));
        $this->assertSame(6, $this->calculator->multiply(2, 3));
    }
}
```

### Поставщики данных

```php
/**
 * @dataProvider additionProvider
 */
public function testAdd(int $a, int $b, int $expected): void
{
    $this->assertEquals($expected, $this->calculator->add($a, $b));
}

public static function additionProvider(): array
{
    return [
        'положительные числа' => [2, 3, 5],
        'отрицательные числа' => [-1, -1, -2],
        'нули'                => [0, 0, 0],
        'смешанные'           => [10, -5, 5],
    ];
}
```

### Утверждения

```php
$this->assertEquals($expected, $actual);
$this->assertSame($expected, $actual);          // строгое сравнение типов
$this->assertNotEquals($unexpected, $actual);
$this->assertTrue($condition);
$this->assertFalse($condition);
$this->assertNull($value);
$this->assertNotNull($value);
$this->assertCount(3, $array);
$this->assertContains('item', $array);
$this->assertArrayHasKey('key', $array);
$this->assertInstanceOf(MyClass::class, $obj);
$this->assertStringContainsString('sub', $string);
$this->assertMatchesRegularExpression('/\d+/', $string);
$this->assertEmpty($collection);
$this->assertGreaterThan(5, $value);
$this->assertJsonStringEqualsJsonString($expected, $actual);
```

### Моки

```php
public function testCreateUser(): void
{
    $mockRepo = $this->createMock(UserRepository::class);
    $mockRepo->expects($this->once())
        ->method('save')
        ->with($this->isInstanceOf(User::class))
        ->willReturn(new User(1, 'Alice'));

    $mockEmail = $this->createMock(EmailService::class);
    $mockEmail->expects($this->once())
        ->method('sendWelcome')
        ->with('alice@test.com');

    $service = new UserService($mockRepo, $mockEmail);
    $result = $service->createUser('alice@test.com', 'Alice');

    $this->assertEquals(1, $result->getId());
}
```

### Жизненный цикл

```php
public static function setUpBeforeClass(): void { }   // один раз перед всеми тестами
protected function setUp(): void { }                    // перед каждым тестом
protected function tearDown(): void { }                 // после каждого теста
public static function tearDownAfterClass(): void { }  // один раз после всех тестов
```

### Антипаттерны

| Плохо | Хорошо | Почему |
|-----|------|--------|
| `assertEquals` для строгой проверки | `assertSame` для типа и значения | Приведение типов |
| Нет поставщиков данных | `@dataProvider` | Меньше дублирования |
| Глобальное состояние | `setUp()` и `tearDown()` | Изоляция тестов |
| Нет групп | `@group smoke` | Можно запускать подмножества |

## Настройка и запуск

- Установка: `composer require --dev phpunit/phpunit`
- Запуск: `./vendor/bin/phpunit` или `./vendor/bin/phpunit --group smoke`
- Конфигурация: `phpunit.xml` с наборами тестов и покрытием
