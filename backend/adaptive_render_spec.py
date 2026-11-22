"""Validated adaptive scene timing specifications.

This module does not render video or call external APIs.
"""

import hashlib
import json
import math

from adaptive_shot_planner import plan_adaptive_shots


def build_adaptive_render_spec(
    narration_duration,
    strategy="balanced",
    clip_duration=5.0,
    crossfade=0.5,
):
    """Build a deterministic, narration-aware render specification."""

    plan = plan_adaptive_shots(
        narration_duration=narration_duration,
        strategy=strategy,
        clip_duration=clip_duration,
        crossfade=crossfade,
    )

    durations = plan["clip_durations"]
    extension = plan["extension"]

    if not durations:
        raise ValueError("No shots were planned.")

    if any(
        not math.isfinite(d) or d <= 0 or d > clip_duration
        for d in durations
    ):
        raise ValueError("Invalid planned clip duration.")

    if len(durations) > 1 and any(
        d <= crossfade for d in durations
    ):
        raise ValueError("Clip duration must exceed crossfade.")

    offsets = []
    elapsed = 0.0

    for index, duration in enumerate(durations):
        if index:
            elapsed -= crossfade

        offsets.append(round(elapsed, 3))
        elapsed += duration

    coverage = elapsed + extension

    if abs(coverage - narration_duration) > 0.001:
        raise ValueError(
            "Adaptive render specification does not cover narration."
        )

    specification = {
        "schema_version": 2,
        "strategy": strategy,
        "clip_count": len(durations),
        "clip_durations": durations,
        "clip_duration_limit": clip_duration,
        "crossfade": crossfade,
        "crossfade_offsets": offsets[1:],
        "extension": extension,
        "narration_duration": round(narration_duration, 3),
    }

    encoded = json.dumps(
        specification,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    specification["timing_sha256"] = hashlib.sha256(
        encoded
    ).hexdigest()

    return specification
