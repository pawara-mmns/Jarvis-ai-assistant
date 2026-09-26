from enum import StrEnum


class AssistantState(StrEnum):
    SLEEPING = "sleeping"
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    EXECUTING = "executing"
    SPEAKING = "speaking"
    CONFIRMATION = "confirmation"
    ERROR = "error"
