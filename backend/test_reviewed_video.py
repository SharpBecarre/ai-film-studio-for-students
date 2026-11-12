from pathlib import Path

from animation_review import load_review
from video_renderer import (
    create_scene_video,
    create_moving_scene_video,
    assemble_with_crossfades,
)

folder = Path(
    "backend/generated_videos/animation_review_test"
).resolve()

if not folder.is_dir():
    raise RuntimeError("Test folder not found.")

# Verify all inputs before rendering anything.
plan = []

for index in range(5):
    scene_number = index + 1
    review = load_review(folder, scene_number)

    if review is None:
        raise RuntimeError(f"Scene {scene_number}: review missing.")

    image = folder / f"scene_{index}.png"
    audio = folder / f"scene_{index}.mp3"
    moving = folder / f"moving_{index}.mp4"
    output = folder / f"reviewed_scene_{index}.mp4"

    if not image.is_file() or not audio.is_file():
        raise RuntimeError(
            f"Scene {scene_number}: image or narration missing."
        )

    if review["status"] == "approved":
        if not moving.is_file():
            raise RuntimeError(
                f"Scene {scene_number}: approved animation missing."
            )
        mode = "moving"
    else:
        mode = "static"

    plan.append((scene_number, mode, image, audio, moving, output))

print("Rendering plan:")

for scene_number, mode, *_ in plan:
    print(f"  Scene {scene_number}: {mode}")

print()

scene_videos = []

for scene_number, mode, image, audio, moving, output in plan:
    print(f"Rendering scene {scene_number}...", flush=True)

    if mode == "moving":
        create_moving_scene_video(moving, audio, output)
    else:
        create_scene_video(image, audio, output)

    scene_videos.append(output)

final_output = folder / "reviewed_documentary_test.mp4"

assemble_with_crossfades(
    scene_videos,
    final_output,
    fade=0.5,
)

print()
print("PASS: Reviewed documentary created.")
print(f"Output: {final_output}")
