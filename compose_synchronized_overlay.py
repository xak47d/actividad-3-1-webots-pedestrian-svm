from pathlib import Path
import json
import subprocess


ROOT = Path(__file__).resolve().parent
MEDIA = ROOT / "media"
MAIN_VIDEO = MEDIA / "Actividad_3_1_synchronized_main.mp4"
CAMERA_VIDEO = MEDIA / "Actividad_3_1_synchronized_camera.mp4"
OUTPUT_VIDEO = MEDIA / "Actividad_3_1_synchronized_overlay.mp4"


def probe_duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def main():
    if not MAIN_VIDEO.exists() or not CAMERA_VIDEO.exists():
        raise SystemExit(
            "Primero genera los videos con capture_synchronized_video.sh o capture_synchronized_video.cmd."
        )

    main_duration = probe_duration(MAIN_VIDEO)
    camera_duration = probe_duration(CAMERA_VIDEO)
    timeline_ratio = camera_duration / main_duration

    filter_graph = (
        f"[0:v]setpts={timeline_ratio:.10f}*PTS[main];"
        "[1:v]scale=384:192,"
        "drawbox=x=0:y=0:w=iw:h=ih:color=yellow@0.95:t=4[cam];"
        "[main][cam]overlay=W-w-28:28"
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(MAIN_VIDEO),
            "-i",
            str(CAMERA_VIDEO),
            "-filter_complex",
            filter_graph,
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-an",
            "-shortest",
            str(OUTPUT_VIDEO),
        ],
        check=True,
    )

    print(f"Video compuesto generado: {OUTPUT_VIDEO}")


if __name__ == "__main__":
    main()
