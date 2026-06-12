import random
import string

def generate_invite_code():
    """Generates a 4-character CTF invite code."""
    return "CTF-" + "".join(
        random.choices(string.ascii_uppercase + string.digits, k=4)
    )
