""" Bot AI """


def generate_bot_reply(user_message: str, username: str) -> str:
    """Generates a fake bot reply based on user input."""
    # Example: Simple logic for bot replies
    if "hello" in user_message.lower():
        return f"Hello {username}, how can I assist you?"
    elif "how are you" in user_message.lower():
        return "I'm just a bot, but I'm doing great! Thanks for asking."
    else:
        return "That's interesting! Tell me more."