import argparse
import json
import subprocess
from pathlib import Path


def check_motion(video_path, threshold=1.0):
    """Estimate visual changes between sampled video frames."""

    video_path = Path(video_path)

    if not video_path.is_file():
        raise FileNotFoundError(video_path)

    command = [
        "ffmpeg", "-v", "error",
        "-i", str(video_path),
        "-vf", "fps=2,scale=160:90,format=gray",
        "-f", "rawvideo",
        "-pix_fmt", "gray",
        "-",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        check=True,
    )

    frame_size = 160 * 90
    data = result.stdout

    if len(data) % frame_size != 0:
        raise ValueError("Unexpected decoded frame size.")

    frames = [
        data[i:i + frame_size]
        for i in range(0, len(data), frame_size)
    ]

    if len(frames) < 2:
        raise ValueError("Not enough video frames to measure motion.")

    changes = []

    for previous, current in zip(frames, frames[1:]):
        difference = sum(
            abs(a - b)
            for a, b in zip(previous, current)
        ) / frame_size

        changes.append(difference)

    average_change = sum(changes) / len(changes)
    maximum_change = max(changes)

    return {
        "video": str(video_path),
        "frames_sampled": len(frames),
        "average_frame_change": round(average_change, 3),
        "maximum_frame_change": round(maximum_change, 3),
        "low_motion_warning": average_change < threshold,
        "threshold": threshold,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    args = parser.parse_args()

    result = check_motion(args.video)
    print(json.dumps(result, indent=2))
