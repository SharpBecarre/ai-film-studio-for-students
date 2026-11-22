"""Preview a verified Runway request without generating video.

No API calls, file writes, or media generation.
"""

import hmac
import json
import re
from pathlib import Path

from adaptive_prompt_approvals import validate_prompt_approval
from cinematic_director import storyboard_image_fingerprint
from video_renderer import storyboard_fingerprint


def build_adaptive_runway_preview(
    plan,
    clip_number,
    approval_record,
    storyboard_path,
):
    """Prepare a preview for an approved, unlocked motion prompt."""

    validate_prompt_approval(plan, clip_number, approval_record)

    matches = [
        clip for clip in plan["clips"]
        if clip["clip_number"] == clip_number
    ]

    clip = matches[0]

    if clip["prompt_locked"]:
        raise PermissionError("Protected clip cannot be generated.")

    storyboard_path = Path(storyboard_path).resolve()
    storyboard = json.loads(
        storyboard_path.read_text(encoding="utf-8")
    )

    scenes = storyboard["scenes"]

    if not isinstance(scenes, list):
        raise ValueError("Invalid storyboard scenes.")

    actual_fingerprint = storyboard_fingerprint(scenes)
    approved_fingerprint = approval_record["storyboard_fingerprint"]

    if not isinstance(approved_fingerprint, str) or not hmac.compare_digest(
        actual_fingerprint,
        approved_fingerprint,
    ):
        raise ValueError(
            "Storyboard has changed since motion prompt approval."
        )

    scene_number = plan["scene_number"]

    if type(scene_number) is not int or not 1 <= scene_number <= len(scenes):
        raise ValueError("Invalid scene number.")

    image_id = scenes[scene_number - 1].get("image_id")

    if not isinstance(image_id, str) or not re.fullmatch(
        r"[0-9a-f]{32}\.png", image_id
    ):
        raise ValueError("Invalid storyboard image ID.")

    image_path = (
        Path(__file__).resolve().parent
        / "generated_storyboard_images"
        / image_id
    )

    image_hash = storyboard_image_fingerprint(image_path)

    return {
        "preview_only": True,
        "generation_submitted": False,
        "provider": "runway",
        "model": "gen4_turbo",
        "duration_seconds": 5,
        "ratio": "1280:720",
        "scene_number": scene_number,
        "clip_number": clip_number,
        "motion_prompt": clip["motion_prompt"],
        "image_path": str(image_path),
        "image_sha256": image_hash,
        "prompt_sha256": approval_record["prompt_sha256"],
    }
