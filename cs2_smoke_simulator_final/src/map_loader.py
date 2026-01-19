"""
Загрузчик карт для CS2 Smoke Simulator
Конвертация из форматов CS2 в PyBullet
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
import trimesh
import pybullet as p

# Импортируем конфигурацию
from physics_config import CS2_PHYSICS


class MapLoader:
    """Загрузчик карт с поддержкой различных форматов"""
    
    def __init__(self, map_dir: str = "map"):
        """
        Инициализация загрузчика карт
        
        Args:
            map_dir: путь к папке с картами
        """
        self.map_dir = Path(map_dir)
        self.map_dir.mkdir(exist_ok=True)
        self.loaded_maps = {}  # Кэш загруженных карт
        
    def convert_cs2_to_bullet(self, position: List[float]) -> List[float]:
        """
        Конвертация координат CS2 → PyBullet
        
        CS2 система координат:
          X: восток (East)
          Y: север (North) 
          Z: вверх (Up)
          Единицы: дюймы
        
        PyBullet система координат:
          X: вправо (Right)
          Y: вверх (Up)
          Z: вперед (Forward)
          Единицы: метры
        
        Конвертация:
          1. Дюймы → метры (× 0.0254)
          2. Поворот осей: CS2 (X,Y,Z) → PyBullet (X,Z,Y)
        """
        scale = CS2_PHYSICS.meters_per_unit  # 0.0254 (дюймы → метры)
        
        if len(position) != 3:
            raise ValueError(f"Позиция должна содержать 3 координаты, получено: {len(position)}")
        
        x, y, z = position
        
        # Конвертация: CS2 (X-East, Y-North, Z-Up) → PyBullet (X-East, Z-North, Y-Up)
        return [
            x * scale,      # X: восток → восток
            z * scale,      # Y: вверх → вверх  
            y * scale       # Z: север → вперед
        ]
    
    def convert_bullet_to_cs2(self, position: List[float]) -> List[float]:
        """Обратная конвертация PyBullet → CS2"""
        scale = CS2_PHYSICS.units_per_meter  # 39.37 (метры → дюймы)
        
        x, y, z = position
        return [
            x * scale,      # X: восток → восток
            z * scale,      # Z: вперед → север
            y * scale       # Y: вверх → вверх
        ]
    
    def load_test_scene(self) -> int:
        """
        Создание тестовой сцены для отладки
        
        Returns:
            int: ID тела карты в PyBullet
        """
        print("🧪 Создание тестовой сцены...")
        
        # Создаем пол
        plane_id = p.createCollisionShape(p.GEOM_PLANE)
        plane_body = p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=plane_id
        )
        
        # Создаем несколько тестовых препятствий
        obstacles = [
            # Стена 1
            {"pos": [5, 0, 1.5], "size": [2, 0.2, 3], "color": [1, 0.5, 0, 1]},
            # Стена 2  
            {"pos": [-5, 5, 2], "size": [0.8, 3, 4], "color": [0.5, 1, 0, 1]},
            # Ящик
            {"pos": [0, -3, 0.5], "size": [1, 1, 1], "color": [0, 0.5, 1, 1]},
            # Платформа
            {"pos": [3, 4, 1], "size": [1.5, 1.5, 0.2], "color": [1, 1, 0, 1]},
        ]
        
        map_colliders = [plane_body]
        
        for obs in obstacles:
            # Конвертируем позицию в PyBullet координаты
            pos_bullet = self.convert_cs2_to_bullet(obs["pos"])
            size_bullet = [s * CS2_PHYSICS.meters_per_unit for s in obs["size"]]
            
            # Создаем коллизию
            col_shape = p.createCollisionShape(
                p.GEOM_BOX,
                halfExtents=size_bullet
            )
            
            # Создаем визуальную форму
            vis_shape = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=size_bullet,
                rgbaColor=obs["color"]
            )
            
            # Создаем тело
            body = p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=col_shape,
                baseVisualShapeIndex=vis_shape,
                basePosition=pos_bullet
            )
            
            map_colliders.append(body)
        
        print(f"✅ Тестовая сцена создана: {len(map_colliders)} объектов")
        return map_colliders
    
    def load_glb_file(self, filepath: str) -> Optional[List[int]]:
        """
        Загрузка карты из GLB/GLTF файла
        
        Args:
            filepath: путь к .glb/.gltf файлу
            
        Returns:
            List[int]: список ID тел карты в PyBullet
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"❌ Файл не найден: {filepath}")
            return None
        
        print(f"📁 Загрузка карты: {filepath.name}")
        
        try:
            # Загружаем меш через trimesh
            mesh = trimesh.load(filepath, force='mesh')
            
            if isinstance(mesh, trimesh.Trimesh):
                # Одиночный меш
                meshes = [mesh]
            elif isinstance(mesh, trimesh.Scene):
                # Сцена с несколькими мешами
                meshes = list(mesh.geometry.values())
            else:
                print(f"❌ Неподдерживаемый формат: {type(mesh)}")
                return None
            
            map_colliders = []
            
            for i, m in enumerate(meshes):
                # Экспортируем во временный OBJ
                temp_file = self.map_dir / f"temp_mesh_{i}.obj"
                m.export(temp_file)
                
                # Создаем коллизию из OBJ
                col_shape = p.createCollisionShape(
                    p.GEOM_MESH,
                    fileName=str(temp_file),
                    meshScale=[1, 1, 1],
                    flags=p.GEOM_FORCE_CONCAVE_TRIMESH
                )
                
                # Создаем тело
                body = p.createMultiBody(
                    baseMass=0,
                    baseCollisionShapeIndex=col_shape
                )
                
                map_colliders.append(body)
                
                # Удаляем временный файл
                temp_file.unlink(missing_ok=True)
            
            print(f"✅ Карта загружена: {len(map_colliders)} мешей")
            return map_colliders
            
        except Exception as e:
            print(f"❌ Ошибка загрузки GLB: {e}")
            return None
    
    def load_obj_file(self, filepath: str) -> Optional[List[int]]:
        """
        Загрузка карты из OBJ файла
        
        Args:
            filepath: путь к .obj файлу
            
        Returns:
            List[int]: список ID тел карты
        """
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"❌ Файл не найден: {filepath}")
            return None
        
        print(f"📁 Загрузка OBJ: {filepath.name}")
        
        try:
            # Создаем коллизию из OBJ
            col_shape = p.createCollisionShape(
                p.GEOM_MESH,
                fileName=str(filepath),
                meshScale=[1, 1, 1],
                flags=p.GEOM_FORCE_CONCAVE_TRIMESH
            )
            
            # Создаем тело
            body = p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=col_shape
            )
            
            print(f"✅ OBJ загружен")
            return [body]
            
        except Exception as e:
            print(f"❌ Ошибка загрузки OBJ: {e}")
            return None
    
    def load_map(self, map_name: str) -> Optional[List[int]]:
        """
        Автоматическая загрузка карты по имени
        
        Args:
            map_name: имя карты (например, "de_dust2")
            
        Returns:
            List[int]: список ID тел карты
        """
        # Проверяем кэш
        if map_name in self.loaded_maps:
            print(f"📂 Карта '{map_name}' уже загружена (из кэша)")
            return self.loaded_maps[map_name]
        
        # Пробуем различные форматы
        formats = [
            (f"{map_name}_physics.glb", self.load_glb_file),
            (f"{map_name}.glb", self.load_glb_file),
            (f"{map_name}_collision.obj", self.load_obj_file),
            (f"{map_name}.obj", self.load_obj_file),
            (f"{map_name}/world_physics.glb", self.load_glb_file),
        ]
        
        for filename, loader_func in formats:
            filepath = self.map_dir / filename
            if filepath.exists():
                result = loader_func(str(filepath))
                if result:
                    self.loaded_maps[map_name] = result
                    return result
        
        # Если файлы не найдены, создаем тестовую сцену
        print(f"⚠️ Карта '{map_name}' не найдена, создаем тестовую сцену")
        result = self.load_test_scene()
        self.loaded_maps[map_name] = result
        return result
    
    def get_map_info(self, map_name: str) -> Dict[str, Any]:
        """
        Получение информации о карте
        
        Args:
            map_name: имя карты
            
        Returns:
            Dict[str, Any]: информация о карте
        """
        info = {
            'name': map_name,
            'loaded': map_name in self.loaded_maps,
            'available_formats': [],
            'filepath': None
        }
        
        # Проверяем доступные форматы
        for fmt in ['.glb', '.obj']:
            patterns = [
                f"{map_name}_physics{fmt}",
                f"{map_name}{fmt}",
                f"{map_name}_collision{fmt}"
            ]
            
            for pattern in patterns:
                filepath = self.map_dir / pattern
                if filepath.exists():
                    info['available_formats'].append(fmt)
                    info['filepath'] = str(filepath)
                    break
        
        return info
    
    def clear_cache(self):
        """Очистка кэша загруженных карт"""
        self.loaded_maps.clear()
        print("🧹 Кэш карт очищен")


# Создаем глобальный экземпляр загрузчика
map_loader = MapLoader()


if __name__ == "__main__":
    print("🧪 Тестирование MapLoader")
    
    # Тест конвертации координат
    test_pos = [1000, 500, 128]  # CS2 координаты (дюймы)
    bullet_pos = map_loader.convert_cs2_to_bullet(test_pos)
    cs2_pos = map_loader.convert_bullet_to_cs2(bullet_pos)
    
    print(f"📏 Конвертация координат:")
    print(f"   CS2: {test_pos} → PyBullet: {bullet_pos}")
    print(f"   PyBullet: {bullet_pos} → CS2: {cs2_pos}")
    
    # Тест информации о картах
    test_maps = ["de_dust2", "de_inferno", "test_map"]
    for map_name in test_maps:
        info = map_loader.get_map_info(map_name)
        print(f"\n🗺️ Карта '{map_name}':")
        print(f"   Загружена: {info['loaded']}")
        print(f"   Доступные форматы: {info['available_formats']}")
        if info['filepath']:
            print(f"   Путь: {info['filepath']}")