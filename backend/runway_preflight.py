import argparse
import json
import subprocess
from pathlib import Path


def valid_video(path):
    if not path.is_file() or path.stat().st_size == 0:
        return False

    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    return result.returncode == 0 and result.stdout.strip() == "video"


def inspect_folder(folder):
    metadata_path = folder / "storyboard_metadata.json"

    if not metadata_path.is_file():
        raise FileNotFoundError("Storyboard metadata is missing.")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    count = metadata["scene_count"]
    results = []

    for index in range(count):
        moving = folder / f"moving_{index}.mp4"
        narrated = folder / f"scene_{index}.mp4"
        failure = folder / f"scene_{index}_failure.json"

        has_moving = valid_video(moving)
        has_narrated = valid_video(narrated)

        error = None
        if failure.is_file():
            try:
                error = json.loads(failure.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                error = {"error_message": "Failure record unreadable"}

        if has_moving:
            status = "moving_video_available"
        elif error:
            status = "static_fallback_recorded"
        elif has_narrated:
            status = "narrated_video_without_moving_source"
        else:
            status = "missing_video"

        results.append({
            "scene_number": index + 1,
            "status": status,
            "moving_video_available": has_moving,
            "narrated_video_available": has_narrated,
            "error": error,
        })

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()

    results = inspect_folder(args.folder)

    print(json.dumps(results, indent=2))

    missing = [
        str(item["scene_number"])
        for item in results
        if not item["moving_video_available"]
    ]

    print()
    print("Scenes without reusable moving videos:",
          ", ".join(missing) if missing else "None")
