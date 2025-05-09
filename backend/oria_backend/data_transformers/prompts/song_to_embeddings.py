def generate_song_to_embeddings_prompt(genre: str, mood: str, description: str) -> str:
    """
    Generate a concise, embedding-friendly representation of a song's attributes.

    Args:
        genre (str): The musical genre of the song
        mood (str): The emotional mood/tone of the song
        description (str): Lyrics or description of the song

    Returns:
        str: A formatted string suitable for embedding generation
    """
    # Clean inputs
    genre = genre.strip()
    mood = mood.strip()

    # Extract a sample of the description if it's too long (lyrics)
    if len(description) > 500:
        description_sample = description[:500]
    else:
        description_sample = description

    return f"""
song_attributes:
genre: {genre}
mood: {mood}
lyrics: {description_sample}

musical_elements: {genre} song with {mood} qualities
thematic_elements: lyrics describing {mood} themes
emotional_profile: evokes feelings of {mood}
"""
