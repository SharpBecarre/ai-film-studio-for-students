import base64
from pathlib import Path


def generate_scene_image(client, visual_prompt, output_path):
    """Generate an AI image from a storyboard visual description."""

    prompt = str(visual_prompt).strip()

    if not prompt:
        raise ValueError("A visual description is required.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = client.images.generate(
        model="gpt-image-1-mini",
        prompt=(
            "Create a cinematic, visually engaging image for "
            "an educational short film. "
            "Use a widescreen composition. "
            "Do not include captions, text, or watermarks. "
            f"Scene description: {prompt}"
        ),
        size="1536x1024",
        quality="low",
    )

    image_data = result.data[0].b64_json

    if not image_data:
        raise RuntimeError("The image API returned no image data.")

    output_path.write_bytes(base64.b64decode(image_data))

    return output_path
