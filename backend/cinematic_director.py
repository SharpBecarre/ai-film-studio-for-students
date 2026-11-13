"""Prepare AI instructions for cinematic storyboard shot planning."""

import json


def build_cinematic_prompt(scene):
    """Build a prompt without modifying the original storyboard scene."""
    narration = str(scene.get("narration") or "")
    visual = str(scene.get("visual") or "")
    title = str(scene.get("title") or "")

    return f"""
You are a cinematic director creating short video shots
for an educational documentary.

Scene title: {title}
Narration: {narration}
Original visual description: {visual}

Plan one compelling 5-second animated shot.

Requirements:
- Preserve the factual meaning of the narration.
- Describe a specific subject and setting.
- Specify visible subject movement.
- Specify one realistic camera movement.
- Make the action achievable within 5 seconds.
- If the original visual describes multiple locations, cuts,
  or events, choose ONE coherent visual moment for this shot.
- Do not attempt scene changes, montages, or transitions
  inside a single 5-second animation.
- Prioritize natural movement, clear composition,
  and a visually engaging subject.
- Maintain visual consistency with the original image.
- Avoid unrelated objects, sudden transformations,
  excessive movement, and impossible camera actions.
- Do not add text, captions, logos, or watermarks.
- Make the shot visually engaging and appropriate
  for the educational subject.

Return ONLY valid JSON with these fields:
{{
  "shot_description": "...",
  "subject_action": "...",
  "camera_movement": "...",
  "motion_prompt": "..."
}}

The motion_prompt must be concise, specific,
and suitable for Runway image-to-video generation.
Do not exceed 900 characters in motion_prompt.
""".strip()


if __name__ == "__main__":
    sample = {
        "title": "AI and Creativity",
        "narration": "Artificial intelligence can help people create art.",
        "visual": "A robot painting a colorful picture."
    }

    print(build_cinematic_prompt(sample))


def validate_cinematic_plan(plan):
    """Validate an AI-generated shot plan before using it."""
    required = (
        "shot_description",
        "subject_action",
        "camera_movement",
        "motion_prompt",
    )

    if not isinstance(plan, dict):
        raise ValueError("Cinematic plan must be a JSON object.")

    for field in required:
        value = plan.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing or empty cinematic field: {field}")

    if len(plan["motion_prompt"]) > 900:
        raise ValueError("Motion prompt exceeds 900 characters.")

    return plan


def generate_cinematic_plan(scene, client):
    """Generate and validate one cinematic shot plan using OpenAI."""
    prompt = build_cinematic_prompt(scene)

    response = client.responses.create(
        model="gpt-6-luna",
        input=prompt,
    )

    try:
        plan = json.loads(response.output_text)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError(
            "AI returned invalid cinematic plan JSON."
        ) from error

    return validate_cinematic_plan(plan)


def select_motion_prompt(scene):
    """Select a cinematic prompt without modifying the scene."""
    plan = scene.get("cinematic_plan")

    if isinstance(plan, dict):
        prompt = plan.get("motion_prompt")
        if isinstance(prompt, str) and prompt.strip():
            if len(prompt) <= 900:
                return prompt.strip()

    visual = scene.get("visual")
    if isinstance(visual, str) and visual.strip():
        return visual.strip()[:900]

    title = scene.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()[:900]

    return "A cinematic scene with subtle natural movement."
