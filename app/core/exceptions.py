class AuthenticationError(Exception):
    """Custom exception for authentication failures."""

    def __init__(self, detail: str = "Authentication failed"):
        self.detail = detail
        super().__init__(self.detail)


class AuthorizationError(Exception):
    """Custom exception for authorization failures (e.g., insufficient permissions)."""

    def __init__(self, detail: str = "Not authorized to perform this action"):
        self.detail = detail
        super().__init__(self.detail)
