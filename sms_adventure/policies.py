from typing import Func, Iterable, Optional


class command:
    policies = (self._one_line_policy,)

    @staticmethod
    def invalid_reason(command_text: str) -> Optional[str]:
        for policy in self.policies:
            out = policy(command_text)
            if out:
                return out
        return None

    @staticmethod
    def _one_line_policy(command_text: str) -> Optional[str]:
        if '\n' in command_text:
            return 'COMMAND CAN ONLY BE ONE LINE.'
        return None
