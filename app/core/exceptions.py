class AuthenticationError(Exception):
    """Custom exception for authentication failures."""

    def __init__(self, message: str = "Authentication failed"):
        self.detail = message
        super().__init__(self.detail)


class AuthorizationError(Exception):
    """Custom exception for authorization failures (e.g., insufficient permissions)."""

    def __init__(self, message: str = "Not authorized to perform this action"):
        self.detail = message
        super().__init__(self.detail)
