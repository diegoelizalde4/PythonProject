import sys
import math
import numpy as np
import pygame

# Inicializacion del pygame y creacion de la ventana
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 20, 20)
GOLD = (245, 200, 0)

# Parametros para las vistas
FOCAL_LENGTH = 400
CAMERA_DISTANCE = 8

# Parametros para la generacion de la esfera
#Fi, theta para conversion a cordenadas cartesianas y creacion de la cuadricula
base_sphere = []
step_theta = 0.20
step_phi = 0.20
theta_values = np.arange(0, math.pi + step_theta, step_theta)
phi_values = np.arange(0, 2 * math.pi, step_phi)
radius = 2.0

for theta in theta_values:
    row = []
    for phi in phi_values:
        #Cordenadas cartesianas para la cuadricula
        x = radius * math.sin(theta) * math.cos(phi)
        y = radius * math.sin(theta) * math.sin(phi)
        z = radius * math.cos(theta)
        row.append([x, y, z])
    base_sphere.append(row)

rows = len(base_sphere)
cols = len(base_sphere[0])


# Copo de nieve, dibujamos un circulo y lo dividimos en 6 partes, hacemos lineas
#invisibles y dentro de estas lineas diujamos circulos pequenos para simular los copos
def create_snowflake(z_pos):
    flake = []
    for i in range(6):
        rad = math.radians(i * 60)
        for t in np.linspace(0, 1.5, 10):
            flake.append([t * math.cos(rad), t * math.sin(rad), z_pos])
        for side in [-1, 1]:
            brad = rad + side * math.radians(30)
            for t in np.linspace(0.5, 1.0, 5):
                flake.append([t * math.cos(brad), t * math.sin(brad), z_pos])
    return flake


snowflake = create_snowflake(2.01)


# Metodo de rotacion en x
def rotate_y(x, y, z, angle):
    rad = math.radians(angle)
    c, s = math.cos(rad), math.sin(rad)
    return x * c + z * s, y, -x * s + z * c


# Bucle pa que gire
running = True
frame = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    screen.fill(BLACK)
    angle_y = frame * 1.5

    # Listas temporales
    trans_3d = []
    proj_2d = []

    # 1. TRANSFORMAR PUNTOS
    for row in base_sphere:
        r_3d, r_2d = [], []
        for px, py, pz in row:
            # Rotar
            rx, ry, rz = rotate_y(px, py, pz, angle_y)
            r_3d.append((rx, ry, rz))

            # Proyectar
            if rz + CAMERA_DISTANCE != 0:
                f = FOCAL_LENGTH / (rz + CAMERA_DISTANCE)
                r_2d.append((int(rx * f + WIDTH / 2), int(-ry * f + HEIGHT / 2)))
            else:
                r_2d.append(None)
        trans_3d.append(r_3d)
        proj_2d.append(r_2d)

    # 2. PROCESAR poligonos
    polys = []
    # Vector de luz (fijo)
    lx, ly, lz = 0.5, -0.5, -1.0

    for i in range(rows - 1):
        for j in range(cols - 1):
            p1, p2 = trans_3d[i][j], trans_3d[i][j + 1]
            p3, p4 = trans_3d[i + 1][j + 1], trans_3d[i + 1][j]

            # Profundidad  (Z)
            avg_z = (p1[2] + p2[2] + p3[2] + p4[2]) / 4.0

            if avg_z < 0:  # Solo si está al frente
                vp1, vp2 = proj_2d[i][j], proj_2d[i][j + 1]
                vp3, vp4 = proj_2d[i + 1][j + 1], proj_2d[i + 1][j]

                if vp1 and vp2 and vp3 and vp4:


                    # Textura 1: Rayas Horizontale
                    if (i // 3) % 2 == 0:
                        base = list(RED)
                    else:
                        base = list(GOLD)

                    # TEXTURA 2: Patrón de "Diamantina" o Puntos
                    # Si la suma de indices es par, aclaramos el color
                    if (i + j) % 2 == 0:
                        # Aclaramos colores para el efecto
                        base[0] = min(255, base[0] + 30)
                        base[1] = min(255, base[1] + 30)
                        base[2] = min(255, base[2] + 30)

                    # sombreado

                    nx = (p1[0] + p2[0] + p3[0] + p4[0]) / 4
                    ny = (p1[1] + p2[1] + p3[1] + p4[1]) / 4
                    nz = (p1[2] + p2[2] + p3[2] + p4[2]) / 4

                    # Cálculos para el efecto de la luz
                    dot = (nx * lx + ny * ly + nz * lz)
                    light = max(0.2, (dot * 0.5) + 0.5)  # Luz base

                    # Especular, efecto
                    spec = 0
                    if light > 0.9: spec = 60

                    # Aplicar luz
                    r = int(min(255, base[0] * light + spec))
                    g = int(min(255, base[1] * light + spec))
                    b = int(min(255, base[2] * light + spec))

                    polys.append((avg_z, [vp1, vp2, vp3, vp4], (r, g, b)))

    # Mostrar las figuras
    polys.sort(key=lambda x: x[0], reverse=True)
    for _, pts, col in polys:
        pygame.draw.polygon(screen, col, pts)

    # Mostrar el copo
    for px, py, pz in snowflake:
        rx, ry, rz = rotate_y(px * 0.5, py * 0.5, pz, angle_y)
        if rz < 0:
            f = FOCAL_LENGTH / (rz + CAMERA_DISTANCE)
            pygame.draw.circle(screen, WHITE, (int(rx * f + WIDTH / 2), int(-ry * f + HEIGHT / 2)), 3)

    # Mostrar cordon
    cord_draw = []
    for t in np.linspace(0, 2, 10):
        cx, cy, cz = rotate_y(0, 2.0 + t, 0, angle_y)
        f = FOCAL_LENGTH / (cz + CAMERA_DISTANCE)
        cord_draw.append((int(cx * f + WIDTH / 2), int(-cy * f + HEIGHT / 2)))
    pygame.draw.lines(screen, GOLD, False, cord_draw, 4)

    pygame.display.flip()
    clock.tick(60)
    frame += 1

pygame.quit()
sys.exit()