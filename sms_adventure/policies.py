import re
from typing import Callable, Iterable, Optional


class command:
    @staticmethod
    def invalid_reason(command_text: str) -> Optional[str]:
        for policy in command._policies():
            out = policy(command_text)
            if out:
                return out
        return None

    @staticmethod
    def _one_line_policy(command_text: str) -> Optional[str]:
        if "\n" in command_text:
            return "COMMAND CAN ONLY BE ONE LINE."
        return None

    @staticmethod
    def _includes_words_policy(command_text: str) -> Optional[str]:
        if not re.findall(r"\w+", command_text):
            return "COMMAND MUST CONTAIN AT LEAST ONE WORD."
        return None

    @staticmethod
    def _policies() -> Iterable[Callable[[str], Optional[str]]]:
        return (command._one_line_policy, command._includes_words_policy)
