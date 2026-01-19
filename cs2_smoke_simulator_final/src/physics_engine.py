"""
Enhanced Physics Engine for CS2 Smoke Simulator
Объединенная версия с лучшими возможностями обеих реализаций
"""

import pybullet as p
import pybullet_data
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import time
import trimesh
from pathlib import Path

from physics_config import ThrowType, CS2_PHYSICS
from map_loader import MapLoader


class EnhancedPhysicsEngine:
    """Улучшенный физический движок на базе PyBullet"""
    
    def __init__(self, 
                 map_name: Optional[str] = None,
                 gui: bool = False):
        """
        Инициализация физического движка
        
        Args:
            map_name: Имя карты для загрузки (None = тестовая сцена)
            gui: Показывать GUI PyBullet
        """
        # Подключение к PyBullet
        self.physics_client = p.connect(p.GUI if gui else p.DIRECT)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        
        # Настройка физики
        p.setGravity(0, 0, -CS2_PHYSICS.gravity)
        p.setTimeStep(CS2_PHYSICS.time_step)
        
        # Инициализация загрузчика карт
        self.map_loader = MapLoader()
        self.map_bodies = []
        
        # Загрузка карты
        if map_name:
            self.load_map(map_name)
        else:
            self.load_test_scene()
        
        self.gui = gui
        print(f"✅ Physics engine initialized (GUI: {gui})")
    
    def load_map(self, map_name: str) -> bool:
        """
        Загрузить карту по имени
        
        Args:
            map_name: Имя карты (например, "de_dust2")
            
        Returns:
            True если успешно загружено
        """
        print(f"📦 Loading map: {map_name}")
        
        try:
            # Используем MapLoader для загрузки
            self.map_bodies = self.map_loader.load_map(map_name)
            
            if self.map_bodies:
                # Настройка физических свойств поверхности
                for body_id in self.map_bodies:
                    p.changeDynamics(
                        body_id,
                        -1,
                        restitution=CS2_PHYSICS.grenade_restitution,
                        lateralFriction=CS2_PHYSICS.grenade_friction
                    )
                
                print(f"   ✅ Map loaded: {len(self.map_bodies)} bodies")
                return True
            else:
                print("   ⚠️  Map loading failed, creating test scene")
                return self.load_test_scene()
                
        except Exception as e:
            print(f"   ❌ Error loading map: {e}")
            return self.load_test_scene()
    
    def load_test_scene(self) -> bool:
        """Загрузить тестовую сцену"""
        print("🧪 Creating test scene...")
        self.map_bodies = self.map_loader.load_test_scene()
        
        # Настройка физических свойств
        for body_id in self.map_bodies:
            p.changeDynamics(
                body_id,
                -1,
                restitution=CS2_PHYSICS.grenade_restitution,
                lateralFriction=CS2_PHYSICS.grenade_friction
            )
        
        return True
    
    def simulate_throw(self, 
                      start_pos: np.ndarray,
                      pitch: float,
                      yaw: float,
                      throw_type: ThrowType,
                      max_time: float = 3.0) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """
        Симулировать бросок гранаты с заданными углами
        
        Args:
            start_pos: Начальная позиция в CS2 координатах [x, y, z]
            pitch: Угол вверх/вниз (градусы)
            yaw: Угол влево/вправо (градусы)
            throw_type: Тип броска
            max_time: Максимальное время симуляции (сек)
            
        Returns:
            (trajectory, info) где:
                trajectory - список позиций в CS2 координатах
                info - словарь с информацией о симуляции
        """
        # Конвертация позиции в PyBullet координаты
        start_bullet = self.map_loader.convert_cs2_to_bullet(start_pos.tolist())
        
        # Вычисление направления из углов
        pitch_rad = np.radians(pitch)
        yaw_rad = np.radians(yaw)
        
        # Направление в CS2 координатах (X-восток, Y-север, Z-вверх)
        direction_cs2 = np.array([
            np.cos(pitch_rad) * np.cos(yaw_rad),  # X
            np.cos(pitch_rad) * np.sin(yaw_rad),  # Y
            np.sin(pitch_rad)                      # Z
        ])
        
        # Конвертация направления (поворот осей)
        direction_bullet = np.array([
            direction_cs2[0],  # X остается
            direction_cs2[2],  # Z -> Y (вверх)
            direction_cs2[1]   # Y -> Z (вперед)
        ])
        
        # Получение скорости броска
        speed_cs2 = CS2_PHYSICS.get_throw_speed(throw_type)
        speed_bullet = speed_cs2 * CS2_PHYSICS.meters_per_unit
        
        # Создание гранаты
        grenade_shape = p.createCollisionShape(
            p.GEOM_SPHERE,
            radius=CS2_PHYSICS.grenade_radius
        )
        
        grenade_visual = p.createVisualShape(
            p.GEOM_SPHERE,
            radius=CS2_PHYSICS.grenade_radius,
            rgbaColor=[0, 1, 0, 1]
        )
        
        grenade_id = p.createMultiBody(
            baseMass=CS2_PHYSICS.grenade_mass,
            baseCollisionShapeIndex=grenade_shape,
            baseVisualShapeIndex=grenade_visual,
            basePosition=start_bullet
        )
        
        # Настройка физических свойств
        p.changeDynamics(
            grenade_id,
            -1,
            restitution=CS2_PHYSICS.grenade_restitution,
            lateralFriction=CS2_PHYSICS.grenade_friction,
            linearDamping=CS2_PHYSICS.grenade_linear_damping,
            angularDamping=CS2_PHYSICS.grenade_angular_damping
        )
        
        # Начальный импульс
        velocity_bullet = direction_bullet * speed_bullet
        p.resetBaseVelocity(grenade_id, linearVelocity=velocity_bullet.tolist())
        
        # Симуляция
        trajectory_bullet = []
        trajectory_cs2 = []
        num_steps = int(max_time / CS2_PHYSICS.time_step)
        bounces = 0
        last_velocity_mag = speed_bullet
        
        for step in range(num_steps):
            p.stepSimulation()
            
            # Получение позиции
            pos_bullet, _ = p.getBasePositionAndOrientation(grenade_id)
            trajectory_bullet.append(np.array(pos_bullet))
            
            # Конвертация обратно в CS2 координаты
            pos_cs2 = self.map_loader.convert_bullet_to_cs2(list(pos_bullet))
            trajectory_cs2.append(np.array(pos_cs2))
            
            # Проверка скорости для определения отскоков
            linear_vel, _ = p.getBaseVelocity(grenade_id)
            current_velocity_mag = np.linalg.norm(linear_vel)
            
            # Детекция отскока
            if abs(current_velocity_mag - last_velocity_mag) > (100 * CS2_PHYSICS.meters_per_unit):
                bounces += 1
            
            last_velocity_mag = current_velocity_mag
            
            # Остановка если граната остановилась
            if current_velocity_mag < (10 * CS2_PHYSICS.meters_per_unit) and step > 50:
                break
        
        # Финальная позиция
        final_pos_bullet, _ = p.getBasePositionAndOrientation(grenade_id)
        final_pos_cs2 = self.map_loader.convert_bullet_to_cs2(list(final_pos_bullet))
        
        final_vel, _ = p.getBaseVelocity(grenade_id)
        final_speed_cs2 = np.linalg.norm(final_vel) / CS2_PHYSICS.meters_per_unit
        
        # Удаление гранаты
        p.removeBody(grenade_id)
        
        # Информация о симуляции
        info = {
            'final_position': np.array(final_pos_cs2),
            'final_velocity': final_speed_cs2,
            'bounces': bounces,
            'simulation_time': step * CS2_PHYSICS.time_step,
            'trajectory_points': len(trajectory_cs2)
        }
        
        return trajectory_cs2, info
    
    def test_line_of_sight(self, 
                          pos1: np.ndarray, 
                          pos2: np.ndarray) -> bool:
        """
        Проверить прямую видимость между точками (в CS2 координатах)
        
        Args:
            pos1: Первая точка [x, y, z]
            pos2: Вторая точка [x, y, z]
            
        Returns:
            True если путь свободен
        """
        # Конвертация в PyBullet координаты
        pos1_bullet = self.map_loader.convert_cs2_to_bullet(pos1.tolist())
        pos2_bullet = self.map_loader.convert_cs2_to_bullet(pos2.tolist())
        
        result = p.rayTest(pos1_bullet, pos2_bullet)
        
        if result and len(result) > 0:
            hit_fraction = result[0][2]
            return hit_fraction >= 0.99
        
        return True
    
    def get_spawn_points(self, team: str = "t") -> List[np.ndarray]:
        """Получить точки спавна для команды (CS2 координаты)"""
        # TODO: Парсинг из entities.vents
        if team == "t":
            return [
                np.array([256.0, 640.0, 16.0]),
                np.array([300.0, 600.0, 16.0]),
            ]
        else:  # ct
            return [
                np.array([768.0, 640.0, 16.0]),
                np.array([800.0, 600.0, 16.0]),
            ]
    
    def get_bombsite_positions(self) -> Dict[str, np.ndarray]:
        """Получить позиции бомбсайтов (CS2 координаты)"""
        return {
            "A": np.array([500.0, 500.0, 16.0]),
            "B": np.array([700.0, 700.0, 16.0]),
        }
    
    def reset_simulation(self):
        """Сброс симуляции"""
        p.resetSimulation()
        p.setGravity(0, 0, -CS2_PHYSICS.gravity)
        p.setTimeStep(CS2_PHYSICS.time_step)
        
        # Перезагрузка карты
        if self.map_bodies:
            self.map_loader.clear_cache()
            self.load_test_scene()
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            p.disconnect(self.physics_client)
            print("✅ Physics engine cleaned up")
        except:
            pass
    
    def __del__(self):
        """Деструктор"""
        self.cleanup()


if __name__ == "__main__":
    print("=" * 60)
    print(" CS2 Physics Engine Test")
    print("=" * 60)
    
    # Создание движка с GUI для визуализации
    print("\n1. Creating physics engine...")
    engine = EnhancedPhysicsEngine(map_name=None, gui=False)
    
    # Тестовый бросок
    print("\n2. Testing grenade throw...")
    start_pos = np.array([0.0, 0.0, 200.0])  # CS2 координаты
    pitch = 30.0  # градусы
    yaw = 45.0    # градусы
    
    trajectory, info = engine.simulate_throw(
        start_pos, 
        pitch, 
        yaw, 
        ThrowType.LEFT_CLICK
    )
    
    print(f"\n📊 Simulation results:")
    print(f"   Trajectory points: {info['trajectory_points']}")
    print(f"   Simulation time: {info['simulation_time']:.2f}s")
    print(f"   Bounces: {info['bounces']}")
    print(f"   Final position: {info['final_position']}")
    print(f"   Final velocity: {info['final_velocity']:.1f} u/s")
    
    # Тест видимости
    print("\n3. Testing line of sight...")
    pos1 = np.array([0.0, 0.0, 50.0])
    pos2 = np.array([500.0, 500.0, 50.0])
    los = engine.test_line_of_sight(pos1, pos2)
    print(f"   Clear path: {los}")
    
    engine.cleanup()
    print("\n✅ Physics engine test complete!")
