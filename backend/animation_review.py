import json
import os
from datetime import datetime, timezone
from pathlib import Path


VALID_STATUSES = {
    "pending_review",
    "approved",
    "rejected",
}


def save_review(folder, scene_number, status, notes=""):
    """Save a student's animation review decision."""

    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid review status: {status}")

    if not isinstance(scene_number, int) or scene_number < 1:
        raise ValueError("Scene number must be a positive integer.")

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    review_path = folder / f"scene_{scene_number - 1}_review.json"

    record = {
        "scene_number": scene_number,
        "scene_index": scene_number - 1,
        "status": status,
        "notes": notes,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    temporary_path = review_path.with_suffix(".json.tmp")

    temporary_path.write_text(
        json.dumps(record, indent=2),
        encoding="utf-8",
    )

    os.replace(temporary_path, review_path)

    return review_path


def load_review(folder, scene_number):
    """Read an existing review record."""

    review_path = (
        Path(folder) / f"scene_{scene_number - 1}_review.json"
    )

    if not review_path.is_file():
        return None

    return json.loads(review_path.read_text(encoding="utf-8"))
