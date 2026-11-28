"""Read the two binary parts of a bounded visualization request."""

from collections.abc import AsyncIterable
from dataclasses import dataclass

from python_multipart import MultipartParser
from python_multipart.exceptions import FormParserError
from python_multipart.multipart import parse_options_header

from wind_turbine_visualization.api.problems import VisualizationProblem

MAX_REQUEST_BYTES = 22 * 1024 * 1024
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_PARAMETERS_BYTES = 1024 * 1024
MAX_PART_HEADER_BYTES = 16 * 1024


@dataclass(frozen=True)
class VisualizationUpload:
    """Image bytes, their declared MIME type, and UTF-8 JSON bytes."""

    image: bytes
    mime_type: str
    parameters: bytes


def _invalid(detail: str, part: str | None = None) -> VisualizationProblem:
    return VisualizationProblem(400, "INVALID_MULTIPART", detail, part=part)


def _header_options(value: str | bytes | None) -> tuple[bytes, dict[bytes, bytes]]:
    media_type, options = parse_options_header(value)
    return media_type, {key.lower(): value for key, value in options.items()}


class _Parts:
    """Callbacks for the library parser so part media types and raw bytes survive."""

    def __init__(self) -> None:
        self.items: dict[str, tuple[str, bytes]] = {}
        self.finished = False
        self.on_part_begin()

    def on_part_begin(self) -> None:
        self.headers: dict[bytes, bytes] = {}
        self.header_size = 0
        self.header_name = bytearray()
        self.header_value = bytearray()
        self.data = bytearray()
        self.name = ""
        self.mime_type = ""

    def _append_header(
        self, target: bytearray, data: bytes, start: int, end: int
    ) -> None:
        self.header_size += end - start
        if self.header_size > MAX_PART_HEADER_BYTES:
            raise _invalid("Multipart part headers are too large.")
        target.extend(data[start:end])

    def on_header_field(self, data: bytes, start: int, end: int) -> None:
        self._append_header(self.header_name, data, start, end)

    def on_header_value(self, data: bytes, start: int, end: int) -> None:
        self._append_header(self.header_value, data, start, end)

    def on_header_end(self) -> None:
        field = bytes(self.header_name).lower()
        if field in self.headers:
            raise _invalid("Multipart part headers must be unique.")
        self.headers[field] = bytes(self.header_value)
        self.header_name.clear()
        self.header_value.clear()

    def on_headers_finished(self) -> None:
        disposition, options = _header_options(self.headers.get(b"content-disposition"))
        name = options.get(b"name")
        if disposition.lower() != b"form-data" or name not in (b"image", b"parameters"):
            raise _invalid("Send exactly the image and parameters multipart parts.")
        self.name = name.decode("ascii")
        if self.name in self.items:
            raise VisualizationProblem(
                400, "DUPLICATE_PART", "Multipart part is repeated.", part=self.name
            )

        media_type, options = _header_options(self.headers.get(b"content-type"))
        media_type = media_type.lower()
        if self.name == "parameters":
            if media_type != b"application/json" or options.get(
                b"charset", b"utf-8"
            ).lower() not in (b"utf-8", b"utf8"):
                raise _invalid(
                    "The parameters part must be UTF-8 application/json.", self.name
                )
        elif media_type not in (b"image/jpeg", b"image/png"):
            raise VisualizationProblem(
                415, "UNSUPPORTED_IMAGE_TYPE", "Upload a JPEG or PNG.", part=self.name
            )
        self.mime_type = media_type.decode("ascii")

    def on_part_data(self, data: bytes, start: int, end: int) -> None:
        size = len(self.data) + end - start
        if self.name == "image" and size > MAX_IMAGE_BYTES:
            raise VisualizationProblem(
                413, "IMAGE_TOO_LARGE", "Image exceeds 20 MiB.", part=self.name
            )
        if self.name == "parameters" and size > MAX_PARAMETERS_BYTES:
            raise VisualizationProblem(
                413, "PARAMETERS_TOO_LARGE", "Parameters exceed 1 MiB.", part=self.name
            )
        self.data.extend(data[start:end])

    def on_part_end(self) -> None:
        self.items[self.name] = self.mime_type, bytes(self.data)
        self.data.clear()

    def on_end(self) -> None:
        self.finished = True


async def read_upload(
    content_type: str, chunks: AsyncIterable[bytes]
) -> VisualizationUpload:
    """Validate multipart framing, limit bytes, and require one part of each kind."""
    media_type, options = _header_options(content_type)
    boundary = options.get(b"boundary", b"")
    if media_type.lower() != b"multipart/form-data" or not 1 <= len(boundary) <= 70:
        raise _invalid("A valid multipart/form-data boundary is required.")

    parts = _Parts()
    callbacks = {
        name: getattr(parts, name)
        for name in (
            "on_part_begin",
            "on_header_field",
            "on_header_value",
            "on_header_end",
            "on_headers_finished",
            "on_part_data",
            "on_part_end",
            "on_end",
        )
    }
    parser = MultipartParser(boundary, callbacks)
    total = 0
    try:
        async for chunk in chunks:
            total += len(chunk)
            if total > MAX_REQUEST_BYTES:
                raise VisualizationProblem(
                    413, "REQUEST_TOO_LARGE", "Request exceeds 22 MiB."
                )
            if chunk:
                parser.write(chunk)
        parser.finalize()
    except FormParserError as exc:
        raise _invalid("Multipart body could not be parsed.") from exc

    if not parts.finished:
        raise _invalid("Multipart body has no closing boundary.")
    for name in ("image", "parameters"):
        if name not in parts.items:
            raise _invalid("A required multipart part is missing.", name)
    mime_type, image = parts.items["image"]
    return VisualizationUpload(image, mime_type, parts.items["parameters"][1])
