"""
CS2 Smoke Finder - Intelligent Position Search
Поиск оптимальных позиций для броска смоков с разными стратегиями
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, asdict
import time
from enum import Enum

from physics_engine import EnhancedPhysicsEngine
from physics_config import ThrowType, CS2_PHYSICS


class SearchStrategy(Enum):
    """Стратегии поиска"""
    GRID_SEARCH = "GRID_SEARCH"
    GENETIC = "GENETIC"
    HYBRID = "HYBRID"


@dataclass
class SmokePosition:
    """Найденная позиция для броска смока"""
    throw_position: List[float]
    angles: Dict[str, float]
    throw_type: str
    target_position: List[float]
    landing_position: List[float]
    accuracy: float
    trajectory: List[List[float]]
    bounces: int
    cs2_commands: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        if self.cs2_commands is None:
            x, y, z = self.throw_position
            pitch = self.angles['pitch']
            yaw = self.angles['yaw']
            self.cs2_commands = {
                'setpos': f"setpos {x:.1f} {y:.1f} {z:.1f}",
                'setang': f"setang {pitch:.1f} {yaw:.1f} 0",
                'combined': f"setpos {x:.1f} {y:.1f} {z:.1f}; setang {pitch:.1f} {yaw:.1f} 0"
            }
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SmokeFinder:
    """Поиск оптимальных позиций для броска смоков"""
    
    def __init__(self, physics_engine: EnhancedPhysicsEngine):
        self.physics = physics_engine
        self.max_accuracy = 150.0
        self.search_radius = 500.0
        self.grid_step = 100.0
        print("✅ Smoke Finder initialized")
    
    def find_smokes(self, target_pos: np.ndarray, throw_type: ThrowType = ThrowType.LEFT_CLICK,
                   strategy: SearchStrategy = SearchStrategy.GENETIC, max_results: int = 10) -> List[SmokePosition]:
        print(f"\n🔍 Searching...")
        start_time = time.time()
        
        if strategy == SearchStrategy.GRID_SEARCH:
            solutions = self._grid_search(target_pos, throw_type, max_results)
        elif strategy == SearchStrategy.GENETIC:
            solutions = self._genetic_search(target_pos, throw_type, max_results)
        else:
            solutions = self._hybrid_search(target_pos, throw_type, max_results)
        
        print(f"✅ Found {len(solutions)} in {time.time()-start_time:.1f}s")
        return solutions
    
    def _grid_search(self, target_pos, throw_type, max_results):
        solutions = []
        center = target_pos.copy()
        center[2] = 72
        
        for x in np.arange(center[0]-self.search_radius, center[0]+self.search_radius, self.grid_step):
            for y in np.arange(center[1]-self.search_radius, center[1]+self.search_radius, self.grid_step):
                throw_pos = np.array([x, y, center[2]])
                delta = target_pos - throw_pos
                base_yaw = np.degrees(np.arctan2(delta[1], delta[0]))
                
                for pitch in np.linspace(-20, 60, 10):
                    try:
                        trajectory, info = self.physics.simulate_throw(throw_pos, pitch, base_yaw, throw_type, 2.0)
                        accuracy = np.linalg.norm(info['final_position'] - target_pos)
                        if accuracy < self.max_accuracy:
                            solutions.append(SmokePosition(
                                throw_position=throw_pos.tolist(),
                                angles={'pitch': pitch, 'yaw': base_yaw},
                                throw_type=throw_type.value,
                                target_position=target_pos.tolist(),
                                landing_position=info['final_position'].tolist(),
                                accuracy=float(accuracy),
                                trajectory=[p.tolist() for p in trajectory[::10]],
                                bounces=info['bounces']
                            ))
                    except:
                        pass
        
        solutions.sort(key=lambda s: s.accuracy)
        return solutions[:max_results]
    
    def _genetic_search(self, target_pos, throw_type, max_results):
        # Упрощенная версия для быстрой работы
        return self._grid_search(target_pos, throw_type, max_results)
    
    def _hybrid_search(self, target_pos, throw_type, max_results):
        return self._grid_search(target_pos, throw_type, max_results)


if __name__ == "__main__":
    physics = EnhancedPhysicsEngine(gui=False)
    finder = SmokeFinder(physics)
    target = np.array([500, 500, 50])
    solutions = finder.find_smokes(target, ThrowType.LEFT_CLICK, SearchStrategy.GRID_SEARCH, 5)
    for i, s in enumerate(solutions, 1):
        print(f"#{i}: {s.cs2_commands['combined']}")
    physics.cleanup()
