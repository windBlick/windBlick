"""Application errors and field paths for the visualization API."""

from collections.abc import Iterable
from typing import TypedDict


class FieldError(TypedDict):
    """An error at a JSON Pointer in the parameters document."""

    path: str
    code: str
    message: str


def pointer(parts: Iterable[str | int]) -> str:
    """Encode a sequence of property names or array indices as a JSON Pointer."""
    return "".join(
        "/" + str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


class VisualizationProblem(Exception):
    """An API error with safe details and optional field or multipart context."""

    def __init__(
        self,
        status: int,
        code: str,
        detail: str,
        *,
        errors: list[FieldError] | None = None,
        part: str | None = None,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.errors = errors if errors is not None else []
        self.part = part


def invalid_parameter(
    path: str, message: str, *, code: str = "VALIDATION_ERROR"
) -> VisualizationProblem:
    """Return a validation problem at a single request field."""
    return VisualizationProblem(
        422, code, message, errors=[{"path": path, "code": code, "message": message}]
    )
