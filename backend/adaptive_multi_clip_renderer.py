"""Optional adaptive FFmpeg scene renderer.

Uses existing clips and narration only.
Does not call paid APIs or modify the legacy renderer.
"""

from pathlib import Path
import subprocess

from adaptive_render_spec import build_adaptive_render_spec
from multi_clip_renderer import probe_duration


def assemble_adaptive_scene_clips(
    clip_paths,
    narration_path,
    output_path,
    strategy="balanced",
    crossfade=0.5,
):
    """Assemble existing clips with narration-aware shot durations."""

    clips = [Path(p).resolve() for p in clip_paths]
    narration = Path(narration_path).resolve()
    output = Path(output_path).resolve()

    if not narration.is_file():
        raise FileNotFoundError(narration)

    if output.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing file: {output}"
        )

    narration_duration = probe_duration(narration)

    spec = build_adaptive_render_spec(
        narration_duration=narration_duration,
        strategy=strategy,
        crossfade=crossfade,
    )

    durations = spec["clip_durations"]
    offsets = spec["crossfade_offsets"]
    extension = spec["extension"]

    if len(clips) != len(durations):
        raise ValueError(
            f"Expected {len(durations)} clips, received {len(clips)}."
        )

    for index, (clip, required) in enumerate(
        zip(clips, durations), start=1
    ):
        if not clip.is_file():
            raise FileNotFoundError(clip)

        available = probe_duration(clip)

        if available + 0.001 < required:
            raise ValueError(
                f"Clip {index} is too short: "
                f"{available:.3f}s available, "
                f"{required:.3f}s required."
            )

    filters = []

    for index, duration in enumerate(durations):
        filters.append(
            f"[{index}:v]"
            f"fps=24,"
            f"scale=1280:720:force_original_aspect_ratio=decrease,"
            f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,"
            f"setsar=1,format=yuv420p,"
            f"trim=duration={duration:.6f},"
            f"settb=AVTB,setpts=PTS-STARTPTS[v{index}]"
        )

    previous = "v0"

    for index, offset in enumerate(offsets, start=1):
        filters.append(
            f"[{previous}][v{index}]"
            f"xfade=transition=fade:"
            f"duration={crossfade:.6f}:"
            f"offset={offset:.6f}[x{index}]"
        )
        previous = f"x{index}"

    # Freeze the final frame only for the planned extension.
    # A small frame-level safety pad avoids rounding truncation.
    safety_pad = 0.1
    target_duration = narration_duration + safety_pad

    filters.append(
        f"[{previous}]"
        f"tpad=stop_mode=clone:"
        f"stop_duration={extension + safety_pad:.6f},"
        f"trim=duration={target_duration:.6f}"
        f"[video]"
    )

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-n"
    ]

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

    return {
        "output_path": output,
        "specification": spec,
    }
