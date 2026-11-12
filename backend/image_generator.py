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
            "Create a photorealistic, cinematic film still suitable "
            "for an animated documentary scene. "
            "Use a widescreen cinematic composition. "
            "The image must contain absolutely no readable text, "
            "letters, numbers, titles, subtitles, logos, labels, "
            "signage, credits, or watermarks. "
            "Do not create title cards, opening credits, posters, "
            "or text overlays. "
            "If the scene description mentions text appearing on "
            "screen, represent the underlying visual concept "
            "without displaying any written words. "
            "Prioritize natural cinematic imagery, realistic lighting, "
            "and visually coherent subjects. "
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
