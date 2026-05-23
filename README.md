# Actividad 3.1 - Webots Pedestrian Detection with SVM

This repository contains the Webots implementation and deliverables for Activity 3.1, focused on pedestrian detection with HOG + SVM and vehicle response inside the Webots city world.

## Contents

- `SDC_webots/controllers/vehicle_controller/vehicle_controller.py`
  Main vehicle controller with PID lane following, LiDAR distance checks, HOG + SVM pedestrian detection using **multi-scale sliding-window search**, emergency braking (with hazard flashers for barrels, without for pedestrians), and optional car-camera recording.
- `SDC_webots/controllers/vehicle_controller/svm_pedestrian_model.pkl`
  Trained SVM model used by the controller (HOG features, 64x128 window).
- `SDC_webots/controllers/supervisor_controller/supervisor_controller.py`
  Supervisor that periodically spawns an oil barrel in front of the vehicle and removes it after a few steps. Provided unmodified per the activity instructions.
- `SDC_webots/controllers/recording_supervisor/recording_supervisor.py`
  Supervisor used only for synchronized recording of the Webots main 3D view.
- `SDC_webots/training/train_svm.py`
  Trains the HOG + LinearSVC model. Positives are cropped from the Penn-Fudan annotation bounding boxes; negatives are random non-overlapping patches from the same images (no synthetic noise).
- `SDC_webots/worlds/city_2025a_activity_3_1.wbt`
  Activity world. Includes pedestrians, a `DEF BARREL OilBarrel` node, and a `Robot` running `supervisor_controller`. The vehicle is configured for an external controller.
- `SDC_webots/worlds/city_2025a_activity_3_1_recording.wbt`
  Recording world. Same vehicle + recording supervisor run inside Webots so the main view and car camera are captured from the same simulation run.
- `run_activity_3_1.sh` and `run_activity_3_1.cmd`
  **All-in-one launcher**: sets up the venv, trains the SVM if needed, copies the model into the controller folder, launches Webots with the activity world, and starts the external controller.
- `run_webots_controller.sh` and `run_webots_controller.cmd`
  macOS/Linux and Windows helpers for running just the external controller against an already-open Webots window.
- `capture_synchronized_video.sh` and `capture_synchronized_video.cmd`
  macOS/Linux and Windows helpers for recording the main Webots view and the car camera at the same time (uses the recording world).
- `compose_synchronized_overlay.py`
  Uses `ffmpeg` and `ffprobe` to retime the Webots main movie to the car-camera timeline and create the final picture-in-picture overlay.
- `media/Actividad_3_1_synchronized_overlay.mp4`
  Verified synchronized demo video.
- `Actividad 3.1 - Detección de Peatones con SVM.md`
  Original activity note.

## What the controller does

The controller implements the requested perception and response pipeline:

1. Captures the vehicle camera image (256x128).
2. Runs the PID lane follower on a yellow HSV mask of the bottom of the image.
3. Reads the front LiDAR (Sick LMS 291), restricted to a ~30 degree cone and 20 m range.
4. Runs HOG + SVM pedestrian detection with a multi-scale sliding window over the bottom region of interest (windows are batched into a single `predict` call).
5. Requires N consecutive confirmations before classifying an obstacle to avoid false positives.
6. If the LiDAR sees a close obstacle AND the SVM confirms a pedestrian: emergency brake, **no hazard flashers**, wait until the obstacle clears.
7. If the LiDAR sees a close obstacle but the SVM does **not** confirm a pedestrian: treat it as a barrel, emergency brake, **enable hazard flashers**, wait until the barrel disappears.
8. Otherwise: cruise at the configured speed and follow the line.
9. Optionally writes the camera feed to MP4 when `WEBOTS_RECORD_CAMERA_PATH` is defined.

## Requirements

- Webots R2025a or compatible.
- Python 3 with `venv`.
- Python packages listed in `requirements_webots.txt`.
- `ffmpeg` and `ffprobe` only if you want to regenerate the synchronized overlay video.

## Quick start (all-in-one)

The simplest path is the all-in-one launcher. It creates the venv, retrains the SVM if needed, copies the model into the controller, opens Webots with the activity world, and starts the external controller:

```bash
./run_activity_3_1.sh
```

Useful flags:

```bash
./run_activity_3_1.sh --retrain          # force SVM retraining
./run_activity_3_1.sh --no-webots        # only prepare/train, don't open Webots
./run_activity_3_1.sh --record           # use recording world + capture sync videos
./run_activity_3_1.sh --world recording  # open the recording world manually
```

On Windows the equivalent is `run_activity_3_1.cmd` with the same flags.

The Penn-Fudan dataset must be available so the training step can find positives. By default the script looks in `SDC_webots/PennFudanPed/`; override with `PENNFUDAN_DIR=/path/to/PennFudanPed`.

## Manual workflow (macOS or Linux)

Create and activate a local environment:

```bash
python3 -m venv .venv-webots
source .venv-webots/bin/activate
pip install -r requirements_webots.txt
```

Open the activity world in Webots:

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

## Training the SVM

The model shipped in `SDC_webots/controllers/vehicle_controller/svm_pedestrian_model.pkl` is trained on the Penn-Fudan dataset, using bounding-box crops as positives and non-overlapping background patches as negatives. To retrain locally:

```bash
source .venv-webots/bin/activate
cd SDC_webots/training
python train_svm.py
cp svm_pedestrian_model.pkl ../controllers/vehicle_controller/svm_pedestrian_model.pkl
```

The script prints the confusion matrix and `classification_report` used in the deliverable video. Last training run (170 images): 420 positives / 239 negatives, ~97% accuracy.

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
- The sliding-window detector evaluates ~63 candidate windows per frame across 3 scales; it batches them into a single `LinearSVC.predict` call to keep the per-step cost low at the 32 ms timestep.
- Pedestrians vs. barrels are disambiguated using the SVM output on top of LiDAR proximity: SVM-positive obstacles trigger a no-hazard pedestrian stop, SVM-negative obstacles trigger the hazard-flasher barrel branch.
