"""Coordinate adaptive AI planning without automatically calling APIs."""

from adaptive_render_spec import build_adaptive_render_spec
from adaptive_shot_plan_store import (
    create_shot_plan,
    validate_saved_shot_plan,
)
from adaptive_ai_plan_preparation import prepare_ai_shot_planning
from adaptive_cinematic_director import build_adaptive_multi_shot_prompt


def prepare_scene_ai_plan(
    scene,
    narration_duration,
    storyboard_fingerprint,
    scene_number,
    strategy="balanced",
    existing_prompts=None,
    locked_clips=None,
    saved_plan=None,
):
    """Prepare an AI planning preview without generating anything."""

    specification = build_adaptive_render_spec(
        narration_duration=narration_duration,
        strategy=strategy,
    )

    if saved_plan is None:
        plan = create_shot_plan(
            storyboard_fingerprint=storyboard_fingerprint,
            scene_number=scene_number,
            specification=specification,
            existing_prompts=existing_prompts,
            locked_clips=locked_clips,
        )
    else:
        validate_saved_shot_plan(
            saved_plan,
            storyboard_fingerprint,
            scene_number,
            specification,
        )
        plan = saved_plan

    preparation = prepare_ai_shot_planning(
        scene=scene,
        saved_plan=plan,
        storyboard_fingerprint=storyboard_fingerprint,
        scene_number=scene_number,
        specification=specification,
    )

    ai_prompt = None

    if preparation["requires_ai"]:
        ai_prompt = build_adaptive_multi_shot_prompt(
            scene=scene,
            narration_duration=narration_duration,
            strategy=strategy,
            shot_plan=plan,
        )

    return {
        "specification": specification,
        "shot_plan": plan,
        "preparation": preparation,
        "ai_prompt": ai_prompt,
    }
