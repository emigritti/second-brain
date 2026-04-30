import os
import base64
from typing import List, Dict

_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def describe_images(image_paths: List[str], slug: str) -> Dict[str, str]:
    """
    Generate descriptions for a list of extracted images using Claude API.

    Args:
        image_paths: List of absolute paths to the extracted images.
        slug: The slug of the document (used for context).

    Returns:
        A dictionary mapping image_path -> generated description.
    """
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    results = {}

    for path in image_paths:
        ext = os.path.splitext(path)[1].lower()
        media_type = _MEDIA_TYPES.get(ext)
        if media_type is None:
            print(f"[vision] Skipping unsupported image format '{ext}': {path}")
            continue
        try:
            base64_image = encode_image_to_base64(path)
            response = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=300,
                system=f"You are an expert OCR and image analysis system. Describe the contents of this image extracted from the document '{slug}'. If it is a chart, summarize its data. If it is a diagram, explain its meaning. If it is text, transcribe it. Be concise but thorough.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": "Describe this image in detail so it can be indexed for search."
                            }
                        ]
                    }
                ]
            )
            results[path] = response.content[0].text.strip() if response.content else ""
        except Exception as e:
            print(f"Failed to describe image {path}: {e}")
            results[path] = "Image could not be described."

    return results
