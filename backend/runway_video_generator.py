import base64
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlretrieve

from dotenv import load_dotenv
from PIL import Image, ImageOps
from runwayml import RunwayML


def save_runway_task_record(path, record):
    """Atomically save a Runway attempt record."""
    record["updated_at"] = datetime.now(timezone.utc).isoformat()
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(temporary, path)


def generate_moving_scene(image_path, output_path, prompt):
    """Animate an existing image with Runway Gen-4 Turbo."""

    load_dotenv(Path(__file__).parent / ".env")

    image_path = Path(image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    attempt_id = uuid.uuid4().hex
    record_path = output_path.parent / (
        f"{output_path.stem}_runway_{attempt_id}.json"
    )

    record = {
        "attempt_id": attempt_id,
        "provider": "runway",
        "model": "gen4_turbo",
        "input_image": str(image_path),
        "output_video": str(output_path),
        "duration_seconds": 5,
        "task_id": None,
        "status": "PREPARING",
        "downloaded": False,
        "error_type": None,
        "error_message": None,
    }

    save_runway_task_record(record_path, record)

    try:
        with Image.open(image_path) as source:
            image = ImageOps.fit(
                source.convert("RGB"),
                (1280, 720),
                method=Image.Resampling.LANCZOS,
            )
            import io
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True)

        image_uri = (
            "data:image/png;base64,"
            + base64.b64encode(buffer.getvalue()).decode("ascii")
        )

        client = RunwayML()

        record["status"] = "SUBMITTING"
        save_runway_task_record(record_path, record)

        task = client.image_to_video.create(
            model="gen4_turbo",
            prompt_image=image_uri,
            prompt_text=str(prompt)[:1000],
            ratio="1280:720",
            duration=5,
        )

        record["task_id"] = task.id
        record["status"] = "SUBMITTED"
        save_runway_task_record(record_path, record)

        print(f"Runway task created: {task.id}", flush=True)
        print(f"Task record: {record_path}", flush=True)

        for _ in range(120):
            task = client.tasks.retrieve(task.id)
            record["status"] = str(task.status)
            save_runway_task_record(record_path, record)

            if task.status == "SUCCEEDED":
                if not task.output:
                    raise RuntimeError("Runway returned no video URL.")

                # Download to a temporary file before replacing the output.
                temporary_video = output_path.with_name(
                    output_path.stem + f".{attempt_id}.tmp.mp4"
                )

                try:
                    urlretrieve(task.output[0], temporary_video)

                    if not temporary_video.is_file() or (
                        temporary_video.stat().st_size == 0
                    ):
                        raise RuntimeError("Downloaded Runway video is empty.")

                    os.replace(temporary_video, output_path)
                finally:
                    temporary_video.unlink(missing_ok=True)

                record["status"] = "SUCCEEDED"
                record["downloaded"] = True
                save_runway_task_record(record_path, record)
                return output_path

            if task.status == "FAILED":
                raise RuntimeError(
                    f"Runway generation failed: {task.failure}"
                )

            time.sleep(5)

        raise TimeoutError(
            f"Runway task still pending: {task.id}"
        )

    except Exception as error:
        record["error_type"] = type(error).__name__
        record["error_message"] = str(error)

        if record["task_id"] and record["status"] not in (
            "SUCCEEDED", "FAILED"
        ):
            record["status"] = "CHECK_REQUIRED"
        elif record["status"] == "SUCCEEDED":
            record["status"] = "DOWNLOAD_FAILED"
        else:
            record["status"] = "FAILED"

        save_runway_task_record(record_path, record)
        raise
