"""Read-only inspection of existing adaptive cinematic assets."""

from pathlib import Path


def inspect_existing_scene_assets(
    project_folder,
    scene_number,
):
    """Read saved prompts and protect clips with existing video."""

    if type(scene_number) is not int or scene_number < 1:
        raise ValueError(
            "Scene number must be a positive integer."
        )

    project = Path(project_folder)

    if not project.is_dir():
        raise FileNotFoundError(
            "Saved project folder does not exist."
        )

    scene_folder = (
        project
        / "multiclip"
        / f"scene_{scene_number:03d}"
    )

    if not scene_folder.is_dir():
        return {
            "scene_number": scene_number,
            "existing_prompts": {},
            "locked_clips": [],
            "existing_videos": [],
        }

    prompts = {}
    locked = set()
    videos = set()

    for path in scene_folder.glob("clip_*_prompt.txt"):
        parts = path.stem.split("_")

        if (
            len(parts) != 3
            or parts[0] != "clip"
            or parts[2] != "prompt"
            or not parts[1].isdigit()
        ):
            continue

        clip_number = int(parts[1])

        if clip_number < 1:
            continue

        prompts[clip_number] = path.read_text(
            encoding="utf-8"
        )

    for path in scene_folder.glob("clip_*.mp4"):
        parts = path.stem.split("_")

        if (
            len(parts) != 2
            or parts[0] != "clip"
            or not parts[1].isdigit()
        ):
            continue

        clip_number = int(parts[1])

        if clip_number < 1:
            continue

        videos.add(clip_number)
        locked.add(clip_number)

    return {
        "scene_number": scene_number,
        "existing_prompts": {
            str(number): prompts[number]
            for number in sorted(prompts)
        },
        "locked_clips": sorted(locked),
        "existing_videos": sorted(videos),
    }
