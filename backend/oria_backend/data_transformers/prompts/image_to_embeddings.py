def generate_image_to_embeddings_prompt(
    image_description: str, emotions: list[str], user_description: str
) -> str:
    """
    Generate a concise, embedding-friendly representation of image and emotional content.

    Args:
        image_description (str): Description of the image content
        emotions (list[str]): List of emotions associated with the image
        user_description (str): User's description or context

    Returns:
        str: A formatted string suitable for embedding generation
    """
    # Clean inputs and join emotions
    emotions_text = ", ".join(emotions).strip()
    image_description = image_description.strip()
    user_description = user_description.strip() if user_description else ""

    # Combine descriptions if both exist
    full_description = image_description
    if user_description:
        full_description = f"{image_description} {user_description}"

    return f"""
image_attributes:
emotions: {emotions_text}
visual_content: {full_description}

emotion_profile: scene conveying {emotions_text}
visual_elements: image showing {image_description}
context: {user_description}
musical_alignment: would pair well with music that evokes {emotions_text}
"""
