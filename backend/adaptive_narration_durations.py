"""Read-only duration inspection for saved storyboard narration."""

import json
import math
from pathlib import Path

from multi_clip_renderer import probe_duration
from video_renderer import storyboard_fingerprint


def inspect_saved_narration(project_folder, scenes):
    """Return durations only for a matching saved storyboard."""

    folder = Path(project_folder)

    if not folder.is_dir():
        raise FileNotFoundError(
            "Saved project folder does not exist."
        )

    if (
        not isinstance(scenes, list)
        or not scenes
        or not all(isinstance(scene, dict) for scene in scenes)
    ):
        raise ValueError(
            "A nonempty storyboard scene list is required."
        )

    metadata_path = folder / "storyboard_metadata.json"

    if not metadata_path.is_file():
        raise ValueError(
            "Saved storyboard metadata is missing."
        )

    metadata = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )

    fingerprint = storyboard_fingerprint(scenes)

    if metadata.get("fingerprint") != fingerprint:
        raise ValueError(
            "Saved narration storyboard fingerprint does not match."
        )

    if metadata.get("scene_count") != len(scenes):
        raise ValueError(
            "Saved storyboard scene count does not match."
        )

    results = []

    for index, scene in enumerate(scenes):
        audio_path = folder / f"scene_{index}.mp3"

        if not audio_path.is_file():
            raise FileNotFoundError(
                f"Saved narration missing for scene {index + 1}."
            )

        duration = probe_duration(audio_path)

        if not math.isfinite(duration) or duration <= 0:
            raise ValueError(
                f"Invalid narration duration for scene {index + 1}."
            )

        results.append({
            "scene_number": index + 1,
            "title": scene.get("title", ""),
            "duration_seconds": duration,
            "audio_filename": audio_path.name,
        })

    return {
        "storyboard_fingerprint": fingerprint,
        "scene_count": len(scenes),
        "durations": results,
        "total_duration_seconds": sum(
            item["duration_seconds"] for item in results
        ),
        "audio_verified": True,
        "narration_text_verified": False,
    }
