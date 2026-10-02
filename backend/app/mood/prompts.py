from datetime import datetime, timezone

JOURNAL_PROMPTS: list[str] = [
    "What's one thing that went well today?",
    "What's weighing on you right now?",
    "Describe your energy level today and why.",
    "What's something you're looking forward to?",
    "What would make tomorrow feel a little easier?",
    "Who or what are you grateful for today?",
    "What's a small win you can celebrate?",
]


def prompt_for_today() -> str:
    day_index = datetime.now(timezone.utc).date().toordinal()
    return JOURNAL_PROMPTS[day_index % len(JOURNAL_PROMPTS)]
