import os
from pathlib import Path
import textwrap
import subprocess
import tempfile
import hashlib
import json
import uuid

from PIL import Image, ImageDraw, ImageFont
from image_generator import generate_scene_image
from runway_video_generator import generate_moving_scene


USE_RUNWAY = os.getenv("USE_RUNWAY", "false").lower() == "true"
RESUME_FOLDER = os.getenv("VIDEO_RESUME_FOLDER", "").strip()

def create_scene_image(scene, output_path):
    """Create a 1280x720 image from a storyboard scene."""

    width, height = 1280, 720

    image = Image.new("RGB", (width, height), "#17243a")
    draw = ImageDraw.Draw(image)

    title = str(scene.get("title", "Untitled Scene"))
    visual = str(scene.get("visual", ""))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    title_font = ImageFont.truetype(font_path, 54)
    body_font = ImageFont.truetype(font_path, 30)

    draw.text(
        (80, 100),
        title,
        font=title_font,
        fill="white",
    )

    wrapped_visual = textwrap.fill(visual, width=65)

    draw.multiline_text(
        (80, 230),
        wrapped_visual,
        font=body_font,
        fill="#d9e6f2",
        spacing=15,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    image.save(output_path)

    return output_path

def create_scene_video(image_path, audio_path, output_path):
    """Combine a scene image and narration audio into an MP4."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-framerate", "24",
        "-i", str(image_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    subprocess.run(command, check=True)

    return output_path


def create_moving_scene_video(moving_video_path, audio_path, output_path):
    """Combine a moving video clip with narration, preserving all audio."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(moving_video_path),
        "-i", str(audio_path),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]

    subprocess.run(command, check=True)
    return output_path



def is_valid_scene_video(path):
    """Check that a saved scene contains a readable video stream."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size == 0:
        return False

    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "video"




def is_valid_narrated_scene(path):
    """Check that a completed scene contains video and audio."""
    if not is_valid_scene_video(path):
        return False

    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "audio"


def storyboard_fingerprint(scenes):
    """Create a stable fingerprint of the storyboard content."""
    content = json.dumps(
        scenes,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def render_storyboard(scenes, client, output_path):
    """Generate a narrated MP4 from storyboard scenes."""

    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Storyboard must contain at least one scene.")

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if True:
        if RESUME_FOLDER:
            temp_dir = Path(RESUME_FOLDER).resolve()
            if not temp_dir.is_dir():
                raise ValueError(f"Resume folder does not exist: {temp_dir}")
            print(f"Resuming from folder: {temp_dir}")
        else:
            debug_root = Path("generated_videos").resolve()
            debug_root.mkdir(parents=True, exist_ok=True)
            temp_dir = Path(
                tempfile.mkdtemp(prefix="scene_debug_", dir=debug_root)
            )
            print(f"Scene files saved in: {temp_dir}")
        fingerprint = storyboard_fingerprint(scenes)
        metadata_path = temp_dir / "storyboard_metadata.json"

        if RESUME_FOLDER:
            if not metadata_path.is_file():
                raise ValueError(
                    "Cannot resume: storyboard metadata is missing."
                )
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata.get("fingerprint") != fingerprint:
                raise ValueError(
                    "Cannot resume: storyboard does not match saved scenes."
                )
            print("Storyboard fingerprint verified.", flush=True)
        else:
            metadata_path.write_text(
                json.dumps(
                    {"fingerprint": fingerprint, "scene_count": len(scenes)},
                    indent=2,
                ),
                encoding="utf-8",
            )

        scene_videos = []

        for index, scene in enumerate(scenes):
            narration = str(scene.get("narration", "")).strip()

            if not narration:
                narration = str(scene.get("title", "Untitled Scene"))

            image_path = temp_dir / f"scene_{index}.png"
            audio_path = temp_dir / f"scene_{index}.mp3"
            video_path = temp_dir / f"scene_{index}.mp4"

            if RESUME_FOLDER and is_valid_narrated_scene(video_path):
                print(f"Reusing completed scene {index + 1}: {video_path}", flush=True)
                scene_videos.append(video_path)
                continue

            if RESUME_FOLDER and image_path.is_file():
                try:
                    with Image.open(image_path) as saved_image:
                        saved_image.verify()
                    print(f"Reusing image for scene {index + 1}", flush=True)
                except Exception:
                    image_path.unlink(missing_ok=True)

            saved_image_id = scene.get("image_id")

            if saved_image_id:
                import re
                import shutil

                if not isinstance(saved_image_id, str) or not re.fullmatch(
                    r"[0-9a-f]{32}\\.png", saved_image_id
                ):
                    raise ValueError(f"Invalid storyboard image ID for scene {index + 1}.")

                saved_image_path = (
                    Path(__file__).parent
                    / "generated_storyboard_images"
                    / saved_image_id
                )

                if not saved_image_path.is_file():
                    raise FileNotFoundError(
                        f"Storyboard image missing for scene {index + 1}: {saved_image_id}"
                    )

                with Image.open(saved_image_path) as saved_image:
                    saved_image.verify()

                shutil.copyfile(saved_image_path, image_path)
                print(
                    f"Using saved storyboard image for scene {index + 1}",
                    flush=True,
                )

            elif not image_path.is_file():
                try:
                    generate_scene_image(
                        client,
                        scene.get("visual", ""),
                        image_path,
                    )
                except Exception as error:
                    print(f"AI image generation failed for scene {index}: {error}")
                    create_scene_image(scene, image_path)

            if RESUME_FOLDER and audio_path.is_file():
                probe = subprocess.run(
                    [
                        "ffprobe", "-v", "error",
                        "-select_streams", "a:0",
                        "-show_entries", "stream=codec_type",
                        "-of", "default=noprint_wrappers=1:nokey=1",
                        str(audio_path),
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if probe.returncode == 0 and probe.stdout.strip() == "audio":
                    print(f"Reusing narration for scene {index + 1}", flush=True)
                else:
                    audio_path.unlink(missing_ok=True)

            if not audio_path.is_file():
                with client.audio.speech.with_streaming_response.create(
                    model="tts-1",
                    voice="alloy",
                    input=narration,
                    response_format="mp3",
                ) as response:
                    response.stream_to_file(audio_path)

            if USE_RUNWAY:
                moving_path = temp_dir / f"moving_{index}.mp4"
                if RESUME_FOLDER and is_valid_scene_video(moving_path):
                    print(
                        f"Reusing Runway animation for scene {index + 1}",
                        flush=True,
                    )
                else:
                    try:
                        generate_moving_scene(
                            image_path,
                            moving_path,
                            scene.get("visual", "") or scene.get("title", "A cinematic scene"),
                        )
                    except Exception as error:
                        print(
                            f"Runway failed for scene {index + 1}: {error}",
                            flush=True,
                        )
                        print("Using narrated static-image fallback.", flush=True)
                        create_scene_video(image_path, audio_path, video_path)

                if not is_valid_scene_video(video_path):
                    if not is_valid_scene_video(moving_path):
                        raise RuntimeError(
                            f"Scene {index + 1}: no valid moving video or fallback."
                        )
                    create_moving_scene_video(
                        moving_path, audio_path, video_path
                    )
            else:
                create_scene_video(image_path, audio_path, video_path)

            scene_videos.append(video_path)

        concat_file = temp_dir / "scenes.txt"

        with concat_file.open("w", encoding="utf-8") as file:
            for video_path in scene_videos:
                file.write(f"file '{video_path}'\n")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                "-movflags", "+faststart",
                str(output_path),
            ],
            check=True,
        )

    return output_path

