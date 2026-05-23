from vehicle import Driver
from controller import Camera, Lidar
import atexit
import cv2
import joblib
import math
import numpy as np
import os

# ============================================================
# ACTIVIDAD:
# Seguidor de línea con PID + detección de peatones con SVM
# + detección de obstáculos con LiDAR.
#
# En este código se agregó:
# - Uso de LiDAR Sick LMS 291.
# - Detección de peatones usando HOG + SVM.
# - Frenado de emergencia.
# - Encendido de intermitentes para barriles.
# ============================================================

TIME_STEP = 32

driver = Driver()

# ============================================================
# CÁMARA
# ============================================================
camera = driver.getDevice("camera")
camera.enable(TIME_STEP)

width = camera.getWidth()
height = camera.getHeight()

# Grabación opcional de la cámara del coche para componerla después
# sobre la vista principal sin depender de overlays de la UI de Webots.
record_camera_path = os.getenv("WEBOTS_RECORD_CAMERA_PATH", "").strip()
record_max_seconds_text = os.getenv("WEBOTS_RECORD_MAX_SECONDS", "").strip()
record_max_seconds = None
camera_video_writer = None

if record_max_seconds_text:
    try:
        record_max_seconds = float(record_max_seconds_text)
    except ValueError:
        print("WEBOTS_RECORD_MAX_SECONDS debe ser numerico:", record_max_seconds_text)


def close_camera_video_writer():
    global camera_video_writer

    if camera_video_writer is not None:
        camera_video_writer.release()
        camera_video_writer = None

if record_camera_path:
    camera_video_writer = cv2.VideoWriter(
        record_camera_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        1000.0 / TIME_STEP,
        (width, height)
    )

    if camera_video_writer.isOpened():
        atexit.register(close_camera_video_writer)
    else:
        print("No se pudo iniciar la grabacion de la camara:", record_camera_path)
        camera_video_writer = None

# ============================================================
# LIDAR
# ============================================================
# Se habilita el LiDAR frontal del vehículo.
# Este sensor ayudará a detectar obstáculos al frente.

lidar = driver.getDevice("Sick LMS 291")
lidar.enable(TIME_STEP)

# ============================================================
# MODELO SVM
# ============================================================
# Se carga el modelo previamente entrenado para detectar peatones.

model = joblib.load("svm_pedestrian_model.pkl")

# Descriptor HOG utilizado por el modelo SVM.
hog = cv2.HOGDescriptor()

# ============================================================
# VELOCIDAD DEL VEHÍCULO
# ============================================================
cruising_speed = 130.0
emergency_speed = 0.0

# ============================================================
# DISTANCIAS DE DETECCIÓN
# ============================================================
# Distancia máxima permitida por la actividad para detectar obstáculos.

max_obstacle_distance = 20.0

# Si un obstáculo está a esta distancia, se activa frenado.
emergency_distance = 12.0

# Distancia válida para considerar un peatón.
pedestrian_min_distance = 6.0
pedestrian_max_distance = 20.0

# ============================================================
# TIEMPOS DE ESPERA
# ============================================================
pedestrian_stop_time = 25
barrel_stop_time = 35

# Cooldowns para evitar múltiples frenados por el mismo objeto.
pedestrian_ignore_time = 80
barrel_ignore_time = 100

# ============================================================
# CONTROL PID
# ============================================================
# Parámetros PID del seguidor de línea.

Kp = 0.006
Ki = 0.00001
Kd = 0.003

previous_error = 0.0
integral = 0.0

# ============================================================
# VARIABLES GENERALES
# ============================================================
mode = "drive"
counter = 0

pedestrian_confirmations = 0
barrel_confirmations = 0

required_confirmations = 2

ignore_pedestrian_counter = 0
ignore_barrel_counter = 0

step_counter = 0

# ============================================================
# FUNCIÓN PARA DETECTAR PEATONES CON SVM
# ============================================================
def detect_pedestrian_with_svm(image_bgra):

    # Convertir imagen a formato BGR.
    img_bgr = cv2.cvtColor(image_bgra, cv2.COLOR_BGRA2BGR)

    # Convertir a escala de grises.
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Región de interés.
    # Solo se usa la parte inferior de la imagen.
    roi = gray[height // 3:height, :]

    # Redimensionar para que coincida con el tamaño esperado por HOG.
    resized = cv2.resize(roi, (64, 128))

    # Extraer características HOG.
    features = hog.compute(resized)

    # Predicción con el modelo SVM.
    prediction = model.predict([features.flatten()])

    return prediction[0] == 1

# ============================================================
# FUNCIÓN DE SEGUIDOR DE LÍNEA CON PID
# ============================================================
def line_following_pid(image_bgra):

    global previous_error
    global integral

    # Conversión a BGR.
    img_bgr = cv2.cvtColor(image_bgra, cv2.COLOR_BGRA2BGR)

    # Conversión a HSV.
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # Rango de amarillo para detectar la línea.
    lower_yellow = np.array([18, 80, 80])
    upper_yellow = np.array([40, 255, 255])

    # Máscara para detectar amarillo.
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    # Solo se usa la parte inferior de la imagen.
    roi = mask[int(height * 0.55):height, :]

    # Calcular momentos.
    moments = cv2.moments(roi)

    # Si se detecta línea.
    if moments["m00"] > 0:

        # Centro de la línea.
        cx = int(moments["m10"] / moments["m00"])

        # Centro de la imagen.
        image_center = width // 2

        # Error PID.
        error = cx - image_center

        # Integral.
        integral += error

        # Derivada.
        derivative = error - previous_error

        # Fórmula PID.
        steering = (
            (Kp * error) +
            (Ki * integral) +
            (Kd * derivative)
        )

        previous_error = error

        # Limitar dirección.
        steering = max(min(steering, 0.5), -0.5)

        return steering

    else:
        # Si no detecta línea, avanzar recto.
        return 0.0

# ============================================================
# FUNCIÓN PARA LEER LIDAR
# ============================================================
def get_front_lidar_distance():

    ranges = lidar.getRangeImage()

    if not ranges:
        return float("inf")

    total_points = len(ranges)

    # Centro del LiDAR.
    center = total_points // 2

    # Aproximadamente 30 grados frontales.
    angle_width = total_points // 12

    # Zona frontal.
    front_zone = ranges[
        center - angle_width:
        center + angle_width
    ]

    valid_distances = []

    for d in front_zone:

        # Validar lecturas correctas.
        if math.isfinite(d) and 0.1 < d <= max_obstacle_distance:
            valid_distances.append(d)

    # Regresar distancia mínima detectada.
    if valid_distances:
        return min(valid_distances)

    return float("inf")

# ============================================================
# BUCLE PRINCIPAL
# ============================================================
while driver.step() != -1:

    step_counter += 1

    image = camera.getImage()

    if not image:
        continue

    # Convertir imagen a numpy array.
    image_bgra = np.frombuffer(
        image,
        np.uint8
    ).reshape((height, width, 4))

    # Liberar freno por defecto.
    try:
        driver.setBrakeIntensity(0.0)
    except:
        pass

    # ========================================================
    # PID
    # ========================================================
    steering_angle = line_following_pid(image_bgra)

    # ========================================================
    # LIDAR
    # ========================================================
    front_distance = get_front_lidar_distance()

    # ========================================================
    # SVM
    # ========================================================
    pedestrian_detected = detect_pedestrian_with_svm(image_bgra)

    # ========================================================
    # COOLDOWNS
    # ========================================================
    if ignore_pedestrian_counter > 0:
        ignore_pedestrian_counter -= 1
        pedestrian_detected = False

    if ignore_barrel_counter > 0:
        ignore_barrel_counter -= 1

    # ========================================================
    # VALIDACIÓN DE OBJETOS
    # ========================================================
    obstacle_detected = (
        front_distance <= emergency_distance
    )

    # Si LiDAR detecta obstáculo y SVM confirma peatón.
    valid_pedestrian = (
        obstacle_detected and
        pedestrian_detected and
        pedestrian_min_distance <= front_distance <= pedestrian_max_distance
    )

    # En esta variante del mundo ya no hay barriles, por lo que se desactiva
    # esa rama de decisión para evitar falsos positivos del SVM/LiDAR.
    valid_barrel = False

    # ========================================================
    # CONFIRMACIONES
    # ========================================================
    # Se usan confirmaciones para evitar falsos positivos.

    if valid_pedestrian:
        pedestrian_confirmations += 1
    else:
        pedestrian_confirmations = 0

    if valid_barrel:
        barrel_confirmations += 1
    else:
        barrel_confirmations = 0

    confirmed_pedestrian = (
        pedestrian_confirmations >= required_confirmations
    )

    confirmed_barrel = (
        barrel_confirmations >= required_confirmations
    )

    # ========================================================
    # DEBUG
    # ========================================================
    if step_counter % 30 == 0:

        print(
            "Modo:", mode,
            "| Distancia:", round(front_distance, 2),
            "| SVM:", pedestrian_detected,
            "| Peaton:", confirmed_pedestrian,
            "| Barril:", confirmed_barrel
        )

    # ========================================================
    # ESTADOS DEL VEHÍCULO
    # ========================================================

    # ========================================================
    # PEATÓN
    # ========================================================
    if mode == "pedestrian_stop":
        driver.setHazardFlashers(False)

        driver.setCruisingSpeed(emergency_speed)

        driver.setSteeringAngle(steering_angle)

        try:
            driver.setBrakeIntensity(1.0)
        except:
            pass

        counter -= 1

        # Después del tiempo de espera continúa.
        if counter <= 0:

            mode = "drive"

            pedestrian_confirmations = 0

            ignore_pedestrian_counter = pedestrian_ignore_time

    # ========================================================
    # BARRIL
    # ========================================================
    elif mode == "barrel_stop":
        # Encender intermitentes.
        driver.setHazardFlashers(True)

        driver.setCruisingSpeed(emergency_speed)

        driver.setSteeringAngle(steering_angle)

        try:
            driver.setBrakeIntensity(1.0)
        except:
            pass

        counter -= 1

        # Cuando desaparezca el barril continúa.
        if counter <= 0 or front_distance > emergency_distance:

            mode = "drive"

            barrel_confirmations = 0

            ignore_barrel_counter = barrel_ignore_time

    # ========================================================
    # DETECCIÓN DE PEATÓN
    # ========================================================
    elif confirmed_pedestrian:

        print("PEATÓN DETECTADO")

        mode = "pedestrian_stop"

        counter = pedestrian_stop_time

        driver.setHazardFlashers(False)

        driver.setCruisingSpeed(emergency_speed)

        driver.setSteeringAngle(steering_angle)

        try:
            driver.setBrakeIntensity(1.0)
        except:
            pass

    # ========================================================
    # DETECCIÓN DE BARRIL
    # ========================================================
    elif confirmed_barrel:

        print("BARRIL DETECTADO")

        mode = "barrel_stop"

        counter = barrel_stop_time

        driver.setHazardFlashers(True)

        driver.setCruisingSpeed(emergency_speed)

        driver.setSteeringAngle(steering_angle)

        try:
            driver.setBrakeIntensity(1.0)
        except:
            pass

    # ========================================================
    # CONDUCCIÓN NORMAL
    # ========================================================
    else:
        mode = "drive"

        driver.setHazardFlashers(False)

        try:
            driver.setBrakeIntensity(0.0)
        except:
            pass

        driver.setCruisingSpeed(cruising_speed)

        driver.setSteeringAngle(steering_angle)

    if camera_video_writer is not None:
        recorded_frame = cv2.cvtColor(image_bgra, cv2.COLOR_BGRA2BGR)

        distance_text = "inf" if not math.isfinite(front_distance) else f"{front_distance:.2f} m"
        overlay_lines = [
            f"t={step_counter * TIME_STEP / 1000.0:05.2f}s",
            f"modo={mode}",
            f"dist={distance_text}"
        ]

        cv2.rectangle(recorded_frame, (6, 6), (154, 72), (0, 0, 0), -1)
        cv2.rectangle(recorded_frame, (6, 6), (154, 72), (0, 255, 255), 1)

        for idx, text in enumerate(overlay_lines):
            cv2.putText(
                recorded_frame,
                text,
                (12, 28 + (idx * 18)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

        camera_video_writer.write(recorded_frame)

        elapsed_seconds = step_counter * TIME_STEP / 1000.0
        if record_max_seconds is not None and elapsed_seconds >= record_max_seconds:
            close_camera_video_writer()
            break

close_camera_video_writer()
