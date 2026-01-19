# 🎯 CS2 Smoke Simulator - Финальная версия

Интеллектуальный поиск позиций для броска дымовых гранат в Counter-Strike 2.

## ⚡ Быстрый старт

```bash
# 1. Установка
pip install -r requirements.txt

# 2. Тест
python src/test_physics.py

# 3. Запуск сервера
python server.py

# 4. Откройте браузер
http://localhost:5000
```

## 📁 Структура

```
cs2_smoke_simulator_final/
├── src/
│   ├── physics_engine.py      # Физический движок PyBullet
│   ├── smoke_finder.py        # Поиск позиций
│   ├── physics_config.py      # Параметры CS2
│   ├── map_loader.py          # Загрузчик карт
│   ├── utils.py               # Утилиты
│   └── test_physics.py        # Тест
├── web/
│   └── index.html             # Веб-интерфейс
├── map/                        # GLB файлы карт
├── server.py                   # Flask API
├── requirements.txt
└── README.md
```

## 🎮 Использование

### Python API

```python
from physics_engine import EnhancedPhysicsEngine
from smoke_finder import SmokeFinder, SearchStrategy
from physics_config import ThrowType
import numpy as np

# Инициализация
physics = EnhancedPhysicsEngine(gui=False)
finder = SmokeFinder(physics)

# Поиск
target = np.array([500, 500, 50])
solutions = finder.find_smokes(
    target_pos=target,
    throw_type=ThrowType.LEFT_CLICK,
    strategy=SearchStrategy.GRID_SEARCH,
    max_results=5
)

# Результаты
for sol in solutions:
    print(sol.cs2_commands['combined'])
```

### Web Interface

1. Запустите `python server.py`
2. Откройте http://localhost:5000
3. Введите целевую позицию
4. Нажмите "Начать поиск"

### REST API

```bash
# Поиск смоков
curl -X POST http://localhost:5000/find_smokes \
  -H "Content-Type: application/json" \
  -d '{
    "target_pos": [500, 500, 50],
    "throw_type": "LEFT_CLICK",
    "strategy": "GRID_SEARCH"
  }'
```

## ⚙️ Конфигурация

Редактируйте `src/physics_config.py`:

```python
# Скорости броска (units/sec)
throw_speeds = {
    ThrowType.LEFT_CLICK: 1000.0,
    ThrowType.BOTH_CLICKS: 600.0,
    ThrowType.RIGHT_CLICK: 400.0
}

# Физика
gravity = 800.0
grenade_restitution = 0.45
grenade_friction = 0.5
```

## 🗺️ Добавление карт

1. Экспортируйте коллизионную геометрию в `.glb`
2. Поместите в папку `map/`
3. Загрузите: `EnhancedPhysicsEngine(map_name="your_map")`

## 🔧 Решение проблем

**PyBullet не устанавливается:**
```bash
pip install wheel setuptools
pip install pybullet --no-cache-dir
```

**Сервер не запускается:**
```bash
# Проверьте порт
lsof -i :5000
# Или измените порт в server.py
```

## 📊 Стратегии поиска

- `GRID_SEARCH` - Полный перебор по сетке (медленно, точно)
- `GENETIC` - Генетический алгоритм (быстро, хорошо)
- `HYBRID` - Комбинированный подход (оптимально)

## 📄 Лицензия

MIT License

---
Made with ❤️ for CS2 community
