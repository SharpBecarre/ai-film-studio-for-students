"""Assemble multiple video clips into one narrated scene."""

import json
import subprocess
from pathlib import Path

from cinematic_director import calculate_shot_timeline


def probe_duration(path):
    """Read media duration without modifying the file."""
    result = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json", str(path),
        ],
        text=True,
    )
    return float(json.loads(result)["format"]["duration"])


def assemble_scene_clips(
    clip_paths,
    narration_path,
    output_path,
    clip_duration=5.0,
    crossfade=0.5,
):
    """Combine clips with crossfades and continuous narration."""

    clips = [Path(p).resolve() for p in clip_paths]
    narration = Path(narration_path).resolve()
    output = Path(output_path).resolve()

    if not clips:
        raise ValueError("At least one video clip is required.")

    if not 0 <= crossfade < clip_duration:
        raise ValueError("Invalid crossfade duration.")

    if not narration.is_file():
        raise FileNotFoundError(narration)

    for clip in clips:
        if not clip.is_file():
            raise FileNotFoundError(clip)

    if output.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing file: {output}"
        )

    narration_duration = probe_duration(narration)

    timeline = calculate_shot_timeline(
        required_duration=narration_duration,
        clip_duration=clip_duration,
        crossfade_duration=crossfade,
    )

    if len(clips) != len(timeline):
        raise ValueError(
            f"Expected {len(timeline)} clips, "
            f"received {len(clips)}."
        )

    for index, clip in enumerate(clips):
        available = probe_duration(clip)
        required = (
            timeline[index]["end_seconds"]
            - timeline[index]["start_seconds"]
        )
        if available + 0.05 < required:
            raise ValueError(
                f"Clip {index + 1} is too short: "
                f"{available:.3f}s available, "
                f"{required:.3f}s required."
            )

    filters = []

    for index, shot in enumerate(timeline):
        duration = (
            shot["end_seconds"] - shot["start_seconds"]
        )

        filters.append(
            f"[{index}:v]fps=24,"
            f"scale=1280:720:force_original_aspect_ratio=decrease,"
            f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,format=yuv420p,"
            f"trim=duration={duration:.6f},"
            f"settb=AVTB,setpts=PTS-STARTPTS[v{index}]"
        )

    previous = "v0"

    for index in range(1, len(clips)):
        offset = timeline[index]["start_seconds"]

        filters.append(
            f"[{previous}][v{index}]"
            f"xfade=transition=fade:"
            f"duration={crossfade:.6f}:"
            f"offset={offset:.6f}[x{index}]"
        )
        previous = f"x{index}"

    # A small final-frame extension ensures video covers
    # the complete narration after frame-rate rounding.
    filters.append(
        f"[{previous}]"
        f"tpad=stop_mode=clone:stop_duration=0.1,"
        f"trim=duration={narration_duration + 0.1:.6f}"
        f"[video]"
    )

    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-n"]

    for clip in clips:
        command += ["-i", str(clip)]

    command += ["-i", str(narration)]

    command += [
        "-filter_complex", ";".join(filters),
        "-map", "[video]",
        "-map", f"{len(clips)}:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(output),
    ]

    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, check=True)

    return output


def find_approved_scene_clips(
    scene_directory,
    required_count,
    require_approval=False,
    storyboard_fingerprint=None,
    scene_number=None,
):
    """Find exactly the required pre-existing scene clips.

    This function never generates, modifies, or downloads clips.
    """
    directory = Path(scene_directory).resolve()

    if not isinstance(required_count, int) or required_count < 1:
        raise ValueError("required_count must be a positive integer.")

    if not directory.is_dir():
        raise FileNotFoundError(
            f"Scene clip directory does not exist: {directory}"
        )

    clips = [
        directory / f"clip_{index:03d}.mp4"
        for index in range(1, required_count + 1)
    ]

    missing = [
        clip.name for clip in clips
        if not clip.is_file()
    ]

    if missing:
        raise FileNotFoundError(
            f"Missing required clips in {directory}: "
            + ", ".join(missing)
            + ". No paid generation will be attempted."
        )

    invalid = [
        clip.name for clip in clips
        if not is_playable_video(clip)
    ]

    if invalid:
        raise ValueError(
            f"Invalid video clips in {directory}: "
            + ", ".join(invalid)
            + ". No paid generation will be attempted."
        )

    if require_approval:
        if storyboard_fingerprint is None or scene_number is None:
            raise ValueError(
                "Approved clip discovery requires storyboard "
                "fingerprint and scene number."
            )

        approval_path = directory / "approvals.json"

        if not approval_path.is_file():
            raise FileNotFoundError(
                f"Approval record missing: {approval_path}. "
                "No paid generation will be attempted."
            )

        with approval_path.open("r", encoding="utf-8") as file:
            approval_record = json.load(file)

        validate_clip_approvals(
            approval_record,
            required_count,
            directory,
            storyboard_fingerprint=storyboard_fingerprint,
            scene_number=scene_number,
        )

    return clips


def is_playable_video(path):
    """Check that a file contains a video stream with positive duration."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries",
                "stream=codec_type:format=duration",
                "-of", "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        duration = float(
            data.get("format", {}).get("duration", 0)
        )

        return (
            bool(streams)
            and streams[0].get("codec_type") == "video"
            and duration > 0
        )

    except (
        subprocess.CalledProcessError,
        ValueError,
        KeyError,
        TypeError,
        OSError,
    ):
        return False

def validate_clip_approvals(
    record,
    required_count,
    scene_directory=None,
    storyboard_fingerprint=None,
    scene_number=None,
):
    """Require explicit approval for every planned scene clip."""

    if not isinstance(record, dict):
        raise ValueError("Approval record must be an object.")

    if storyboard_fingerprint is not None:
        if (
            not isinstance(storyboard_fingerprint, str)
            or len(storyboard_fingerprint) != 64
            or any(
                char not in "0123456789abcdef"
                for char in storyboard_fingerprint
            )
        ):
            raise ValueError("Invalid expected storyboard fingerprint.")

        if record.get("storyboard_fingerprint") != storyboard_fingerprint:
            raise ValueError(
                "Approval belongs to a different storyboard."
            )

    if scene_number is not None:
        if (
            not isinstance(scene_number, int)
            or isinstance(scene_number, bool)
            or scene_number < 1
        ):
            raise ValueError("Invalid expected scene number.")

        if record.get("scene_number") != scene_number:
            raise ValueError(
                "Approval belongs to a different scene."
            )

    clips = record.get("clips")

    if not isinstance(clips, list):
        raise ValueError("Approval record must contain a clips list.")

    if (
        not isinstance(required_count, int)
        or isinstance(required_count, bool)
        or required_count < 1
    ):
        raise ValueError("Invalid required clip count.")

    if len(clips) != required_count:
        raise ValueError(
            "Approval count does not match required clips."
        )

    for index, clip in enumerate(clips, 1):
        if not isinstance(clip, dict):
            raise ValueError("Invalid clip approval entry.")

        expected = f"clip_{index:03d}.mp4"

        if clip.get("clip_number") != index:
            raise ValueError(
                f"Incorrect clip number: {index}"
            )

        if clip.get("filename") != expected:
            raise ValueError(
                f"Incorrect filename: {expected}"
            )

        if clip.get("status") != "approved":
            raise ValueError(
                f"Clip {index} is not approved."
            )

        if scene_directory is not None:
            import hmac

            expected_hash = clip.get("sha256")

            if (
                not isinstance(expected_hash, str)
                or len(expected_hash) != 64
                or any(
                    char not in "0123456789abcdef"
                    for char in expected_hash
                )
            ):
                raise ValueError(
                    f"Clip {index}: missing or invalid SHA-256."
                )

            video_path = (
                Path(scene_directory).resolve() / expected
            )

            if not is_playable_video(video_path):
                raise ValueError(
                    f"Clip {index}: video is not playable."
                )

            actual_hash = video_sha256(video_path)

            if not hmac.compare_digest(
                actual_hash, expected_hash
            ):
                raise ValueError(
                    f"Clip {index}: video fingerprint mismatch."
                )

    return True

def video_sha256(path):
    """Calculate a video file's SHA-256 fingerprint without modifying it."""
    import hashlib

    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()

def calculate_render_identity(
    storyboard_fingerprint_value,
    scene_number,
    narration_path,
    clip_paths,
    clip_duration=5.0,
    crossfade=0.5,
):
    """Fingerprint the exact inputs used for one rendered scene."""

    import hashlib
    import json

    if not isinstance(storyboard_fingerprint_value, str) or not storyboard_fingerprint_value:
        raise ValueError("Storyboard fingerprint is required.")

    if (
        not isinstance(scene_number, int)
        or isinstance(scene_number, bool)
        or scene_number < 1
    ):
        raise ValueError("Scene number must be a positive integer.")

    narration = Path(narration_path).resolve()
    clips = [Path(path).resolve() for path in clip_paths]

    if not narration.is_file():
        raise FileNotFoundError(narration)

    if not clips:
        raise ValueError("At least one source clip is required.")

    for clip in clips:
        if not clip.is_file():
            raise FileNotFoundError(clip)

    if not 0 <= crossfade < clip_duration:
        raise ValueError("Invalid clip timing settings.")

    identity_data = {
        "schema_version": 1,
        "storyboard_fingerprint": storyboard_fingerprint_value,
        "scene_number": scene_number,
        "narration_sha256": video_sha256(narration),
        "clip_sha256": [
            video_sha256(clip) for clip in clips
        ],
        "clip_duration": clip_duration,
        "crossfade": crossfade,
    }

    encoded = json.dumps(
        identity_data,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()

def build_render_metadata(
    storyboard_fingerprint_value,
    scene_number,
    narration_path,
    clip_paths,
    output_path,
    clip_duration=5.0,
    crossfade=0.5,
):
    """Build metadata for a completed narrated multi-clip scene."""

    output = Path(output_path).resolve()

    if not output.is_file():
        raise FileNotFoundError(
            f"Completed scene video missing: {output}"
        )

    if not is_playable_video(output):
        raise ValueError(
            f"Completed scene video is invalid: {output}"
        )

    import subprocess

    audio_probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if (
        audio_probe.returncode != 0
        or audio_probe.stdout.strip() != "audio"
    ):
        raise ValueError(
            "Completed scene video has no valid audio stream."
        )

    render_identity = calculate_render_identity(
        storyboard_fingerprint_value=storyboard_fingerprint_value,
        scene_number=scene_number,
        narration_path=narration_path,
        clip_paths=clip_paths,
        clip_duration=clip_duration,
        crossfade=crossfade,
    )

    return {
        "schema_version": 1,
        "storyboard_fingerprint": storyboard_fingerprint_value,
        "scene_number": scene_number,
        "render_identity": render_identity,
        "output_filename": output.name,
        "output_sha256": video_sha256(output),
        "clip_duration": clip_duration,
        "crossfade": crossfade,
    }

def validate_render_metadata(
    metadata,
    storyboard_fingerprint_value,
    scene_number,
    narration_path,
    clip_paths,
    output_path,
    clip_duration=5.0,
    crossfade=0.5,
):
    """Verify completed scene metadata against current inputs."""

    import hmac

    if not isinstance(metadata, dict):
        raise ValueError("Render metadata must be an object.")

    if metadata.get("schema_version") != 1:
        raise ValueError("Unsupported render metadata version.")

    if metadata.get("storyboard_fingerprint") != storyboard_fingerprint_value:
        raise ValueError("Render metadata storyboard mismatch.")

    if metadata.get("scene_number") != scene_number:
        raise ValueError("Render metadata scene mismatch.")

    output = Path(output_path).resolve()

    if not output.is_file():
        raise FileNotFoundError(
            f"Completed scene missing: {output}"
        )

    if metadata.get("output_filename") != output.name:
        raise ValueError("Completed scene filename mismatch.")

    if not is_playable_video(output):
        raise ValueError("Completed scene video is invalid.")

    import subprocess

    audio_probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_type",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if (
        audio_probe.returncode != 0
        or audio_probe.stdout.strip() != "audio"
    ):
        raise ValueError("Completed scene audio is invalid.")

    expected_identity = calculate_render_identity(
        storyboard_fingerprint_value=storyboard_fingerprint_value,
        scene_number=scene_number,
        narration_path=narration_path,
        clip_paths=clip_paths,
        clip_duration=clip_duration,
        crossfade=crossfade,
    )

    saved_identity = metadata.get("render_identity")

    if (
        not isinstance(saved_identity, str)
        or not hmac.compare_digest(
            saved_identity,
            expected_identity,
        )
    ):
        raise ValueError("Completed scene input identity mismatch.")

    saved_output_hash = metadata.get("output_sha256")
    actual_output_hash = video_sha256(output)

    if (
        not isinstance(saved_output_hash, str)
        or not hmac.compare_digest(
            saved_output_hash,
            actual_output_hash,
        )
    ):
        raise ValueError("Completed scene output fingerprint mismatch.")

    if (
        metadata.get("clip_duration") != clip_duration
        or metadata.get("crossfade") != crossfade
    ):
        raise ValueError("Completed scene timing settings mismatch.")

    return True
