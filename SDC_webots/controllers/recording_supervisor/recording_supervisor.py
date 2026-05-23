from controller import Supervisor
import os

TIME_STEP = 32

supervisor = Supervisor()

main_video_path = os.getenv("WEBOTS_RECORD_MAIN_PATH", "").strip()
duration_text = os.getenv("WEBOTS_RECORD_MAX_SECONDS", "18").strip()
width = int(os.getenv("WEBOTS_RECORD_MAIN_WIDTH", "1280"))
height = int(os.getenv("WEBOTS_RECORD_MAIN_HEIGHT", "720"))
quality = int(os.getenv("WEBOTS_RECORD_MAIN_QUALITY", "85"))

try:
    max_seconds = float(duration_text)
except ValueError:
    print("WEBOTS_RECORD_MAX_SECONDS debe ser numerico:", duration_text)
    max_seconds = 18.0

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
while supervisor.step(TIME_STEP) != -1:
    elapsed_seconds += TIME_STEP / 1000.0

    if elapsed_seconds >= max_seconds:
        if main_video_path:
            supervisor.movieStopRecording()

            while not supervisor.movieIsReady() and not supervisor.movieFailed():
                if supervisor.step(TIME_STEP) == -1:
                    break

            if supervisor.movieFailed():
                print("No se pudo guardar el video principal:", main_video_path)

        break
