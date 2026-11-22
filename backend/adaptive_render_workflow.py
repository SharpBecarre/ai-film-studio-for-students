"""Safe, optional adaptive scene rendering workflow.

No paid APIs. Existing legacy renderer remains unchanged.
"""

import json
from pathlib import Path

from adaptive_multi_clip_renderer import assemble_adaptive_scene_clips
from multi_clip_renderer import find_approved_scene_clips
from adaptive_render_metadata import (
    build_adaptive_render_metadata,
    validate_adaptive_render_metadata,
)


def render_or_reuse_adaptive_scene(
    scene_directory,
    narration_path,
    storyboard_fingerprint_value,
    scene_number,
    strategy="balanced",
    crossfade=0.5,
):
    """Render once or reuse only a verified adaptive scene."""

    directory = Path(scene_directory).resolve()

    if not directory.is_dir():
        raise FileNotFoundError(directory)

    from adaptive_render_spec import build_adaptive_render_spec
    from multi_clip_renderer import probe_duration

    narration = Path(narration_path).resolve()

    if not narration.is_file():
        raise FileNotFoundError(narration)

    spec = build_adaptive_render_spec(
        narration_duration=probe_duration(narration),
        strategy=strategy,
        crossfade=crossfade,
    )

    # Require explicit approval before rendering OR reuse.
    # Validates the storyboard, scene number, clip status,
    # playability, and exact SHA256 of every source clip.
    clips = find_approved_scene_clips(
        scene_directory=directory,
        required_count=spec["clip_count"],
        require_approval=True,
        storyboard_fingerprint=storyboard_fingerprint_value,
        scene_number=scene_number,
    )

    output = directory / "adaptive_rendered_scene.mp4"
    metadata_path = directory / "adaptive_render_metadata.json"

    if output.exists() or metadata_path.exists():
        if not output.is_file() or not metadata_path.is_file():
            raise ValueError(
                "Incomplete adaptive render exists. "
                "Manual review required; nothing overwritten."
            )

        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )

        validate_adaptive_render_metadata(
            metadata,
            storyboard_fingerprint_value,
            scene_number,
            narration,
            clips,
            output,
            strategy=strategy,
            crossfade=crossfade,
        )

        return {
            "output_path": output,
            "metadata_path": metadata_path,
            "reused": True,
        }

    result = assemble_adaptive_scene_clips(
        clip_paths=clips,
        narration_path=narration,
        output_path=output,
        strategy=strategy,
        crossfade=crossfade,
    )

    metadata = build_adaptive_render_metadata(
        storyboard_fingerprint_value,
        scene_number,
        narration,
        clips,
        output,
        strategy=strategy,
        crossfade=crossfade,
    )

    # Exclusive creation prevents accidental metadata overwrite.
    with metadata_path.open("x", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    validate_adaptive_render_metadata(
        metadata,
        storyboard_fingerprint_value,
        scene_number,
        narration,
        clips,
        output,
        strategy=strategy,
        crossfade=crossfade,
    )

    return {
        "output_path": output,
        "metadata_path": metadata_path,
        "reused": False,
        "specification": result["specification"],
    }
