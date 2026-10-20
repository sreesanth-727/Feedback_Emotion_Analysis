import unicodedata


def clean_text(text: str) -> str:
    """
    Clean and validate feedback text.

    - Strips leading, trailing, and excess internal whitespace.
    - Normalizes unicode characters using NFKC normalization.
    - Validates that the input is a non-empty string.

    Args:
        text: Input string to clean.

    Returns:
        Cleaned, normalized string.

    Raises:
        ValueError: If input is not a string, or is empty/whitespace-only.
    """
    if not isinstance(text, str):
        raise ValueError(f"Feedback text must be a string, got {type(text).__name__}.")

    # Unicode normalization (NFKC decomposes compatibility chars and recomposes canonically)
    normalized = unicodedata.normalize("NFKC", text)

    # Strip excess whitespace, tabs, and newlines
    cleaned = " ".join(normalized.split())

    if not cleaned:
        raise ValueError("Feedback text cannot be empty or whitespace only.")

    return cleaned
