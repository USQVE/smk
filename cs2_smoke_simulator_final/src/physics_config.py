"""
Конфигурация физических параметров для CS2
Все настройки в одном месте для легкой настройки
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

class ThrowType(Enum):
    """Типы бросков гранаты в CS2"""
    LEFT_CLICK = "LEFT_CLICK"    # Сильный бросок (только ЛКМ)
    BOTH_CLICKS = "BOTH_CLICKS"  # Средний бросок (ЛКМ+ПКМ)
    RIGHT_CLICK = "RIGHT_CLICK"  # Слабый бросок (только ПКМ)

@dataclass
class PhysicsConfig:
    """Основная конфигурация физики CS2"""
    
    # Гравитация и общие параметры
    gravity: float = 800.0           # Гравитация CS2 (юниты/с²)
    time_step: float = 1/120         # Шаг симуляции (120 FPS)
    
    # Параметры гранаты
    grenade_mass: float = 0.5        # Масса гранаты (кг)
    grenade_radius: float = 0.1      # Радиус гранаты (метры)
    grenade_restitution: float = 0.45  # Коэффициент отскока
    grenade_friction: float = 0.5    # Трение
    grenade_linear_damping: float = 0.03  # Линейное сопротивление воздуха
    grenade_angular_damping: float = 0.1  # Угловое сопротивление
    
    # Скорости броска (юниты/сек)
    throw_speeds: Dict[ThrowType, float] = None
    
    # Параметры игрока
    player_height: float = 1.8       # Рост игрока (метры)
    hand_height: float = 0.56        # Высота руки при броске (метры)
    
    # Координаты и масштаб
    units_per_meter: float = 39.37   # 1 метр = 39.37 юнитов CS2
    meters_per_unit: float = 0.0254  # 1 юнит = 0.0254 метра (1 дюйм)
    
    def __post_init__(self):
        if self.throw_speeds is None:
            self.throw_speeds = {
                ThrowType.LEFT_CLICK: 1000.0,
                ThrowType.BOTH_CLICKS: 600.0,
                ThrowType.RIGHT_CLICK: 400.0
            }
    
    def get_throw_speed(self, throw_type: ThrowType) -> float:
        """Получение скорости броска по типу"""
        return self.throw_speeds.get(throw_type, 900.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Экспорт конфигурации в словарь"""
        return {
            'gravity': self.gravity,
            'time_step': self.time_step,
            'grenade_mass': self.grenade_mass,
            'grenade_radius': self.grenade_radius,
            'grenade_restitution': self.grenade_restitution,
            'grenade_friction': self.grenade_friction,
            'throw_speeds': {k.name: v for k, v in self.throw_speeds.items()},
            'player_height': self.player_height,
            'hand_height': self.hand_height,
            'units_per_meter': self.units_per_meter
        }
    
    @classmethod
    def cs2_default(cls):
        """Конфигурация по умолчанию для CS2"""
        return cls()


# Глобальный экземпляр конфигурации
CS2_PHYSICS = PhysicsConfig.cs2_default()


if __name__ == "__main__":
    print("🔧 Конфигурация физики CS2:")
    config = CS2_PHYSICS
    for key, value in config.to_dict().items():
        print(f"   {key}: {value}")