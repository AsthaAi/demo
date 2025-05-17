"""
Common exceptions used across the ShopperAI system.
"""


class PolicyVerificationError(Exception):
    """
    Exception raised when policy verification fails.
    Used across agents and tools to indicate access control failures.
    """
    pass
