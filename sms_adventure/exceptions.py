class SMSAdventureError(Exception):
    """Exception base class."""


class CommandPolicyViolationError(SMSAdventureError):
    """Error raised upon encountering a command policy violation."""
