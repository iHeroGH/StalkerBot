BLACKLISTED_CHARACTERS: list[str] = [
    "`",
    "\\", # Keep \\ at the end as to interfere with the rest of the message
]

MIN_INPUT_LENGTH = 2
MAX_INPUT_LENGTH = 150

def has_blacklisted(input: str) -> bool:
    """
    Returns a bool denoting the existance of a blacklisted character in the input

    Parameters
    ----------
    input : str
        The input string to check
    Returns
    -------
    is_blacklisted : bool
        True if the string is blacklisted, False otherwise
    """
    return any([blacklisted in input for blacklisted in BLACKLISTED_CHARACTERS])

def get_blacklisted_error() -> str:
    return (
        "Your input cannot contain "
        + ", ".join(BLACKLISTED_CHARACTERS[:-1])
        + (f", or {BLACKLISTED_CHARACTERS[-1]}"
            if len(BLACKLISTED_CHARACTERS) > 1
            else f"{BLACKLISTED_CHARACTERS[-1]}")
        + " ."
    )