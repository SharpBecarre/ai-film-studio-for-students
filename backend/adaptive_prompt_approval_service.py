"""Explicit approval of verified cinematic motion prompts.

Approvals are returned in memory only.
No files are written and no media is generated.
"""

import json
from pathlib import Path

from adaptive_trusted_approval_plan import (
    build_trusted_approval_plan,
)
from adaptive_prompt_approvals import (
    create_prompt_approval,
    validate_prompt_approval,
)


def approve_verified_motion_prompt(
    scene_number,
    strategy,
    clip_number,
    submitted_plan,
    confirmed=False,
):
    """Approve an unlocked prompt after server-side verification."""

    if confirmed is not True:
        raise PermissionError(
            "Explicit prompt approval confirmation is required."
        )

    project_folder = (
        Path(__file__).resolve().parent
        / "generated_videos"
        / "ocean_city_cinematic"
    )

    storyboard_path = project_folder / "storyboard.json"

    storyboard = json.loads(
        storyboard_path.read_text(encoding="utf-8")
    )

    if not isinstance(storyboard, dict):
        raise ValueError("Invalid saved storyboard.")

    scenes = storyboard.get("scenes")

    verified = build_trusted_approval_plan(
        scenes,
        scene_number,
        strategy,
        submitted_plan,
    )

    plan = verified["shot_plan"]

    if type(clip_number) is not int or clip_number < 1:
        raise ValueError("Invalid clip number.")

    clips = plan["clips"]

    matches = [
        clip for clip in clips
        if clip["clip_number"] == clip_number
    ]

    if len(matches) != 1:
        raise ValueError("Clip not uniquely identified.")

    if matches[0]["prompt_locked"]:
        raise PermissionError(
            "Cannot approve a protected cinematic clip."
        )

    record = create_prompt_approval(
        plan,
        clip_number,
        confirmed=True,
    )

    validate_prompt_approval(
        plan,
        clip_number,
        record,
    )

    return {
        "approved": True,
        "approval": record,
        "trusted_assets_verified": True,
        "saved_to_disk": False,
        "video_generated": False,
    }
