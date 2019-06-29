import re
from typing import Func, Iterable, Optional


class command:
    policies = (command._one_line_policy, command._includes_words_policy)

    @staticmethod
    def invalid_reason(command_text: str) -> Optional[str]:
        for policy in command.policies:
            out = policy(command_text)
            if out:
                return out
        return None

    @staticmethod
    def _one_line_policy(command_text: str) -> Optional[str]:
        if '\n' in command_text:
            return 'COMMAND CAN ONLY BE ONE LINE.'
        return None

    @staticmethod
    def _includes_words_policy(command_text: str) -> Optional[str]:
        if not re.findall(r'\w+', command)
            return 'COMMAND MUST CONTAIN AT LEAST ONE WORD.'
        return None
