# Actividad 3.1 - Detección de Peatones en Webots con SVM

Este repositorio contiene la implementación en Webots y los entregables de la Actividad 3.1, enfocada en la detección de peatones con HOG + SVM y la respuesta del vehículo dentro del mundo de ciudad de Webots.

## Contenido

- `SDC_webots/controllers/vehicle_controller/vehicle_controller.py`
  Controlador principal del vehículo con seguidor de línea PID, lectura de distancia con LiDAR, detección de peatones HOG + SVM mediante **Sliding Window Search multi-escala**, frenado de emergencia (con luces intermitentes para barriles, sin intermitentes para peatones) y grabación opcional de la cámara del auto.
- `SDC_webots/controllers/vehicle_controller/svm_pedestrian_model.pkl`
  Modelo SVM entrenado que usa el controlador (HOG, ventana de 64x128).
- `SDC_webots/controllers/supervisor_controller/supervisor_controller.py`
  Supervisor que coloca periódicamente un barril de aceite frente al vehículo y lo retira segundos después. Provisto por el profesor y utilizado sin modificaciones, según las instrucciones de la actividad.
- `SDC_webots/controllers/recording_supervisor/recording_supervisor.py`
  Supervisor utilizado únicamente para la grabación sincronizada de la vista 3D principal de Webots. Llama a `simulationQuit` cuando termina la grabación para que la app de Webots se cierre limpiamente.
- `SDC_webots/training/train_svm.py`
  Entrena el modelo HOG + LinearSVC. Las muestras positivas se obtienen recortando los bounding boxes anotados de Penn-Fudan; las negativas son parches aleatorios que no se solapan con ningún bounding box (sin ruido sintético).
- `SDC_webots/worlds/city_2025a_activity_3_1.wbt`
  Mundo de la actividad. Incluye peatones, un nodo `DEF BARREL OilBarrel` y un `Robot` que ejecuta `supervisor_controller`. El BmwX5 está configurado con controlador externo.
- `SDC_webots/worlds/city_2025a_activity_3_1_recording.wbt`
  Mundo de grabación. El mismo vehículo y el supervisor de grabación se ejecutan dentro de Webots para que la vista principal y la cámara del auto se capturen en el mismo run de simulación.
- `run_activity_3_1.sh` y `run_activity_3_1.cmd`
  **Script todo-en-uno**: arma el venv, entrena el SVM si hace falta, copia el modelo al folder del controlador, abre Webots con el mundo correspondiente y lanza el controlador externo.
- `run_webots_controller.sh` y `run_webots_controller.cmd`
  Helpers de macOS/Linux y Windows para lanzar únicamente el controlador externo contra una instancia de Webots ya abierta.
- `capture_synchronized_video.sh` y `capture_synchronized_video.cmd`
  Helpers de macOS/Linux y Windows para grabar la vista principal de Webots y la cámara del auto al mismo tiempo (utilizan el mundo de grabación).
- `compose_synchronized_overlay.py`
  Usa `ffmpeg` y `ffprobe` para resincronizar la película principal con la línea de tiempo de la cámara y generar el overlay picture-in-picture final.
- `update_docx.py`
  Regenera las secciones modificables del entregable `.docx` (matriz de confusión, código actual, declaración de IA, subsección del supervisor) a partir del estado vigente del código.
- `media/Actividad_3_1_synchronized_overlay.mp4`
  Video demo sincronizado, verificado.
- `Actividad 3.1 - Detección de Peatones con SVM.md`
  Nota original de la actividad.

## Lo que hace el controlador

El controlador implementa el pipeline de percepción y respuesta solicitado:

1. Captura la imagen de la cámara del vehículo (256x128).
2. Ejecuta el seguidor de línea PID sobre una máscara HSV amarilla de la parte inferior de la imagen.
3. Lee el LiDAR frontal (Sick LMS 291), restringido a un cono de ~30 grados y 20 m de rango.
4. Corre la detección de peatones HOG + SVM con una ventana deslizante multi-escala sobre la región de interés inferior (las ventanas se procesan en una sola llamada a `predict`).
5. Requiere N confirmaciones consecutivas antes de clasificar un obstáculo para evitar falsos positivos.
6. Si el LiDAR ve un obstáculo cercano Y el SVM confirma un peatón: frenado de emergencia, **sin** intermitentes, espera hasta que el obstáculo se libere.
7. Si el LiDAR ve un obstáculo cercano pero el SVM **no** lo confirma como peatón: se trata como barril, frenado de emergencia, **se encienden los intermitentes**, espera hasta que el barril desaparezca.
8. En cualquier otro caso: avanza a la velocidad crucero y sigue la línea.
9. Opcionalmente escribe el feed de cámara a MP4 cuando `WEBOTS_RECORD_CAMERA_PATH` está definido.

## Requisitos

- Webots R2025a o compatible.
- Python 3 con `venv`.
- Paquetes Python listados en `requirements_webots.txt`.
- `ffmpeg` y `ffprobe` solo si quieres regenerar el video overlay sincronizado.

## Inicio rápido (todo-en-uno)

La ruta más simple es el launcher todo-en-uno. Crea el venv, re-entrena el SVM solo si hace falta, copia el modelo al controlador, abre Webots con el mundo de la actividad y arranca el controlador externo:

```bash
./run_activity_3_1.sh
```

Banderas útiles:

```bash
./run_activity_3_1.sh --retrain          # fuerza el re-entrenamiento del SVM
./run_activity_3_1.sh --no-webots        # solo prepara/entrena, no abre Webots
./run_activity_3_1.sh --record           # usa el mundo de grabación y captura videos sincronizados
./run_activity_3_1.sh --world recording  # abre el mundo de grabación manualmente
```

En Windows el equivalente es `run_activity_3_1.cmd` con las mismas banderas.

El launcher selecciona automáticamente un puerto libre y ata el controlador externo a esa instancia vía `WEBOTS_CONTROLLER_URL`, de modo que se puede ejecutar incluso con otra instancia de Webots ya abierta en el puerto 1234 sin colisiones.

El dataset Penn-Fudan debe estar disponible para que el paso de entrenamiento encuentre las muestras positivas. Por defecto el script lo busca en `SDC_webots/PennFudanPed/`; se puede sobreescribir con `PENNFUDAN_DIR=/ruta/a/PennFudanPed`.

## Flujo manual (macOS o Linux)

Crear y activar un entorno local:

```bash
python3 -m venv .venv-webots
source .venv-webots/bin/activate
pip install -r requirements_webots.txt
```

Abrir el mundo de la actividad en Webots:

```bash
open SDC_webots/worlds/city_2025a_activity_3_1.wbt
```

Luego correr el controlador externo:

```bash
./run_webots_controller.sh
```

Si Webots está instalado en una ruta distinta a `/Applications/Webots.app`, define primero `WEBOTS_HOME`:

```bash
export WEBOTS_HOME="/Applications/Webots.app"
./run_webots_controller.sh
```

## Entrenamiento del SVM

El modelo que se distribuye en `SDC_webots/controllers/vehicle_controller/svm_pedestrian_model.pkl` está entrenado con el dataset Penn-Fudan, usando recortes de bounding boxes como positivos y parches no solapados como negativos. Para re-entrenarlo localmente:

```bash
source .venv-webots/bin/activate
cd SDC_webots/training
python train_svm.py
cp svm_pedestrian_model.pkl ../controllers/vehicle_controller/svm_pedestrian_model.pkl
```

El script imprime la matriz de confusión y el `classification_report` que se usan en el video del entregable. Último entrenamiento (170 imágenes): 420 positivos / 239 negativos, ~97% de exactitud.

## Ejecución en Windows

Crear y activar el entorno local desde el Símbolo del sistema:

```bat
py -3 -m venv .venv-webots
.venv-webots\Scripts\activate
pip install -r requirements_webots.txt
```

Abrir el mundo en Webots:

```bat
SDC_webots\worlds\city_2025a_activity_3_1.wbt
```

Luego correr:

```bat
run_webots_controller.cmd
```

El launcher de Windows revisa rutas comunes de instalación de Webots, incluyendo `C:\Program Files\Webots`. Si tu instalación está en otra parte, define `WEBOTS_HOME` manualmente:

```bat
set WEBOTS_HOME=C:\Program Files\Webots
run_webots_controller.cmd
```

## Grabación del video demo sincronizado

La forma recomendada es usar el launcher todo-en-uno con `--record`:

```bash
./run_activity_3_1.sh --record
```

Esto, en una sola ejecución:

- Abre Webots con el mundo de grabación (que ejecuta el `vehicle_controller` como controlador INTERNO de Webots para mantener sincronizadas la cámara y la vista 3D).
- Graba simultáneamente la vista principal y el feed de la cámara del auto.
- Cierra Webots automáticamente cuando termina la grabación (`recording_supervisor` llama a `simulationQuit`).
- Compone el overlay picture-in-picture con `ffmpeg` y `ffprobe`.

Las variables de entorno que se pueden ajustar antes del `--record`:

- `WEBOTS_RECORD_MAX_SECONDS` (default `30`): duración de la grabación.
- `WEBOTS_RECORD_MAIN_QUALITY` (default `50`): calidad de la película principal. Se baja respecto al valor por defecto de Webots para evitar el error `libx264: 2pass curve failed to converge` en escenas casi estáticas.

Los streams sincronizados se escriben en:

- `media/Actividad_3_1_synchronized_main.mp4`
- `media/Actividad_3_1_synchronized_camera.mp4`

El video picture-in-picture final se escribe en:

- `media/Actividad_3_1_synchronized_overlay.mp4`

Alternativamente, los helpers heredados `capture_synchronized_video.sh` / `.cmd` siguen funcionando si prefieres invocar las piezas por separado y luego correr `python compose_synchronized_overlay.py` a mano.

## Actualización del entregable `.docx`

El entregable principal (`Actividad_3.1_Detección_de_Peatones_Equipo19.docx`) vive fuera del repositorio (en la carpeta de iCloud de los entregables), pero el script `update_docx.py` lo regenera de forma idempotente a partir del estado vigente del código:

```bash
./.venv-webots/bin/python update_docx.py
```

Re-emplaza el bloque de código del controlador, inyecta la matriz de confusión real, actualiza la descripción de la sección SVM (Sliding Window + Penn-Fudan), añade la subsección del supervisor de barriles y la declaración obligatoria de uso de IA, y deja el placeholder del enlace de YouTube. Se guarda un backup `*_backup_pre_update.docx` junto al original antes de cualquier modificación.

## Notas

- El dataset de imágenes de entrenamiento Penn-Fudan no se incluye para mantener el repositorio pequeño. El `svm_pedestrian_model.pkl` ya entrenado, necesario para correr el controlador, sí está incluido.
- `scikit-learn==1.7.2` está pineado porque el modelo distribuido se entrenó con esa versión.
- `compose_synchronized_overlay.py` compensa el hecho de que Webots escribe la película principal a 25 FPS mientras la cámara del vehículo graba al timestep del controlador (32 ms).
- El detector con ventana deslizante evalúa ~63 ventanas candidatas por frame en 3 escalas y las procesa en una sola llamada a `LinearSVC.predict` para mantener bajo el costo por paso del controlador (32 ms).
- La distinción entre peatón y barril se hace combinando la salida del SVM con la proximidad del LiDAR: obstáculo cercano + SVM positivo = peatón (sin intermitentes); obstáculo cercano + SVM negativo = barril (con intermitentes).
