"""Validation of explicit cinematic motion-prompt approvals.

Prompt approval is separate from video clip approval.
This module performs no file writes or paid API requests.
"""

import hashlib
import hmac


def prompt_sha256(prompt):
    """Hash the exact UTF-8 text of a motion prompt."""
    if not isinstance(prompt, str):
        raise ValueError("Motion prompt must be text.")
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def validate_prompt_approval(plan, clip_number, record):
    """Validate an approval against the current shot plan."""
    if not isinstance(plan, dict):
        raise ValueError("Invalid shot plan.")

    if not isinstance(record, dict):
        raise ValueError("Invalid prompt approval record.")

    if type(clip_number) is not int or clip_number < 1:
        raise ValueError("Invalid clip number.")

    clips = plan.get("clips")

    if not isinstance(clips, list):
        raise ValueError("Invalid shot-plan clips.")

    matches = [
        clip for clip in clips
        if isinstance(clip, dict)
        and clip.get("clip_number") == clip_number
    ]

    if len(matches) != 1:
        raise ValueError("Clip not uniquely identified.")

    clip = matches[0]
    prompt = clip.get("motion_prompt")

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Cannot approve an empty prompt.")

    if len(prompt) > 900:
        raise ValueError("Prompt exceeds 900 characters.")

    if record.get("schema_version") != 1:
        raise ValueError("Unsupported approval version.")

    if record.get("status") != "approved":
        raise ValueError("Prompt has not been approved.")

    for field in (
        "storyboard_fingerprint",
        "scene_number",
        "strategy",
        "timing_sha256",
    ):
        if record.get(field) != plan.get(field):
            raise ValueError(
                f"Prompt approval mismatch: {field}"
            )

    if record.get("clip_number") != clip_number:
        raise ValueError("Prompt approval clip mismatch.")

    expected_hash = record.get("prompt_sha256")

    if (
        not isinstance(expected_hash, str)
        or len(expected_hash) != 64
        or any(c not in "0123456789abcdef" for c in expected_hash)
    ):
        raise ValueError("Invalid approval prompt hash.")

    actual_hash = prompt_sha256(prompt)

    if not hmac.compare_digest(
        actual_hash,
        expected_hash
    ):
        raise ValueError(
            "Prompt changed after approval."
        )

    return True



def create_prompt_approval(plan, clip_number, confirmed=False):
    """Create an in-memory record after explicit confirmation.

    This does not write files or approve generated video clips.
    """
    if confirmed is not True:
        raise PermissionError(
            "Explicit prompt approval confirmation is required."
        )

    if not isinstance(plan, dict):
        raise ValueError("Invalid shot plan.")

    if type(clip_number) is not int or clip_number < 1:
        raise ValueError("Invalid clip number.")

    clips = plan.get("clips")

    if not isinstance(clips, list):
        raise ValueError("Invalid shot-plan clips.")

    matches = [
        clip for clip in clips
        if isinstance(clip, dict)
        and clip.get("clip_number") == clip_number
    ]

    if len(matches) != 1:
        raise ValueError("Clip not uniquely identified.")

    prompt = matches[0].get("motion_prompt")

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Cannot approve an empty prompt.")

    if len(prompt) > 900:
        raise ValueError("Prompt exceeds 900 characters.")

    required_fields = (
        "storyboard_fingerprint",
        "scene_number",
        "strategy",
        "timing_sha256",
    )

    for field in required_fields:
        if field not in plan:
            raise ValueError(
                f"Missing shot-plan identity: {field}"
            )

    record = {
        "schema_version": 1,
        "status": "approved",
        "storyboard_fingerprint":
            plan["storyboard_fingerprint"],
        "scene_number": plan["scene_number"],
        "strategy": plan["strategy"],
        "timing_sha256": plan["timing_sha256"],
        "clip_number": clip_number,
        "prompt_sha256": prompt_sha256(prompt),
    }

    validate_prompt_approval(plan, clip_number, record)

    return record
