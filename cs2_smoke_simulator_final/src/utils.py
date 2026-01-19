"""
Утилиты для CS2 Smoke Simulator
Вспомогательные функции для работы с путями, файлами, координатами
"""

import os
import json
import math
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict, is_dataclass
import time
import csv
from enum import Enum


class ProjectPaths:
    """Класс для управления путями проекта"""
    
    def __init__(self, project_root: str = None):
        """
        Инициализация путей проекта
        
        Args:
            project_root: корневая директория проекта (если None, определяется автоматически)
        """
        if project_root is None:
            # Определяем корневую директорию проекта
            current_file = Path(__file__).resolve()
            # Предполагаем, что utils.py находится в src/
            self.project_root = current_file.parent.parent
        else:
            self.project_root = Path(project_root)
        
        # Основные директории
        self.maps_dir = self.project_root / "map"
        self.src_dir = self.project_root / "src"
        self.web_dir = self.project_root / "web"
        self.outputs_dir = self.project_root / "outputs"
        self.data_dir = self.project_root / "data"
        
        # Создаем директории при инициализации
        self.create_directories()
    
    def create_directories(self):
        """Создание необходимых директорий проекта"""
        directories = [
            self.maps_dir,
            self.outputs_dir / "smokes",
            self.outputs_dir / "configs",
            self.outputs_dir / "debug",
            self.data_dir / "cache",
            self.data_dir / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_map_path(self, map_name: str, file_type: str = "glb") -> Optional[Path]:
        """
        Получение пути к файлу карты
        
        Args:
            map_name: название карты (например, "de_palacio_d")
            file_type: тип файла (glb, zip, vents)
            
        Returns:
            Path: путь к файлу или None если не найден
        """
        # Проверяем различные варианты имен файлов
        possible_names = [
            f"{map_name}_physics.{file_type}",
            f"{map_name}.{file_type}",
            f"{map_name}/{map_name}_physics.{file_type}",
            f"{map_name}/world_physics.{file_type}"
        ]
        
        for name in possible_names:
            path = self.maps_dir / name
            if path.exists():
                return path
        
        # Если файл не найден, возвращаем None
        return None
    
    def get_output_path(self, filename: str, subdir: str = "smokes") -> Path:
        """
        Получение пути для сохранения результатов
        
        Args:
            filename: имя файла
            subdir: поддиректория в outputs
            
        Returns:
            Path: полный путь к файлу
        """
        return self.outputs_dir / subdir / filename
    
    def clear_temp_files(self):
        """Очистка временных файлов"""
        temp_dir = self.data_dir / "temp"
        if temp_dir.exists():
            for file in temp_dir.glob("*"):
                try:
                    file.unlink()
                except:
                    pass


class CS2CoordinateConverter:
    """Конвертер координат для CS2"""
    
    # Коэффициенты преобразования (CS2 использует дюймы как единицы)
    UNITS_PER_METER = 39.37  # CS2: 1 метр = 39.37 юнитов
    METERS_PER_UNIT = 1.0 / UNITS_PER_METER
    
    @classmethod
    def meters_to_units(cls, meters: float) -> float:
        """Конвертация метров в игровые юниты"""
        return meters * cls.UNITS_PER_METER
    
    @classmethod
    def units_to_meters(cls, units: float) -> float:
        """Конвертация игровых юнитов в метры"""
        return units * cls.METERS_PER_UNIT
    
    @classmethod
    def vector_meters_to_units(cls, vector: List[float]) -> List[float]:
        """Конвертация вектора из метров в юниты"""
        return [coord * cls.UNITS_PER_METER for coord in vector]
    
    @classmethod
    def vector_units_to_meters(cls, vector: List[float]) -> List[float]:
        """Конвертация вектора из юнитов в метры"""
        return [coord * cls.METERS_PER_UNIT for coord in vector]
    
    @classmethod
    def normalize_angle(cls, angle: float) -> float:
        """
        Нормализация угла к диапазону [0, 360)
        
        Args:
            angle: угол в градусах
            
        Returns:
            float: нормализованный угол
        """
        return angle % 360
    
    @classmethod
    def clamp_angle(cls, angle: float, min_angle: float = -180, max_angle: float = 180) -> float:
        """
        Ограничение угла в диапазоне
        
        Args:
            angle: исходный угол
            min_angle: минимальный угол
            max_angle: максимальный угол
            
        Returns:
            float: ограниченный угол
        """
        return max(min_angle, min(max_angle, angle))


class MathUtils:
    """Математические утилиты"""
    
    @staticmethod
    def distance(p1: List[float], p2: List[float]) -> float:
        """
        Евклидово расстояние между двумя точками
        
        Args:
            p1: первая точка [x, y, z]
            p2: вторая точка [x, y, z]
            
        Returns:
            float: расстояние
        """
        p1_np = np.array(p1)
        p2_np = np.array(p2)
        return np.linalg.norm(p1_np - p2_np)
    
    @staticmethod
    def angle_between_vectors(v1: List[float], v2: List[float]) -> float:
        """
        Угол между двумя векторами в градусах
        
        Args:
            v1: первый вектор
            v2: второй вектор
            
        Returns:
            float: угол в градусах
        """
        v1_np = np.array(v1)
        v2_np = np.array(v2)
        
        dot = np.dot(v1_np, v2_np)
        norm = np.linalg.norm(v1_np) * np.linalg.norm(v2_np)
        
        # Избегаем ошибок округления
        cos_angle = max(-1.0, min(1.0, dot / norm))
        return math.degrees(math.acos(cos_angle))
    
    @staticmethod
    def calculate_optimal_pitch(distance: float, speed: float, gravity: float = 800.0) -> float:
        """
        Расчет оптимального угла броска для максимальной дальности
        
        Args:
            distance: расстояние до цели (метры)
            speed: начальная скорость (юниты/сек)
            gravity: гравитация
            
        Returns:
            float: оптимальный угол pitch в градусах
        """
        if speed == 0:
            return 45.0
        
        # Формула оптимального угла броска
        # θ = 0.5 * arcsin(g * d / v²)
        try:
            sin_2theta = (gravity * distance) / (speed ** 2)
            sin_2theta = max(-1.0, min(1.0, sin_2theta))  # Ограничиваем
            theta = 0.5 * math.asin(sin_2theta)
            return math.degrees(theta)
        except:
            # Если расчет невозможен, возвращаем угол 45°
            return 45.0
    
    @staticmethod
    def interpolate_trajectory(trajectory: List[List[float]], num_points: int = 100) -> List[List[float]]:
        """
        Интерполяция траектории для сглаживания
        
        Args:
            trajectory: исходная траектория
            num_points: количество точек в результате
            
        Returns:
            List[List[float]]: интерполированная траектория
        """
        if not trajectory or len(trajectory) < 2:
            return trajectory
        
        # Преобразуем в numpy для удобства
        traj_np = np.array(trajectory)
        
        # Вычисляем кумулятивное расстояние
        distances = np.zeros(len(traj_np))
        for i in range(1, len(traj_np)):
            distances[i] = distances[i-1] + np.linalg.norm(traj_np[i] - traj_np[i-1])
        
        # Параметризуем по расстоянию
        total_distance = distances[-1]
        if total_distance == 0:
            return trajectory
        
        # Создаем новые равномерно распределенные точки
        new_distances = np.linspace(0, total_distance, num_points)
        
        # Интерполируем каждую координату отдельно
        interpolated = []
        for dim in range(3):
            interp_dim = np.interp(new_distances, distances, traj_np[:, dim])
            interpolated.append(interp_dim)
        
        # Транспонируем обратно
        return np.column_stack(interpolated).tolist()
    
    @staticmethod
    def calculate_trajectory_metrics(trajectory: List[List[float]]) -> Dict[str, float]:
        """
        Вычисление метрик траектории
        
        Args:
            trajectory: траектория [[x,y,z], ...]
            
        Returns:
            Dict[str, float]: словарь метрик
        """
        if not trajectory:
            return {}
        
        traj_np = np.array(trajectory)
        
        metrics = {
            'total_distance': 0.0,
            'max_height': float(np.max(traj_np[:, 2])),
            'min_height': float(np.min(traj_np[:, 2])),
            'num_points': len(trajectory),
            'duration_estimate': len(trajectory) / 120.0  # Предполагаем 120 FPS
        }
        
        # Вычисляем общее расстояние
        for i in range(1, len(traj_np)):
            metrics['total_distance'] += np.linalg.norm(traj_np[i] - traj_np[i-1])
        
        return metrics


class FileUtils:
    """Утилиты для работы с файлами"""
    
    @staticmethod
    def save_json(data: Any, filepath: Union[str, Path], indent: int = 2) -> bool:
        """
        Сохранение данных в JSON файл
        
        Args:
            data: данные для сохранения
            filepath: путь к файлу
            indent: отступ для форматирования
            
        Returns:
            bool: успешность операции
        """
        try:
            # Преобразуем dataclass в словарь
            if is_dataclass(data) and not isinstance(data, type):
                data = asdict(data)
            
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения JSON: {e}")
            return False
    
    @staticmethod
    def load_json(filepath: Union[str, Path]) -> Optional[Dict]:
        """
        Загрузка данных из JSON файла
        
        Args:
            filepath: путь к файлу
            
        Returns:
            Optional[Dict]: загруженные данные или None
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки JSON: {e}")
            return None
    
    @staticmethod
    def save_csv(data: List[Dict], filepath: Union[str, Path]) -> bool:
        """
        Сохранение данных в CSV файл
        
        Args:
            data: список словарей
            filepath: путь к файлу
            
        Returns:
            bool: успешность операции
        """
        if not data:
            return False
        
        try:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения CSV: {e}")
            return False
    
    @staticmethod
    def generate_cs2_commands(throw_position: List[float], angles: Dict[str, float]) -> Dict[str, str]:
        """
        Генерация команд для CS2 консоли
        
        Args:
            throw_position: позиция броска [x, y, z]
            angles: углы {'pitch': ..., 'yaw': ...}
            
        Returns:
            Dict[str, str]: словарь команд
        """
        # Конвертируем в юниты CS2
        conv = CS2CoordinateConverter()
        pos_units = conv.vector_meters_to_units(throw_position)
        
        commands = {
            'setpos': f"setpos {pos_units[0]:.1f} {pos_units[1]:.1f} {pos_units[2]:.1f}",
            'setang': f"setang {angles.get('pitch', 0):.1f} {angles.get('yaw', 0):.1f} 0",
            'combined': f"setpos {pos_units[0]:.1f} {pos_units[1]:.1f} {pos_units[2]:.1f}; setang {angles.get('pitch', 0):.1f} {angles.get('yaw', 0):.1f} 0"
        }
        
        return commands
    
    @staticmethod
    def create_cs2_config(smokes_data: List[Dict], filename: str = "smokes.cfg") -> str:
        """
        Создание конфиг файла для CS2
        
        Args:
            smokes_data: данные о смоках
            filename: имя файла
            
        Returns:
            str: содержимое конфига
        """
        cfg_lines = [
            "// Автоматически сгенерированный конфиг смоков для CS2",
            "// Используйте с sv_cheats 1",
            ""
        ]
        
        for i, smoke in enumerate(smokes_data, 1):
            cfg_lines.append(f"// Смок #{i}")
            
            if 'cs2_commands' in smoke and 'combined' in smoke['cs2_commands']:
                cfg_lines.append(smoke['cs2_commands']['combined'])
            elif 'throw_position' in smoke and 'angles' in smoke:
                commands = FileUtils.generate_cs2_commands(
                    smoke['throw_position'], 
                    smoke['angles']
                )
                cfg_lines.append(commands['combined'])
            
            cfg_lines.append("")
        
        return "\n".join(cfg_lines)


class PerformanceTimer:
    """Таймер для измерения производительности"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        elapsed = self.end_time - self.start_time
        print(f"⏱️  {self.name}: {elapsed:.3f} секунд")
    
    def get_elapsed(self) -> float:
        """Получение прошедшего времени"""
        if self.start_time is None:
            return 0.0
        if self.end_time is None:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time


class Logger:
    """Простой логгер для проекта"""
    
    @staticmethod
    def info(message: str):
        print(f"ℹ️  {message}")
    
    @staticmethod
    def success(message: str):
        print(f"✅ {message}")
    
    @staticmethod
    def warning(message: str):
        print(f"⚠️  {message}")
    
    @staticmethod
    def error(message: str):
        print(f"❌ {message}")
    
    @staticmethod
    def debug(message: str):
        print(f"🐛 {message}")


# Экспорт основных функций для удобства
def ensure_dir(path: Union[str, Path]) -> Path:
    """Создание директории если не существует"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_vector(vector: List[float], precision: int = 2) -> str:
    """Форматирование вектора для вывода"""
    return f"[{', '.join(f'{v:.{precision}f}' for v in vector)}]"


def validate_position(position: List[float]) -> bool:
    """Проверка корректности позиции"""
    if len(position) != 3:
        return False
    
    # Проверяем что это числа и они в разумных пределах
    for coord in position:
        if not isinstance(coord, (int, float)):
            return False
        if abs(coord) > 10000:  # Не может быть больше 10 км
            return False
    
    return True


# Глобальный экземпляр путей для удобства
project_paths = ProjectPaths()

# Создаем алиасы для часто используемых функций
save_to_json = FileUtils.save_json
load_from_json = FileUtils.load_json
calculate_distance = MathUtils.distance
meters_to_units = CS2CoordinateConverter.meters_to_units
units_to_meters = CS2CoordinateConverter.units_to_meters


if __name__ == "__main__":
    """Тестирование утилит"""
    print("🧪 Тестирование utils.py")
    
    # Тест путей
    print(f"\n📁 Пути проекта:")
    print(f"   Корень: {project_paths.project_root}")
    print(f"   Карты: {project_paths.maps_dir}")
    print(f"   Выходные данные: {project_paths.outputs_dir}")
    
    # Тест конвертера координат
    print(f"\n📏 Конвертер координат:")
    print(f"   1 метр = {CS2CoordinateConverter.UNITS_PER_METER:.2f} юнитов")
    test_pos = [10.0, 5.0, 1.5]
    units = CS2CoordinateConverter.vector_meters_to_units(test_pos)
    print(f"   Позиция {test_pos} м = {units} юнитов")
    
    # Тест математических утилит
    print(f"\n🧮 Математические утилиты:")
    dist = MathUtils.distance([0, 0, 0], [3, 4, 0])
    print(f"   Расстояние (0,0,0) до (3,4,0) = {dist:.2f}")
    
    # Тест производительности
    print(f"\n⏱️  Таймер производительности:")
    with PerformanceTimer("Тестовая операция"):
        time.sleep(0.1)
    
    print("\n✅ Все утилиты работают!")