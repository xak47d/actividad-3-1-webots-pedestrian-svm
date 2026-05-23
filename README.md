# Actividad 3.1 - Webots Pedestrian Detection with SVM

This repository contains the Webots implementation and deliverables for Activity 3.1, focused on pedestrian detection with HOG + SVM and vehicle response inside the Webots city world.

## Contents

- `SDC_webots/controllers/vehicle_controller/vehicle_controller.py`
  Main vehicle controller with lane following, LiDAR distance checks, HOG + SVM pedestrian detection, and optional car-camera recording.
- `SDC_webots/controllers/vehicle_controller/svm_pedestrian_model.pkl`
  Trained SVM model used by the controller.
- `SDC_webots/controllers/recording_supervisor/recording_supervisor.py`
  Supervisor used only for synchronized recording of the Webots main 3D view.
- `SDC_webots/worlds/city_2025a_activity_3_1.wbt`
  Normal activity world. The vehicle is configured for an external controller.
- `SDC_webots/worlds/city_2025a_activity_3_1_recording.wbt`
  Recording world. The same vehicle controller and recording supervisor run inside Webots so the main view and car camera are captured from the same simulation run.
- `run_webots_controller.sh` and `run_webots_controller.cmd`
  macOS/Linux and Windows helpers for running the external controller.
- `capture_synchronized_video.sh` and `capture_synchronized_video.cmd`
  macOS/Linux and Windows helpers for recording the main Webots view and the car camera at the same time.
- `compose_synchronized_overlay.py`
  Uses `ffmpeg` and `ffprobe` to retime the Webots main movie to the car-camera timeline and create the final picture-in-picture overlay.
- `media/Actividad_3_1_synchronized_overlay.mp4`
  Verified synchronized demo video.
- `Actividad 3.1 - Detección de Peatones con SVM.md`
  Original activity note.

## What the controller does

The controller implements the requested perception and response pipeline:

1. Captures the vehicle camera image.
2. Extracts HOG features from the camera image.
3. Uses the trained SVM model to classify pedestrian presence.
4. Reads front LiDAR distance.
5. Applies a confirmation counter before stopping for pedestrians.
6. Stops the vehicle and enables hazard flashers when a pedestrian is confirmed close enough.
7. Can record the car camera to MP4 when `WEBOTS_RECORD_CAMERA_PATH` is defined.

Gas tanks/oil barrels were removed from the activity world so the demonstration focuses on pedestrian detection.

## Requirements

- Webots R2025a or compatible.
- Python 3 with `venv`.
- Python packages listed in `requirements_webots.txt`.
- `ffmpeg` and `ffprobe` only if you want to regenerate the synchronized overlay video.

## Running on macOS or Linux

Create and activate a local environment:

```bash
python3 -m venv .venv-webots
source .venv-webots/bin/activate
pip install -r requirements_webots.txt
```

Open the normal world in Webots:

```bash
open SDC_webots/worlds/city_2025a_activity_3_1.wbt
```

Then run the external controller:

```bash
./run_webots_controller.sh
```

If Webots is installed somewhere other than `/Applications/Webots.app`, define `WEBOTS_HOME` first:

```bash
export WEBOTS_HOME="/Applications/Webots.app"
./run_webots_controller.sh
```

## Running on Windows

Create and activate a local environment from Command Prompt:

```bat
py -3 -m venv .venv-webots
.venv-webots\Scripts\activate
pip install -r requirements_webots.txt
```

Open this world in Webots:

```bat
SDC_webots\worlds\city_2025a_activity_3_1.wbt
```

Then run:

```bat
run_webots_controller.cmd
```

The Windows launcher checks common Webots install paths, including `C:\Program Files\Webots`. If your installation is elsewhere, set `WEBOTS_HOME` manually:

```bat
set WEBOTS_HOME=C:\Program Files\Webots
run_webots_controller.cmd
```

## Recording the synchronized demo video

The synchronized video must be captured from one simulation run. The recording world starts:

- the vehicle controller,
- the recording supervisor for the Webots main view,
- and optional camera recording inside `vehicle_controller.py`.

On macOS or Linux:

```bash
source .venv-webots/bin/activate
./capture_synchronized_video.sh
python compose_synchronized_overlay.py
```

On Windows:

```bat
.venv-webots\Scripts\activate
capture_synchronized_video.cmd
python compose_synchronized_overlay.py
```

The raw synchronized streams are written to:

- `media/Actividad_3_1_synchronized_main.mp4`
- `media/Actividad_3_1_synchronized_camera.mp4`

The final picture-in-picture video is written to:

- `media/Actividad_3_1_synchronized_overlay.mp4`

If Webots remains open after `Video creation finished`, close the Webots window normally. The important part is that both streams have already been written before composition.

## Notes

- The Penn-Fudan training image dataset is not included to keep the repository small. The trained `svm_pedestrian_model.pkl` required to run the controller is included.
- `scikit-learn==1.7.2` is pinned because the bundled model was trained with that version.
- `compose_synchronized_overlay.py` compensates for Webots writing the main movie at 25 FPS while the vehicle camera records at the 32 ms controller timestep.
