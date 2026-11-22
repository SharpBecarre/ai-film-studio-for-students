"""Adaptive AI shot planning without modifying the storyboard."""

import json

from adaptive_render_spec import build_adaptive_render_spec
from cinematic_director import validate_multi_shot_plan


def build_adaptive_multi_shot_prompt(
    scene,
    narration_duration,
    strategy="balanced",
    clip_duration=5.0,
    crossfade=0.5,
    shot_plan=None,
):
    """Create narration-aware AI instructions using adaptive timing."""

    spec = build_adaptive_render_spec(
        narration_duration=narration_duration,
        strategy=strategy,
        clip_duration=clip_duration,
        crossfade=crossfade,
    )

    durations = spec["clip_durations"]

    timeline = []
    elapsed = 0.0

    for index, duration in enumerate(durations, start=1):
        if index > 1:
            elapsed -= crossfade

        timeline.append({
            "clip_number": index,
            "start_seconds": round(elapsed, 3),
            "end_seconds": round(elapsed + duration, 3),
            "duration_seconds": duration,
        })

        elapsed += duration

    existing_plan = scene.get("cinematic_plan") or {}

    references = []
    missing = []

    if shot_plan is not None:
        clips = shot_plan.get("clips")

        if not isinstance(clips, list):
            raise ValueError("Shot plan must contain clips.")

        if len(clips) != len(timeline):
            raise ValueError("Shot plan clip count mismatch.")

        for expected, clip in enumerate(clips, start=1):
            if clip.get("clip_number") != expected:
                raise ValueError("Shot plan numbering mismatch.")

            motion = clip.get("motion_prompt", "")

            if not isinstance(motion, str):
                raise ValueError("Invalid existing motion prompt.")

            motion = motion.strip()

            if motion:
                references.append({
                    "clip_number": expected,
                    "prompt_locked": clip.get(
                        "prompt_locked", False
                    ),
                    "motion_prompt": motion,
                })
            else:
                if clip.get("prompt_locked"):
                    raise ValueError(
                        "Locked clip cannot have an empty prompt."
                    )
                missing.append(expected)

    reference_text = json.dumps(
        references,
        ensure_ascii=False,
        indent=2,
    )

    missing_text = json.dumps(missing)

    prompt = f"""
You are an AI Cinematic Director planning a documentary scene.

SCENE
Title: {scene.get("title", "")}
Narration: {scene.get("narration", "")}
Storyboard visual: {scene.get("visual", "")}

EXISTING CINEMATIC DIRECTION
{json.dumps(existing_plan, ensure_ascii=False, indent=2)}

EDITING STRATEGY
{strategy}

Required narration duration: {narration_duration:.3f}s
Maximum generated clip duration: {clip_duration:.3f}s
Crossfade duration: {crossfade:.3f}s
Final-frame extension: {spec["extension"]:.3f}s

ADAPTIVE SHOT TIMELINE
{json.dumps(timeline, indent=2)}

EXISTING CLIP PROMPTS — CREATIVE REFERENCES
{reference_text}

MISSING CLIP NUMBERS
{missing_text}

PRESERVATION RULES
- Existing prompts are authoritative creative references.
- Do not rewrite existing prompts, whether locked or editable.
- Generate new motion prompts only for missing clip numbers.
- Use existing prompts to preserve visual continuity.
- Each shot is independently composed; no matching boundary frames required.
- Return all clip numbers for compatibility with the saved-plan merger.
- For existing clips, return their original motion_prompt unchanged.
- Existing clip entries are ignored by the merger when already populated.

CREATIVE REQUIREMENTS
- Plan exactly {len(timeline)} visually related shots.
- Match the progression of the narration.
- Respect the existing storyboard image and cinematic direction.
- Each shot may have different framing or camera movement.
- Shots do NOT need to form one continuous camera movement.
- Do NOT require the next shot to start from the previous final frame.
- Crossfades will connect the independently composed shots.
- Preserve the subjects, visual style, and scene setting.
- Allow close-ups of existing visual details.
- Do not introduce unrelated objects or locations.
- Avoid abrupt camera motion or unstable geometry.
- Do not include transitions or cuts within individual clips.
- Each motion prompt must be no longer than 900 characters.
- All prompts must be editable before video generation.
- Do not generate video.

Return ONLY valid JSON in this structure:

{{
  "clips": [
    {{
      "clip_number": 1,
      "shot_description": "...",
      "subject_action": "...",
      "camera_movement": "...",
      "motion_prompt": "..."
    }}
  ]
}}

Return exactly {len(timeline)} clips.
""".strip()

    return {
        "prompt": prompt,
        "timeline": timeline,
        "specification": spec,
    }


def generate_adaptive_multi_shot_plan(
    scene,
    narration_duration,
    client,
    strategy="balanced",
    clip_duration=5.0,
    crossfade=0.5,
):
    """Generate an adaptive shot plan with one explicit AI request.

    This function does not render videos or change storyboard data.
    """

    prepared = build_adaptive_multi_shot_prompt(
        scene=scene,
        narration_duration=narration_duration,
        strategy=strategy,
        clip_duration=clip_duration,
        crossfade=crossfade,
    )

    response = client.responses.create(
        model="gpt-6-luna",
        input=prepared["prompt"],
    )

    try:
        plan = json.loads(response.output_text)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError(
            "AI returned invalid adaptive multi-shot JSON."
        ) from error

    validate_multi_shot_plan(
        plan,
        prepared["timeline"],
    )

    return {
        "timeline": prepared["timeline"],
        "specification": prepared["specification"],
        "plan": plan,
    }
