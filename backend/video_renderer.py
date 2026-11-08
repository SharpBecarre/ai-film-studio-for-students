from pathlib import Path
import textwrap
import subprocess
import tempfile
import uuid

from PIL import Image, ImageDraw, ImageFont


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

def render_storyboard(scenes, client, output_path):
    """Generate a narrated MP4 from storyboard scenes."""

    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Storyboard must contain at least one scene.")

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        scene_videos = []

        for index, scene in enumerate(scenes):
            narration = str(scene.get("narration", "")).strip()

            if not narration:
                narration = str(scene.get("title", "Untitled Scene"))

            image_path = temp_dir / f"scene_{index}.png"
            audio_path = temp_dir / f"scene_{index}.mp3"
            video_path = temp_dir / f"scene_{index}.mp4"

            create_scene_image(scene, image_path)

            with client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="alloy",
                input=narration,
                response_format="mp3",
            ) as response:
                response.stream_to_file(audio_path)

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

