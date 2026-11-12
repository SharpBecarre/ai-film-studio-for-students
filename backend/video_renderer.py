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
from animation_review import load_review


USE_RUNWAY = os.getenv("USE_RUNWAY", "false").lower() == "true"
RESUME_FOLDER = os.getenv("VIDEO_RESUME_FOLDER", "").strip()
ALLOW_RUNWAY_RETRY = os.getenv(
    "ALLOW_RUNWAY_RETRY", "false"
).lower() == "true"

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
    """Play animation once, then hold its final frame until narration ends."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg", "-y",
        "-i", str(moving_video_path),
        "-i", str(audio_path),
        "-filter_complex",
        "[0:v]tpad=stop_mode=clone:stop_duration=120[v]",
        "-map", "[v]",
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



def assemble_with_crossfades(
    scene_videos, output_path, fade=0.5, narration_pause=0.7,
    opening_fade=0.5, opening_delay=1.0
):
    """Crossfade first, then begin the next scene's narration."""
    scene_videos = [Path(p).resolve() for p in scene_videos]
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not scene_videos:
        raise ValueError("No scene videos to assemble.")

    if fade < 0 or narration_pause < fade:
        raise ValueError("Narration pause must be at least the fade duration.")

    if opening_fade < 0 or opening_delay < opening_fade:
        raise ValueError("Opening delay must be at least opening fade.")

    def get_audio_duration(path):
        result = subprocess.check_output([
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=duration",
            "-of", "json", str(path),
        ], text=True)

        streams = json.loads(result).get("streams", [])
        if not streams or "duration" not in streams[0]:
            raise ValueError(f"Cannot determine audio duration: {path}")

        return float(streams[0]["duration"])

    durations = [get_audio_duration(p) for p in scene_videos]
    scene_count = len(scene_videos)

    filters = []

    for i, duration in enumerate(durations):
        # Each incoming scene begins visually before its narration.
        lead = narration_pause if i > 0 else opening_delay

        # Hold the previous scene's final frame during the fade.
        tail = fade if i < scene_count - 1 else 0

        filters.append(
            f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,fps=24,format=yuv420p,"
            f"trim=duration={duration:.6f},"
            f"tpad=start_mode=clone:start_duration={lead:.6f}:"
            f"stop_mode=clone:stop_duration={tail:.6f},"
            f"settb=AVTB,setpts=PTS-STARTPTS[v{i}]"
        )

        filters.append(
            f"[{i}:a]aresample=48000,"
            f"atrim=duration={duration:.6f},"
            f"asetpts=PTS-STARTPTS[a{i}]"
        )

    if opening_fade > 0:
        filters.append(
            f"[v0]fade=t=in:st=0:d={opening_fade:.6f}[opening]"
        )
        first_video = "opening"
    else:
        first_video = "v0"

    previous_video = first_video
    offset = opening_delay + durations[0]

    for i in range(1, scene_count):
        video_out = f"x{i}"

        filters.append(
            f"[{previous_video}][v{i}]"
            f"xfade=transition=fade:duration={fade}:"
            f"offset={offset:.6f}[{video_out}]"
        )

        previous_video = video_out

        if i < scene_count - 1:
            offset += durations[i] + narration_pause

    audio_parts = []

    if opening_delay > 0:
        filters.append(
            f"anullsrc=r=48000:cl=stereo,"
            f"atrim=duration={opening_delay:.6f}[opening_silence]"
        )
        audio_parts.append("[opening_silence]")

    for i in range(scene_count):
        audio_parts.append(f"[a{i}]")

        if i < scene_count - 1:
            filters.append(
                f"anullsrc=r=48000:cl=stereo,"
                f"atrim=duration={narration_pause:.6f}[sil{i}]"
            )
            audio_parts.append(f"[sil{i}]")

    filters.append(
        f"{''.join(audio_parts)}"
        f"concat=n={len(audio_parts)}:v=0:a=1[aout]"
    )

    command = ["ffmpeg", "-y", "-loglevel", "error"]

    for scene in scene_videos:
        command.extend(["-i", str(scene)])

    command.extend([
        "-filter_complex", ";".join(filters),
        "-map", f"[{previous_video}]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ])

    subprocess.run(command, check=True)
    return output_path



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

            moving_path = temp_dir / f"moving_{index}.mp4"

            review = load_review(temp_dir, index + 1)
            review_status = (
                review.get("status") if review else None
            )

            can_reuse_scene = (
                RESUME_FOLDER
                and not USE_RUNWAY
                and is_valid_narrated_scene(video_path)
            )

            if can_reuse_scene:
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
                    r"[0-9a-f]{32}\.png", saved_image_id
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

            if USE_RUNWAY and review_status != "approved":
                print(
                    f"Scene {index + 1}: animation status is "
                    f"{review_status or 'unreviewed'}. "
                    "Using original storyboard image without Runway request.",
                    flush=True,
                )
                create_scene_video(image_path, audio_path, video_path)

            elif USE_RUNWAY:
                moving_path = temp_dir / f"moving_{index}.mp4"
                if RESUME_FOLDER and is_valid_scene_video(moving_path):
                    print(
                        f"Reusing Runway animation for scene {index + 1}",
                        flush=True,
                    )
                else:
                    raise RuntimeError(
                        f"Scene {index + 1}: approved Runway animation "
                        "is missing or invalid. No paid generation "
                        "will be attempted. Generate a replacement "
                        "separately with explicit authorization."
                    )

                    if RESUME_FOLDER:
                        retry_setting = os.getenv(
                            "RUNWAY_RETRY_SCENES", ""
                        ).strip()

                        try:
                            retry_scenes = {
                                int(value.strip())
                                for value in retry_setting.split(",")
                                if value.strip()
                            }
                        except ValueError:
                            raise ValueError(
                                "RUNWAY_RETRY_SCENES must contain "
                                "comma-separated scene numbers."
                            )

                        if (
                            not ALLOW_RUNWAY_RETRY
                            or index + 1 not in retry_scenes
                        ):
                            raise RuntimeError(
                                f"Scene {index + 1}: missing Runway animation. "
                                "Paid regeneration is blocked. "
                                "Authorize this scene explicitly using "
                                "ALLOW_RUNWAY_RETRY=true and "
                                "RUNWAY_RETRY_SCENES."
                            )

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

                        failure_record = {
                            "scene_index": index,
                            "scene_number": index + 1,
                            "status": "static_fallback",
                            "provider": "runway",
                            "error_type": type(error).__name__,
                            "error_message": str(error),
                            "retry_available": True,
                        }

                        failure_path = temp_dir / f"scene_{index}_failure.json"
                        failure_path.write_text(
                            json.dumps(failure_record, indent=2),
                            encoding="utf-8",
                        )

                        print(
                            f"Runway failure details saved: {failure_path}",
                            flush=True,
                        )

                        create_scene_video(image_path, audio_path, video_path)

                if not is_valid_scene_video(moving_path):
                    raise RuntimeError(
                        f"Scene {index + 1}: approved Runway clip is invalid."
                    )

                create_moving_scene_video(
                    moving_path, audio_path, video_path
                )
            else:
                create_scene_video(image_path, audio_path, video_path)

            scene_videos.append(video_path)

        assemble_with_crossfades(
            scene_videos,
            output_path,
            fade=0.5,
        )

    return output_path

