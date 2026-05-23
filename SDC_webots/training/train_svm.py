import cv2
import os
import numpy as np
from PIL import Image
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

dataset_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "PennFudanPed", "PNGImages")
)

print("Leyendo imágenes desde:", dataset_path)

hog = cv2.HOGDescriptor()

data = []
labels = []

for filename in os.listdir(dataset_path):
    if not filename.lower().endswith(".png"):
        continue

    image_path = os.path.join(dataset_path, filename)

    try:
        image = Image.open(image_path).convert("RGB")
        image = image.resize((64, 128))
        image = np.array(image)
    except Exception as e:
        print("No se pudo leer:", filename, e)
        continue

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    features = hog.compute(gray)

    data.append(features.flatten())
    labels.append(1)

print("Imágenes positivas cargadas:", labels.count(1))

for i in range(labels.count(1)):
    blank = np.random.randint(0, 255, (128, 64), dtype=np.uint8)
    features = hog.compute(blank)

    data.append(features.flatten())
    labels.append(0)

print("Imágenes negativas generadas:", labels.count(0))
print("Total de muestras:", len(data))

X_train, X_test, y_train, y_test = train_test_split(
    data,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels
)

model = LinearSVC(max_iter=10000)
model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("\nMATRIZ DE CONFUSIÓN\n")
print(confusion_matrix(y_test, predictions))

print("\nREPORTE DE CLASIFICACIÓN\n")
print(classification_report(y_test, predictions))

model_path = os.path.join(os.path.dirname(__file__), "svm_pedestrian_model.pkl")
joblib.dump(model, model_path)

print("\nMODELO GUARDADO EN:")
print(model_path)