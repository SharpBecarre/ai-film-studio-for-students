"""Prepare adaptive AI shot planning without API calls."""

from adaptive_shot_plan_store import validate_saved_shot_plan


def prepare_ai_shot_planning(
    scene,
    saved_plan,
    storyboard_fingerprint,
    scene_number,
    specification,
):
    """Identify missing prompts while preserving existing work."""

    if not isinstance(scene, dict):
        raise ValueError("Storyboard scene must be an object.")

    validate_saved_shot_plan(
        saved_plan,
        storyboard_fingerprint,
        scene_number,
        specification,
    )

    missing = []
    preserved = []

    for clip in saved_plan["clips"]:
        number = clip["clip_number"]
        prompt = clip["motion_prompt"].strip()

        if prompt:
            preserved.append(number)
        else:
            if clip["prompt_locked"]:
                raise ValueError(
                    f"Clip {number} is locked but has no prompt."
                )

            missing.append(number)

    return {
        "storyboard_fingerprint": storyboard_fingerprint,
        "scene_number": scene_number,
        "strategy": specification["strategy"],
        "timing_sha256": specification["timing_sha256"],
        "required_clip_count": specification["clip_count"],
        "preserved_clip_numbers": preserved,
        "missing_clip_numbers": missing,
        "requires_ai": bool(missing),
    }
