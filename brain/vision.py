import os
import base64
from anthropic import Anthropic
from typing import List, Dict

# Assumes ANTHROPIC_API_KEY is set in the environment (.env)
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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
    results = {}
    
    for path in image_paths:
        try:
            base64_image = encode_image_to_base64(path)
            
            # Using Claude 3.5 Haiku for fast and cheap vision tasks
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
                                    "media_type": "image/png",
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
            
            description = response.content[0].text.strip() if response.content else ""
            results[path] = description
            
        except Exception as e:
            print(f"Failed to describe image {path}: {e}")
            results[path] = "Image could not be described."
            
    return results
