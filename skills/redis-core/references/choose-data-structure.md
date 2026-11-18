# Выбор подходящей структуры данных

Выбор подходящего типа данных Redis для твоего сценария — основа производительности и экономии памяти.

| Сценарий | Рекомендуемый тип | Почему |
|----------|------------------|-----|
| Простые значения, счётчики | String | Быстрые атомарные операции |
| Объект с полями | Hash | Экономия памяти, частичные обновления, срок жизни на уровне поля |
| Очередь, последние элементы | List | O(1) на добавление и извлечение с концов |
| Уникальные элементы, участие | Set | O(1) на добавление, удаление и проверку |
| Рейтинги, диапазоны | Sorted Set | Порядок по счёту |
| Вложенные и иерархические данные | JSON | Запросы по пути, вложенные структуры, геопространственная индексация через RQE |
| Журналы событий, обмен сообщениями | Stream | Постоянное хранение, группы консьюмеров |
| Поиск по сходству | Vector Set | Нативное хранение векторов со встроенной индексацией HNSW |

**Неправильно:** использовать строки для всего.

**Python** (redis-py):
```python
# Хранение объекта как JSON-строки лишает атомарных обновлений полей
redis.set("user:1001", json.dumps({"name": "Alice", "email": "alice@example.com"}))

# Чтобы обновить email, нужно прочитать, разобрать, изменить и перезаписать объект целиком
user = json.loads(redis.get("user:1001"))
user["email"] = "new@example.com"
redis.set("user:1001", json.dumps(user))
```

**Java** (Jedis):
```java
// Плохо: хранение строкой с разделителями требует ручного разбора
jedis.set("bicycle", "Deimos;Ergonom;Enduro bikes;4972");
String bike = jedis.get("bicycle");
String[] fields = bike.split(";");
String model = fields[0];  // Хрупко и чревато ошибками
```

**Правильно:** используй Hash для объектов с полями.

**Python** (redis-py):
```python
# Hash позволяет атомарно обновлять поля
redis.hset("user:1001", mapping={"name": "Alice", "email": "alice@example.com"})

# Обновление одного поля без затрагивания остальных
redis.hset("user:1001", "email", "new@example.com")
```

**Java** (Jedis):
```java
import java.util.Map;
import java.util.HashMap;

// Хорошо: Hash естественно моделирует свойства
Map<String, String> hashFields = new HashMap<>();
hashFields.put("model", "Deimos");
hashFields.put("brand", "Ergonom");
hashFields.put("type", "Enduro bikes");
hashFields.put("price", "4972");

jedis.hset("bicycle", hashFields);

// Чтение отдельного поля
String model = jedis.hget("bicycle", "model");
```

Источник: [Choosing the Right Data Type](https://redis.io/docs/latest/develop/data-types/compare-data-types/)
