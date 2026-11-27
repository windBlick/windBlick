"""Domain errors for turbine geometry.

Framework-free: the API layer maps these to HTTP responses. Carrying a
machine-readable ``code`` keeps the contract's error codes in one place.
"""


class InvalidTurbineGeometry(Exception):
    """Raised when a turbine dimension is outside the open interval (0, 500) meters."""

    code = "VALIDATION_ERROR"  # contract: HTTP 422

    def __init__(self, field: str, value: float) -> None:
        self.field = field
        self.value = value
        super().__init__(
            f"{field} must be greater than 0 and less than 500 m, got {value!r}"
        )
