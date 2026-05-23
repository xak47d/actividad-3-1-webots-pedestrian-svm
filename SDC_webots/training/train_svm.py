# ============================================================
# Entrenamiento del SVM para detección de PEATONES (no vehículos).
#
# Cambios sobre el script original de detección de vehículos:
#  1. Dataset reemplazado por Penn-Fudan Pedestrian Database.
#  2. Las MUESTRAS POSITIVAS se obtienen recortando cada bounding box
#     anotado en PennFudanPed/Annotation/*.txt, no usando la imagen
#     completa. Así el SVM aprende la apariencia del peatón y no del
#     fondo de la escena.
#  3. Las MUESTRAS NEGATIVAS se obtienen recortando regiones aleatorias
#     de las mismas imágenes que NO se solapan con ningún bounding box
#     de peatón. Antes se usaban parches de ruido aleatorio, lo cual
#     hacía que el modelo no aprendiera a distinguir peatones de
#     escenas urbanas reales.
#  4. El reporte incluye matriz de confusión y classification_report
#     (mismo formato que el script original).
#
# Bibliografía consultada:
#  - Penn-Fudan Pedestrian Database (readme.txt incluido en el dataset).
#  - Dalal & Triggs, "Histograms of Oriented Gradients for Human
#    Detection", CVPR 2005.
# ============================================================

import os
import re
import random

import cv2
import joblib
import numpy as np
from PIL import Image
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

# ------------------------------------------------------------
# Rutas del dataset.
# ------------------------------------------------------------
dataset_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "PennFudanPed")
)
images_path = os.path.join(dataset_root, "PNGImages")
annotations_path = os.path.join(dataset_root, "Annotation")

print("Imágenes:    ", images_path)
print("Anotaciones: ", annotations_path)

# ------------------------------------------------------------
# Configuración HOG (debe coincidir con el detector en tiempo real).
# ------------------------------------------------------------
WINDOW_W = 64
WINDOW_H = 128

hog = cv2.HOGDescriptor()

# Negativos por imagen — controla el balance del dataset.
NEGATIVES_PER_IMAGE = 2

# Semilla para reproducibilidad de los recortes negativos.
random.seed(42)

# ------------------------------------------------------------
# Parser de bounding boxes del formato PASCAL del dataset.
# Línea ejemplo:
#   Bounding box for object 1 "PASpersonWalking" (Xmin, Ymin) ... : (160, 182) - (302, 431)
# ------------------------------------------------------------
bbox_re = re.compile(
    r"\((\d+),\s*(\d+)\)\s*-\s*\((\d+),\s*(\d+)\)"
)


def parse_bounding_boxes(annotation_file):
    boxes = []
    with open(annotation_file, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if "Bounding box" not in line:
                continue
            match = bbox_re.search(line)
            if not match:
                continue
            xmin, ymin, xmax, ymax = (int(v) for v in match.groups())
            boxes.append((xmin, ymin, xmax, ymax))
    return boxes


def boxes_overlap(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1)


def hog_features_from_crop(crop_rgb):
    gray = cv2.cvtColor(crop_rgb, cv2.COLOR_RGB2GRAY)
    resized = cv2.resize(gray, (WINDOW_W, WINDOW_H))
    return hog.compute(resized).flatten()


# ------------------------------------------------------------
# Construcción del dataset.
# ------------------------------------------------------------
data = []
labels = []
positive_count = 0
negative_count = 0
images_processed = 0

for filename in sorted(os.listdir(images_path)):
    if not filename.lower().endswith(".png"):
        continue

    image_file = os.path.join(images_path, filename)
    annotation_file = os.path.join(
        annotations_path,
        os.path.splitext(filename)[0] + ".txt"
    )

    if not os.path.exists(annotation_file):
        continue

    try:
        image = np.array(Image.open(image_file).convert("RGB"))
    except Exception as exc:
        print("No se pudo leer:", filename, exc)
        continue

    boxes = parse_bounding_boxes(annotation_file)
    if not boxes:
        continue

    img_h, img_w = image.shape[:2]

    # --- Positivos: cada bounding box recortado. ---
    for (xmin, ymin, xmax, ymax) in boxes:
        xmin = max(0, xmin)
        ymin = max(0, ymin)
        xmax = min(img_w, xmax)
        ymax = min(img_h, ymax)
        if xmax - xmin < 16 or ymax - ymin < 32:
            # Bounding box demasiado pequeño para ser útil.
            continue
        crop = image[ymin:ymax, xmin:xmax]
        data.append(hog_features_from_crop(crop))
        labels.append(1)
        positive_count += 1

    # --- Negativos: parches aleatorios que NO se solapan con ningún BBox. ---
    # Tamaño del parche proporcional al promedio de los bboxes positivos
    # para que las distribuciones de escala sean comparables.
    avg_w = max(WINDOW_W, sum(b[2] - b[0] for b in boxes) // len(boxes))
    avg_h = max(WINDOW_H, sum(b[3] - b[1] for b in boxes) // len(boxes))

    sampled = 0
    attempts = 0
    while sampled < NEGATIVES_PER_IMAGE and attempts < 30:
        attempts += 1
        if avg_w >= img_w or avg_h >= img_h:
            break
        nx = random.randint(0, img_w - avg_w)
        ny = random.randint(0, img_h - avg_h)
        candidate = (nx, ny, nx + avg_w, ny + avg_h)
        if any(boxes_overlap(candidate, b) for b in boxes):
            continue
        crop = image[ny:ny + avg_h, nx:nx + avg_w]
        data.append(hog_features_from_crop(crop))
        labels.append(0)
        negative_count += 1
        sampled += 1

    images_processed += 1

print("\nImágenes procesadas:", images_processed)
print("Muestras positivas:  ", positive_count)
print("Muestras negativas:  ", negative_count)
print("Total de muestras:   ", len(data))

# ------------------------------------------------------------
# División train/test y entrenamiento.
# ------------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    data,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels,
)

model = LinearSVC(max_iter=10000)
model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("\nMATRIZ DE CONFUSIÓN\n")
print(confusion_matrix(y_test, predictions))

print("\nREPORTE DE CLASIFICACIÓN\n")
print(classification_report(y_test, predictions, target_names=["No peatón", "Peatón"]))

# ------------------------------------------------------------
# Exportación del modelo entrenado.
# ------------------------------------------------------------
model_path = os.path.join(os.path.dirname(__file__), "svm_pedestrian_model.pkl")
joblib.dump(model, model_path)

print("\nMODELO GUARDADO EN:")
print(model_path)
