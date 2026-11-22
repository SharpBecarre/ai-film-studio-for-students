"""Reconstruct an adaptive shot plan using trusted saved assets.

No files are written and no media is generated.
"""

from pathlib import Path

from adaptive_narration_durations import inspect_saved_narration
from adaptive_existing_assets import inspect_existing_scene_assets
from adaptive_planning_api import prepare_adaptive_planning_response
from adaptive_shot_plan_store import validate_saved_shot_plan


def build_trusted_approval_plan(
    scenes,
    scene_number,
    strategy,
    submitted_plan,
):
    """Verify a submitted plan against saved Ocean City assets."""

    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Complete storyboard scenes are required.")

    if type(scene_number) is not int or not 1 <= scene_number <= len(scenes):
        raise ValueError("Invalid scene number.")

    if strategy not in ("balanced", "cinematic"):
        raise ValueError("Invalid strategy.")

    project_folder = (
        Path(__file__).resolve().parent
        / "generated_videos"
        / "ocean_city_cinematic"
    )

    narration = inspect_saved_narration(
        project_folder,
        scenes,
    )

    assets = inspect_existing_scene_assets(
        project_folder,
        scene_number,
    )

    duration = narration["durations"][scene_number - 1][
        "duration_seconds"
    ]

    response = prepare_adaptive_planning_response({
        "scenes": scenes,
        "scene": scenes[scene_number - 1],
        "scene_number": scene_number,
        "strategy": strategy,
        "narration_duration": duration,
        "existing_prompts": assets["existing_prompts"],
        "locked_clips": assets["locked_clips"],
    })

    trusted_plan = response["shot_plan"]
    specification = response["specification"]

    validate_saved_shot_plan(
        submitted_plan,
        narration["storyboard_fingerprint"],
        scene_number,
        specification,
    )

    for trusted_clip, submitted_clip in zip(
        trusted_plan["clips"],
        submitted_plan["clips"],
    ):
        if trusted_clip["prompt_locked"]:
            if (
                submitted_clip["motion_prompt"]
                != trusted_clip["motion_prompt"]
            ):
                raise PermissionError(
                    "Protected cinematic prompt cannot be changed."
                )

            if submitted_clip["prompt_locked"] is not True:
                raise PermissionError(
                    "Protected clip cannot be unlocked."
                )

        elif submitted_clip["prompt_locked"] is not False:
            raise PermissionError(
                "Browser cannot lock an editable clip."
            )

    return {
        "shot_plan": submitted_plan,
        "specification": specification,
        "storyboard_fingerprint":
            narration["storyboard_fingerprint"],
        "scene_number": scene_number,
        "trusted_assets_verified": True,
        "narration_text_verified": False,
    }
