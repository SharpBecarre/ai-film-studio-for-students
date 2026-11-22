"""Read-only adaptive cinematic planning API logic.

No AI requests, rendering, or filesystem writes.
"""

import math

from adaptive_ai_planning_coordinator import (
    prepare_scene_ai_plan,
)
from video_renderer import storyboard_fingerprint


def prepare_adaptive_planning_response(data):
    """Prepare an adaptive shot plan without generating media."""

    if not isinstance(data, dict):
        raise ValueError("Request body must be an object.")

    scene = data.get("scene")

    if not isinstance(scene, dict):
        raise ValueError("A storyboard scene is required.")

    for field in ("title", "narration", "visual"):
        if not isinstance(scene.get(field), str):
            raise ValueError(
                f"Scene field {field!r} must be text."
            )

    duration = data.get("narration_duration")

    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or duration <= 0
    ):
        raise ValueError(
            "A positive narration duration is required."
        )

    scene_number = data.get("scene_number")

    if (
        type(scene_number) is not int
        or scene_number < 1
    ):
        raise ValueError(
            "Scene number must be a positive integer."
        )

    strategy = data.get("strategy", "balanced")

    if strategy not in ("balanced", "cinematic"):
        raise ValueError(
            "Strategy must be balanced or cinematic."
        )

    scenes = data.get("scenes")

    if (
        not isinstance(scenes, list)
        or not scenes
        or not all(isinstance(item, dict) for item in scenes)
    ):
        raise ValueError(
            "Complete storyboard scenes are required."
        )

    if scene_number > len(scenes):
        raise ValueError(
            "Scene number exceeds storyboard length."
        )

    if scenes[scene_number - 1] != scene:
        raise ValueError(
            "Scene does not match its storyboard position."
        )

    existing_prompts = data.get("existing_prompts")

    if existing_prompts is not None:
        if not isinstance(existing_prompts, dict):
            raise ValueError(
                "Existing prompts must be an object."
            )

        converted = {}

        for key, value in existing_prompts.items():
            try:
                number = int(key)
            except (ValueError, TypeError) as error:
                raise ValueError(
                    "Prompt keys must be clip numbers."
                ) from error

            if (
                number < 1
                or str(number) != str(key)
                or not isinstance(value, str)
            ):
                raise ValueError(
                    "Invalid existing clip prompt."
                )

            converted[number] = value

        existing_prompts = converted

    locked_clips = data.get("locked_clips")

    if locked_clips is not None:
        if (
            not isinstance(locked_clips, list)
            or any(
                type(number) is not int or number < 1
                for number in locked_clips
            )
        ):
            raise ValueError(
                "Locked clips must be positive integers."
            )

    fingerprint = storyboard_fingerprint(scenes)

    result = prepare_scene_ai_plan(
        scene=scene,
        narration_duration=duration,
        storyboard_fingerprint=fingerprint,
        scene_number=scene_number,
        strategy=strategy,
        existing_prompts=existing_prompts,
        locked_clips=locked_clips,
    )

    return {
        "storyboard_fingerprint": fingerprint,
        "scene_number": scene_number,
        "specification": result["specification"],
        "shot_plan": result["shot_plan"],
        "preparation": result["preparation"],
        "ai_prompt": result["ai_prompt"],
        "ai_executed": False,
        "video_generated": False,
    }
