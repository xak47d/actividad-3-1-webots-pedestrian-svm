from controller import Supervisor
import os

TIME_STEP = 32

supervisor = Supervisor()

main_video_path = os.getenv("WEBOTS_RECORD_MAIN_PATH", "").strip()
main_frame_dir = os.getenv("WEBOTS_RECORD_MAIN_FRAME_DIR", "").strip()
frame_interval_text = os.getenv("WEBOTS_RECORD_FRAME_INTERVAL_STEPS", "3").strip()
duration_text = os.getenv("WEBOTS_RECORD_MAX_SECONDS", "18").strip()
width = int(os.getenv("WEBOTS_RECORD_MAIN_WIDTH", "1280"))
height = int(os.getenv("WEBOTS_RECORD_MAIN_HEIGHT", "720"))
quality = int(os.getenv("WEBOTS_RECORD_MAIN_QUALITY", "85"))
frame_index = 0

try:
    frame_interval = max(1, int(frame_interval_text))
except ValueError:
    print("WEBOTS_RECORD_FRAME_INTERVAL_STEPS debe ser entero:", frame_interval_text)
    frame_interval = 3

try:
    max_seconds = float(duration_text)
except ValueError:
    print("WEBOTS_RECORD_MAX_SECONDS debe ser numerico:", duration_text)
    max_seconds = 18.0

if main_frame_dir:
    os.makedirs(main_frame_dir, exist_ok=True)

if main_video_path:
    supervisor.movieStartRecording(
        main_video_path,
        width,
        height,
        0,
        quality,
        1,
        False
    )

elapsed_seconds = 0.0
step_counter = 0
while supervisor.step(TIME_STEP) != -1:
    step_counter += 1
    elapsed_seconds += TIME_STEP / 1000.0

    if main_frame_dir and step_counter % frame_interval == 0:
        frame_index += 1
        frame_path = os.path.join(
            main_frame_dir,
            f"main_{frame_index:05d}_step_{step_counter:06d}_t_{elapsed_seconds:07.3f}.jpg"
        )
        supervisor.exportImage(frame_path, quality)

    if elapsed_seconds >= max_seconds:
        if main_video_path:
            supervisor.movieStopRecording()

            while not supervisor.movieIsReady() and not supervisor.movieFailed():
                if supervisor.step(TIME_STEP) == -1:
                    break

            if supervisor.movieFailed():
                print("No se pudo guardar el video principal:", main_video_path)

        break
