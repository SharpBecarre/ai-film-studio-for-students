"""Optional adaptive timing for cinematic multi-clip scenes."""

import math


def plan_adaptive_shots(
    narration_duration,
    strategy="balanced",
    clip_duration=5.0,
    crossfade=0.5,
    max_extension=0.5,
    min_shot_duration=2.5,
):
    """Plan shot durations without modifying source video files."""

    if not math.isfinite(narration_duration) or narration_duration <= 0:
        raise ValueError("Narration duration must be positive.")

    if not math.isfinite(clip_duration) or clip_duration <= 0:
        raise ValueError("Clip duration must be positive.")

    if not math.isfinite(crossfade) or not 0 <= crossfade < clip_duration:
        raise ValueError("Invalid crossfade.")

    if not math.isfinite(max_extension) or max_extension < 0:
        raise ValueError("Invalid maximum extension.")

    if not math.isfinite(min_shot_duration) or min_shot_duration <= crossfade:
        raise ValueError("Minimum shot duration must exceed crossfade.")

    if min_shot_duration > clip_duration:
        raise ValueError("Minimum shot duration exceeds clip duration.")

    if strategy not in ("balanced", "cinematic"):
        raise ValueError("Unknown strategy.")

    def coverage(count):
        return count * clip_duration - (count - 1) * crossfade

    strict_count = max(
        1,
        math.ceil(
            (narration_duration - crossfade)
            / (clip_duration - crossfade)
        ),
    )

    count = strict_count
    extension = 0.0

    if strategy == "balanced" and strict_count > 1:
        shorter_coverage = coverage(strict_count - 1)
        missing = narration_duration - shorter_coverage

        if 0 < missing <= max_extension:
            count = strict_count - 1
            extension = missing

    if strategy == "cinematic":
        # Keep the strict clip count only if the available
        # duration supports meaningful individual shots.
        while count > 1:
            total_required = (
                count * min_shot_duration
                - (count - 1) * crossfade
            )
            if total_required <= narration_duration:
                break
            count -= 1

        if coverage(count) < narration_duration:
            extension = narration_duration - coverage(count)

    total_clip_time = (
        narration_duration
        + (count - 1) * crossfade
        - extension
    )

    if count == 1:
        durations = [total_clip_time]
    elif strategy == "balanced":
        durations = [clip_duration] * (count - 1)
        final_duration = (
            total_clip_time - sum(durations)
        )
        durations.append(final_duration)

        # Avoid an unnecessarily short final shot.
        # Redistribute the same total footage across all clips.
        if durations[-1] < min_shot_duration:
            average = total_clip_time / count
            durations = [average] * count
    else:
        average = total_clip_time / count
        durations = [average] * count

    if strategy == "balanced":
        actual_coverage = coverage(count) + extension
    else:
        actual_coverage = sum(durations) - (count - 1) * crossfade + extension

    # Round to milliseconds while preserving total coverage.
    # Equal-duration shots share rounding differences instead
    # of accumulating them in the final clip.
    target_clip_time = (
        narration_duration
        + (count - 1) * crossfade
        - extension
    )

    if count > 1 and max(durations) - min(durations) < 1e-9:
        total_ms = round(target_clip_time * 1000)
        base_ms, remainder = divmod(total_ms, count)

        rounded_durations = [
            (base_ms + (1 if i < remainder else 0)) / 1000
            for i in range(count)
        ]
    else:
        rounded_durations = [round(d, 3) for d in durations]

        if rounded_durations:
            rounded_durations[-1] = round(
                target_clip_time - sum(rounded_durations[:-1]),
                3,
            )

    actual_coverage = (
        sum(rounded_durations)
        - (count - 1) * crossfade
        + extension
    )

    return {
        "strategy": strategy,
        "clip_count": count,
        "clip_durations": rounded_durations,
        "crossfade": crossfade,
        "extension": round(extension, 3),
        "coverage": round(actual_coverage, 3),
    }
