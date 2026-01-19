import pybullet as p
import os
import trimesh
import time

# Запуск физического движка
physicsClient = p.connect(p.GUI)
p.setGravity(0, 0, -800)  # Гравитация как в CS2
p.setTimeStep(1 / 120)

# Путь к файлу карты
map_glb_path = os.path.join("map", "de_palacio_d_physics.glb")

if not os.path.exists(map_glb_path):
    print("Ошибка: Файл карты не найден:", map_glb_path)
    p.disconnect()
    exit()

print("Загружаем карту...")

# Загрузка GLB и конвертация в тримеш
mesh = trimesh.load(map_glb_path, force="mesh")

# Экспорт во временный OBJ
temp_obj_path = "map/temp_map.obj"
mesh.export(temp_obj_path)

# Создание коллизионной формы
map_collision = p.createCollisionShape(
    shapeType=p.GEOM_MESH,
    fileName=temp_obj_path,
    meshScale=[1, 1, 1],
    flags=p.GEOM_FORCE_CONCAVE_TRIMESH
)

# Создание визуальной формы
map_visual = p.createVisualShape(
    shapeType=p.GEOM_MESH,
    fileName=temp_obj_path,
    meshScale=[1, 1, 1]
)

# Создание статичного тела карты
map_body = p.createMultiBody(
    baseMass=0,
    baseCollisionShapeIndex=map_collision,
    baseVisualShapeIndex=map_visual,
    basePosition=[0, 0, 0]
)

print("Карта загружена!")

# Создание тестовой гранаты
radius = 2.0

grenade_col = p.createCollisionShape(
    shapeType=p.GEOM_SPHERE,
    radius=radius
)

grenade_vis = p.createVisualShape(
    shapeType=p.GEOM_SPHERE,
    radius=radius,
    rgbaColor=[0, 1, 0, 1]  # Зелёный цвет
)

grenade = p.createMultiBody(
    baseMass=1.0,
    baseCollisionShapeIndex=grenade_col,
    baseVisualShapeIndex=grenade_vis,
    basePosition=[0, 0, 300]  # Бросаем сверху
)

# Настройка физики гранаты
p.changeDynamics(
    grenade,
    -1,
    restitution=0.1,     # Коэффициент отскока
    linearDamping=0.05   # Сопротивление воздуха
)

print("Граната создана, симуляция запущена. Нажмите Ctrl+C для остановки.")

# Запуск симуляции
try:
    while True:
        p.stepSimulation()
        time.sleep(1. / 120.)
except KeyboardInterrupt:
    print("\nСимуляция остановлена.")
finally:
    p.disconnect()
    print("Физический сервер отключён.")
