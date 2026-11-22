"""Metadata identity and validation for adaptive scene renders.

Does not generate videos or make API requests.
Legacy metadata version 1 remains unchanged.
"""

import hashlib
import hmac
import json
import re
import subprocess
from pathlib import Path

from adaptive_render_spec import build_adaptive_render_spec
from multi_clip_renderer import (
    is_playable_video,
    probe_duration,
    video_sha256,
)


def calculate_adaptive_render_identity(
    storyboard_fingerprint_value,
    scene_number,
    narration_path,
    clip_paths,
    strategy="balanced",
    crossfade=0.5,
):
    """Fingerprint exact adaptive rendering inputs."""

    if not re.fullmatch(
        r"[0-9a-f]{64}", str(storyboard_fingerprint_value)
    ):
        raise ValueError("Invalid storyboard fingerprint.")

    if type(scene_number) is not int or scene_number < 1:
        raise ValueError("Invalid scene number.")

    narration = Path(narration_path).resolve()
    clips = [Path(p).resolve() for p in clip_paths]

    if not narration.is_file():
        raise FileNotFoundError(narration)

    if not clips:
        raise ValueError("At least one clip is required.")

    for clip in clips:
        if not clip.is_file():
            raise FileNotFoundError(clip)

    spec = build_adaptive_render_spec(
        narration_duration=probe_duration(narration),
        strategy=strategy,
        crossfade=crossfade,
    )

    if len(clips) != spec["clip_count"]:
        raise ValueError(
            f"Expected {spec['clip_count']} clips, got {len(clips)}."
        )

    identity_data = {
        "schema_version": 2,
        "storyboard_fingerprint": storyboard_fingerprint_value,
        "scene_number": scene_number,
        "narration_sha256": video_sha256(narration),
        "clip_sha256": [video_sha256(p) for p in clips],
        "timing_sha256": spec["timing_sha256"],
    }

    encoded = json.dumps(
        identity_data,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _check_completed_video(output_path):
    output = Path(output_path).resolve()

    if not output.is_file():
        raise FileNotFoundError(output)

    if not is_playable_video(output):
        raise ValueError("Completed video is not playable.")

    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0 or result.stdout.strip() != "audio":
        raise ValueError("Completed video has no valid audio stream.")

    return output


def build_adaptive_render_metadata(
    storyboard_fingerprint_value,
    scene_number,
    narration_path,
    clip_paths,
    output_path,
    strategy="balanced",
    crossfade=0.5,
):
    """Build metadata for an existing completed adaptive render."""

    output = _check_completed_video(output_path)

    spec = build_adaptive_render_spec(
        narration_duration=probe_duration(narration_path),
        strategy=strategy,
        crossfade=crossfade,
    )

    identity = calculate_adaptive_render_identity(
        storyboard_fingerprint_value,
        scene_number,
        narration_path,
        clip_paths,
        strategy=strategy,
        crossfade=crossfade,
    )

    return {
        "schema_version": 2,
        "storyboard_fingerprint": storyboard_fingerprint_value,
        "scene_number": scene_number,
        "render_identity": identity,
        "output_filename": output.name,
        "output_sha256": video_sha256(output),
        "strategy": strategy,
        "timing_sha256": spec["timing_sha256"],
        "timing_specification": spec,
    }


def validate_adaptive_render_metadata(
    metadata,
    storyboard_fingerprint_value,
    scene_number,
    narration_path,
    clip_paths,
    output_path,
    strategy="balanced",
    crossfade=0.5,
):
    """Reject reuse when adaptive inputs or output have changed."""

    if not isinstance(metadata, dict):
        raise ValueError("Metadata must be a JSON object.")

    if metadata.get("schema_version") != 2:
        raise ValueError("Unsupported adaptive metadata version.")

    if metadata.get("storyboard_fingerprint") != storyboard_fingerprint_value:
        raise ValueError("Storyboard fingerprint mismatch.")

    if metadata.get("scene_number") != scene_number:
        raise ValueError("Scene number mismatch.")

    output = _check_completed_video(output_path)

    if metadata.get("output_filename") != output.name:
        raise ValueError("Output filename mismatch.")

    spec = build_adaptive_render_spec(
        narration_duration=probe_duration(narration_path),
        strategy=strategy,
        crossfade=crossfade,
    )

    if metadata.get("strategy") != strategy:
        raise ValueError("Rendering strategy mismatch.")

    if metadata.get("timing_specification") != spec:
        raise ValueError("Adaptive timing specification mismatch.")

    saved_timing_hash = metadata.get("timing_sha256")

    if (
        not isinstance(saved_timing_hash, str)
        or not hmac.compare_digest(
            saved_timing_hash,
            spec["timing_sha256"],
        )
    ):
        raise ValueError("Adaptive timing fingerprint mismatch.")

    expected_identity = calculate_adaptive_render_identity(
        storyboard_fingerprint_value,
        scene_number,
        narration_path,
        clip_paths,
        strategy=strategy,
        crossfade=crossfade,
    )

    saved_identity = metadata.get("render_identity")

    if (
        not isinstance(saved_identity, str)
        or not hmac.compare_digest(
            saved_identity,
            expected_identity,
        )
    ):
        raise ValueError("Adaptive render identity mismatch.")

    saved_output_hash = metadata.get("output_sha256")

    if (
        not isinstance(saved_output_hash, str)
        or not hmac.compare_digest(
            saved_output_hash,
            video_sha256(output),
        )
    ):
        raise ValueError("Completed video fingerprint mismatch.")

    return True
