import base64
import time
from pathlib import Path
from urllib.request import urlretrieve

from dotenv import load_dotenv
from PIL import Image, ImageOps
from runwayml import RunwayML


def generate_moving_scene(image_path, output_path, prompt):
    """Animate an existing image with Runway Gen-4 Turbo."""

    load_dotenv(Path(__file__).parent / ".env")

    image_path = Path(image_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    task = client.image_to_video.create(
        model="gen4_turbo",
        prompt_image=image_uri,
        prompt_text=str(prompt)[:1000],
        ratio="1280:720",
        duration=5,
    )

    print(f"Runway task created: {task.id}")

    for _ in range(120):
        task = client.tasks.retrieve(task.id)

        if task.status == "SUCCEEDED":
            if not task.output:
                raise RuntimeError("Runway returned no video URL.")
            urlretrieve(task.output[0], output_path)
            return output_path

        if task.status == "FAILED":
            raise RuntimeError(f"Runway generation failed: {task.failure}")

        time.sleep(5)

    raise TimeoutError(f"Runway task still pending: {task.id}")
