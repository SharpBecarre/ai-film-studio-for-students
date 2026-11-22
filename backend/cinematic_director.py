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


def build_image_aware_cinematic_prompt(scene):
    """Build instructions for planning motion from an actual image."""
    narration = str(scene.get("narration") or "")
    visual = str(scene.get("visual") or "")
    title = str(scene.get("title") or "")

    return f"""
You are a cinematic director planning a 5-second
image-to-video animation.

You will receive an actual storyboard image together
with the following scene information.

Scene title: {title}
Narration: {narration}
Original visual description: {visual}

IMPORTANT:
- Treat the supplied image as the visual source of truth.
- Identify only subjects and objects visible in the image.
- Do not invent objects or change their identities.
- If the written description differs from the image,
  follow the image for visual details.
- Preserve the existing composition and setting.
- Choose subtle, realistic subject movement.
- Choose one smooth, achievable camera movement.
- Keep all movement suitable for a 5-second shot.
- Do not introduce cuts, montages, or transitions.
- Do not add text, logos, captions, or watermarks.
- Preserve the factual meaning of the narration.

Return ONLY valid JSON with these fields:
{{
  "shot_description": "...",
  "subject_action": "...",
  "camera_movement": "...",
  "motion_prompt": "..."
}}

The motion_prompt must be suitable for Runway
image-to-video generation and must not exceed
900 characters.
""".strip()


def encode_storyboard_image(image_path):
    """Encode an existing storyboard image for AI vision input."""
    import base64
    import mimetypes
    from pathlib import Path

    path = Path(image_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Storyboard image not found: {path}"
        )

    mime_type, _ = mimetypes.guess_type(path.name)

    if mime_type not in ("image/png", "image/jpeg", "image/webp"):
        raise ValueError("Unsupported storyboard image format.")

    image_bytes = path.read_bytes()

    if not image_bytes:
        raise ValueError("Storyboard image is empty.")

    encoded = base64.b64encode(image_bytes).decode("ascii")

    return f"data:{mime_type};base64,{encoded}"


def build_image_aware_input(scene, image_path):
    """Prepare a multimodal cinematic planning request."""
    prompt = build_image_aware_cinematic_prompt(scene)
    image_url = encode_storyboard_image(image_path)

    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": prompt,
                },
                {
                    "type": "input_image",
                    "image_url": image_url,
                },
            ],
        }
    ]


def generate_image_aware_cinematic_plan(scene, image_path, client):
    """Generate a cinematic plan using the actual storyboard image."""
    request_input = build_image_aware_input(scene, image_path)

    response = client.responses.create(
        model="gpt-6-luna",
        input=request_input,
    )

    try:
        plan = json.loads(response.output_text)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError(
            "AI returned invalid image-aware cinematic plan JSON."
        ) from error

    return validate_cinematic_plan(plan)


def cinematic_plan_path(scene_folder, scene_index):
    """Return a separate path for a scene's cinematic plan."""
    from pathlib import Path

    if not isinstance(scene_index, int) or isinstance(scene_index, bool):
        raise ValueError("Scene index must be an integer.")

    if scene_index < 0:
        raise ValueError("Scene index cannot be negative.")

    return Path(scene_folder) / f"cinematic_plan_{scene_index}.json"


def save_cinematic_plan(scene_folder, scene_index, plan, image_path):
    """Save a cinematic plan linked to its source image."""
    import os
    import tempfile

    validated = validate_cinematic_plan(plan)
    image_hash = storyboard_image_fingerprint(image_path)

    path = cinematic_plan_path(scene_folder, scene_index)
    path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "image_fingerprint": image_hash,
        "plan": validated,
    }

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=".cinematic_plan_",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(
                record,
                temporary_file,
                indent=2,
                ensure_ascii=False,
            )

        os.replace(temporary_path, path)

    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)

    return path


def load_cinematic_plan(scene_folder, scene_index, image_path):
    """Load a cinematic plan only if its source image matches."""
    path = cinematic_plan_path(scene_folder, scene_index)

    if not path.is_file():
        return None

    record = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(record, dict):
        raise ValueError("Invalid cinematic plan record.")

    saved_hash = record.get("image_fingerprint")
    current_hash = storyboard_image_fingerprint(image_path)

    if not isinstance(saved_hash, str) or saved_hash != current_hash:
        raise ValueError(
            "Cinematic plan image fingerprint mismatch. "
            "The saved plan cannot be used with this image."
        )

    return validate_cinematic_plan(record.get("plan"))

def select_saved_motion_prompt(scene, scene_folder, scene_index, image_path):
    """Select a saved motion prompt only for its matching image."""
    saved_plan = load_cinematic_plan(
        scene_folder,
        scene_index,
        image_path,
    )

    if saved_plan is not None:
        return saved_plan["motion_prompt"].strip()

    return select_motion_prompt(scene)


def storyboard_image_fingerprint(image_path):
    """Calculate a SHA-256 fingerprint of a storyboard image."""
    import hashlib
    from pathlib import Path

    path = Path(image_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Storyboard image not found: {path}"
        )

    digest = hashlib.sha256()

    with path.open("rb") as image_file:
        for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()



def calculate_clip_count(
    required_duration,
    clip_duration,
    crossfade_duration,
):
    """Calculate the minimum number of overlapping video clips."""
    import math

    if required_duration <= 0:
        raise ValueError("Required duration must be positive.")
    if clip_duration <= 0:
        raise ValueError("Clip duration must be positive.")
    if not 0 <= crossfade_duration < clip_duration:
        raise ValueError("Invalid crossfade duration.")

    return max(
        1,
        math.ceil(
            (required_duration - crossfade_duration)
            / (clip_duration - crossfade_duration)
        ),
    )


def calculate_shot_timeline(
    required_duration,
    clip_duration=5.0,
    crossfade_duration=0.5,
):
    """Calculate overlapping clip positions for a scene."""
    count = calculate_clip_count(
        required_duration,
        clip_duration,
        crossfade_duration,
    )

    timeline = []
    step = clip_duration - crossfade_duration

    for index in range(count):
        start = index * step
        end = min(start + clip_duration, required_duration)

        timeline.append({
            "clip_number": index + 1,
            "start_seconds": round(start, 3),
            "end_seconds": round(end, 3),
            "duration_seconds": round(end - start, 3),
        })

    return timeline


def build_timed_multi_shot_prompt(
    scene,
    required_duration,
    clip_duration=5.0,
    crossfade_duration=0.5,
):
    """Build AI instructions for narration-aware multi-shot planning."""
    timeline = calculate_shot_timeline(
        required_duration,
        clip_duration,
        crossfade_duration,
    )

    return f"""
You are an AI Cinematic Director planning a sequence
of image-to-video shots for one documentary scene.

Scene title: {scene.get("title", "")}
Narration: {scene.get("narration", "")}
Original visual: {scene.get("visual", "")}

Required visual duration: {required_duration:.2f} seconds
Generated clip duration: {clip_duration:.2f} seconds
Crossfade duration: {crossfade_duration:.2f} seconds

SHOT TIMELINE:
{json.dumps(timeline, indent=2)}

Requirements:
- Return exactly {len(timeline)} distinct shots.
- Use ONE existing storyboard image for every shot.
- Match shot ideas to the narration's progression.
- Use different framing, camera movements, or subtle actions.
- Allow closer views of details already visible in the image.
- Preserve subjects, setting, and visual continuity.
- Do not invent new objects or change existing artwork.
- Do not include cuts or transitions inside generated clips.
- Crossfades are applied later during editing.
- Narration remains uninterrupted within the scene.
- Follow the supplied shot timeline.
- Each motion prompt must be 900 characters or fewer.

Return ONLY valid JSON:
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


def validate_multi_shot_plan(plan, timeline):
    """Validate all cinematic shots before video generation."""
    if not isinstance(plan, dict):
        raise ValueError("Multi-shot plan must be a JSON object.")

    clips = plan.get("clips")
    if not isinstance(clips, list):
        raise ValueError("Multi-shot plan must contain a clips list.")

    if len(clips) != len(timeline):
        raise ValueError(
            f"Expected {len(timeline)} clips, got {len(clips)}."
        )

    for index, (clip, timing) in enumerate(
        zip(clips, timeline), start=1
    ):
        if not isinstance(clip, dict):
            raise ValueError(f"Clip {index} must be an object.")

        if type(clip.get("clip_number")) is not int:
            raise ValueError(f"Clip {index} has invalid numbering.")

        if clip["clip_number"] != timing["clip_number"]:
            raise ValueError(f"Clip {index} is out of order.")

        validate_cinematic_plan(clip)

    return plan


def generate_multi_shot_plan(
    scene,
    narration_duration,
    client,
    clip_duration=5.0,
    crossfade_duration=0.5,
):
    """Generate and validate a narration-aware multi-shot plan.

    Makes one OpenAI planning request when explicitly called.
    Does not generate video or modify the storyboard.
    """
    timeline = calculate_shot_timeline(
        narration_duration,
        clip_duration,
        crossfade_duration,
    )

    prompt = build_timed_multi_shot_prompt(
        scene,
        narration_duration,
        clip_duration,
        crossfade_duration,
    )

    response = client.responses.create(
        model="gpt-6-luna",
        input=prompt,
    )

    try:
        plan = json.loads(response.output_text)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError(
            "AI returned invalid multi-shot plan JSON."
        ) from error

    validate_multi_shot_plan(plan, timeline)

    return {
        "timeline": timeline,
        "plan": plan,
    }
