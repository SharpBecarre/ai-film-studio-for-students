"""Persistent, editable adaptive shot plans.

This module does not generate video or make API requests.
Video approvals remain separate from prompt locks.
"""

import json
from pathlib import Path


def shot_plan_path(scene_directory):
    return Path(scene_directory) / "adaptive_shot_plan.json"


def create_shot_plan(
    storyboard_fingerprint,
    scene_number,
    specification,
    existing_prompts=None,
    locked_clips=None,
):
    """Create an editable shot-plan record in memory."""

    if not isinstance(storyboard_fingerprint, str):
        raise ValueError("Storyboard fingerprint is required.")

    if (
        type(scene_number) is not int
        or scene_number < 1
    ):
        raise ValueError("Invalid scene number.")

    if not isinstance(specification, dict):
        raise ValueError("Adaptive specification is required.")

    existing_prompts = existing_prompts or {}
    locked_clips = set(locked_clips or [])

    clips = []

    for number, duration in enumerate(
        specification["clip_durations"], start=1
    ):
        prompt = existing_prompts.get(number, "")

        clips.append({
            "clip_number": number,
            "duration_seconds": duration,
            "motion_prompt": prompt,
            "prompt_locked": number in locked_clips,
            "prompt_source": (
                "existing" if prompt else "pending_ai"
            ),
        })

    return {
        "schema_version": 1,
        "storyboard_fingerprint": storyboard_fingerprint,
        "scene_number": scene_number,
        "strategy": specification["strategy"],
        "timing_sha256": specification["timing_sha256"],
        "clips": clips,
    }


def merge_ai_prompts(saved_plan, ai_plan):
    """Add AI prompts without overwriting existing or locked prompts."""

    if not isinstance(saved_plan, dict):
        raise ValueError("Invalid saved shot plan.")

    if not isinstance(ai_plan, dict):
        raise ValueError("Invalid AI shot plan.")

    saved_clips = saved_plan.get("clips")
    ai_clips = ai_plan.get("clips")

    if not isinstance(saved_clips, list):
        raise ValueError("Saved clips must be a list.")

    if not isinstance(ai_clips, list):
        raise ValueError("AI clips must be a list.")

    if len(saved_clips) != len(ai_clips):
        raise ValueError("AI clip count mismatch.")

    updated = json.loads(json.dumps(saved_plan))

    for saved, generated in zip(
        updated["clips"], ai_clips
    ):
        if saved["clip_number"] != generated.get(
            "clip_number"
        ):
            raise ValueError("AI clip numbering mismatch.")

        if saved.get("prompt_locked"):
            continue

        if saved.get("motion_prompt", "").strip():
            continue

        prompt = generated.get("motion_prompt")

        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("AI returned an empty motion prompt.")

        if len(prompt) > 900:
            raise ValueError("AI motion prompt exceeds 900 characters.")

        saved["motion_prompt"] = prompt.strip()
        saved["prompt_source"] = "ai"

    return updated


def save_shot_plan(scene_directory, plan):
    """Save a new shot plan without overwriting an existing one."""

    path = shot_plan_path(scene_directory)

    if path.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing plan: {path}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("x", encoding="utf-8") as file:
        json.dump(plan, file, indent=2, ensure_ascii=False)

    return path


def load_shot_plan(scene_directory):
    """Load an existing shot plan."""

    path = shot_plan_path(scene_directory)

    if not path.is_file():
        raise FileNotFoundError(path)

    return json.loads(path.read_text(encoding="utf-8"))



def validate_saved_shot_plan(
    plan,
    storyboard_fingerprint,
    scene_number,
    specification,
):
    """Validate a saved plan against its current storyboard and timing."""

    if not isinstance(plan, dict):
        raise ValueError("Shot plan must be an object.")

    if plan.get("schema_version") != 1:
        raise ValueError("Unsupported shot-plan version.")

    if plan.get("storyboard_fingerprint") != storyboard_fingerprint:
        raise ValueError("Shot plan belongs to another storyboard.")

    if plan.get("scene_number") != scene_number:
        raise ValueError("Shot plan belongs to another scene.")

    if plan.get("strategy") != specification.get("strategy"):
        raise ValueError("Shot-plan strategy mismatch.")

    if plan.get("timing_sha256") != specification.get("timing_sha256"):
        raise ValueError("Shot-plan timing mismatch.")

    clips = plan.get("clips")
    durations = specification.get("clip_durations")

    if not isinstance(clips, list):
        raise ValueError("Shot plan must contain a clips list.")

    if not isinstance(durations, list):
        raise ValueError("Invalid adaptive timing specification.")

    if len(clips) != len(durations):
        raise ValueError("Shot-plan clip count mismatch.")

    for number, (clip, duration) in enumerate(
        zip(clips, durations), start=1
    ):
        if not isinstance(clip, dict):
            raise ValueError("Invalid shot-plan clip.")

        if type(clip.get("clip_number")) is not int:
            raise ValueError("Invalid clip number.")

        if clip["clip_number"] != number:
            raise ValueError("Shot-plan clip numbering mismatch.")

        if clip.get("duration_seconds") != duration:
            raise ValueError("Shot-plan clip duration mismatch.")

        if type(clip.get("prompt_locked")) is not bool:
            raise ValueError("Invalid prompt lock status.")

        prompt = clip.get("motion_prompt")

        if not isinstance(prompt, str):
            raise ValueError("Invalid motion prompt.")

        if len(prompt) > 900:
            raise ValueError("Motion prompt exceeds 900 characters.")

    return True


def update_clip_prompt(plan, clip_number, new_prompt):
    """Edit one unlocked prompt, returning a new in-memory plan."""

    if not isinstance(plan, dict):
        raise ValueError("Shot plan must be an object.")

    if type(clip_number) is not int or clip_number < 1:
        raise ValueError("Invalid clip number.")

    if not isinstance(new_prompt, str):
        raise ValueError("Motion prompt must be text.")

    new_prompt = new_prompt.strip()

    if not new_prompt:
        raise ValueError("Motion prompt cannot be empty.")

    if len(new_prompt) > 900:
        raise ValueError("Motion prompt exceeds 900 characters.")

    updated = json.loads(json.dumps(plan))

    clips = updated.get("clips")

    if not isinstance(clips, list):
        raise ValueError("Shot plan has no valid clips list.")

    matches = [
        clip for clip in clips
        if isinstance(clip, dict)
        and clip.get("clip_number") == clip_number
    ]

    if len(matches) != 1:
        raise ValueError("Clip number not found or duplicated.")

    clip = matches[0]

    if clip.get("prompt_locked"):
        raise PermissionError(
            f"Clip {clip_number} prompt is locked."
        )

    clip["motion_prompt"] = new_prompt
    clip["prompt_source"] = "manual_edit"

    return updated
