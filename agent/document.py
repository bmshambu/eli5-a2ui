"""Documents the user uploads in GE chat, turned into parts Gemini can read.

GE sends an uploaded file in the user's turn: through A2A it arrives as inline_data (the
bytes, with the file name as display_name) or file_data (a URI). PDF, plain text and images
go to Gemini as they are. Word, PowerPoint and Excel files are not read by Gemini directly,
so their text is pulled out here (stdlib only: they are zip files of XML).
Our own A2UI DataParts (button clicks) also arrive as inline_data and are skipped.
"""
import html
import logging
import re
import zipfile
from io import BytesIO
from typing import NamedTuple

from google.genai import types as genai_types

from . import a2ui

log = logging.getLogger(__name__)

# Sent to Gemini as they are.
NATIVE = ("application/pdf", "text/", "image/", "application/json")
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_BY_EXTENSION = {".pdf": "application/pdf", ".txt": "text/plain", ".md": "text/markdown", ".csv": "text/csv",
                 ".docx": DOCX, ".pptx": PPTX, ".xlsx": XLSX}
MAX_TEXT_CHARS = 400_000  # extracted text; about 100k tokens


class Document(NamedTuple):
    name: str
    part: genai_types.Part  # ready for generate_content


def _mime(mime: str | None, name: str) -> str:
    mime = (mime or "").split(";")[0].strip().lower()
    if mime and mime != "application/octet-stream":
        return mime
    ext = name[name.rfind("."):].lower() if "." in name else ""
    return _BY_EXTENSION.get(ext, mime or "application/octet-stream")


def _xml_text(xml: str, para: str, run: str) -> list[str]:
    """Text of each paragraph element `para`, joining its `run` text elements."""
    out = []
    for p in re.findall(rf"<{para}\b[^>]*>(.*?)</{para}>", xml, re.S):
        text = "".join(re.findall(rf"<{run}\b[^>]*>([^<]*)</{run}>", p))
        if text.strip():
            out.append(html.unescape(text))
    return out


def _numbered(names: list[str], prefix: str) -> list[str]:
    return sorted((n for n in names if re.fullmatch(rf"{prefix}\d+\.xml", n)), key=lambda n: int(re.findall(r"\d+", n)[-1]))


def office_text(data: bytes, mime: str) -> str:
    """Plain text of a .docx, .pptx or .xlsx file, in reading order."""
    with zipfile.ZipFile(BytesIO(data)) as z:
        names = z.namelist()
        read = lambda n: z.read(n).decode("utf-8", "replace")  # noqa: E731
        if mime == DOCX:
            return "\n".join(_xml_text(read("word/document.xml"), "w:p", "w:t"))
        if mime == PPTX:
            slides = _numbered(names, "ppt/slides/slide")
            return "\n\n".join(f"[Slide {i}]\n" + "\n".join(_xml_text(read(n), "a:p", "a:t"))
                               for i, n in enumerate(slides, 1))
        shared = _xml_text(read("xl/sharedStrings.xml"), "si", "t") if "xl/sharedStrings.xml" in names else []
        sheets = []
        for i, n in enumerate(_numbered(names, "xl/worksheets/sheet"), 1):
            rows = []
            for row in re.findall(r"<row\b[^>]*>(.*?)</row>", read(n), re.S):
                cells = []
                for attrs, val in re.findall(r"<c\b([^>]*)>.*?<v>([^<]*)</v>", row, re.S):
                    shared_ok = 't="s"' in attrs and val.isdigit() and int(val) < len(shared)
                    cells.append(shared[int(val)] if shared_ok else html.unescape(val))
                if cells:
                    rows.append(" | ".join(cells))
            sheets.append(f"[Sheet {i}]\n" + "\n".join(rows))
        return "\n\n".join(sheets)


def _document(part) -> Document | None:
    blob, ref = getattr(part, "inline_data", None), getattr(part, "file_data", None)
    if blob and blob.data and not blob.data.startswith(a2ui.TAG_START):
        name = blob.display_name or "Uploaded document"
        mime = _mime(blob.mime_type, name)
        # Rebuilt clean: the model needs only the bytes (the Gemini API also rejects display_name).
        if mime.startswith(NATIVE):
            return Document(name, genai_types.Part(inline_data=genai_types.Blob(mime_type=mime, data=blob.data)))
        if mime in (DOCX, PPTX, XLSX):
            try:
                text = office_text(blob.data, mime)[:MAX_TEXT_CHARS]
            except (zipfile.BadZipFile, KeyError) as exc:
                log.warning("could not read %s (%s): %s", name, mime, exc)
                return None
            return Document(name, genai_types.Part(text=f"--- Document: {name} ---\n{text}\n--- End of {name} ---"))
        log.warning("skipping %s: unsupported type %s", name, mime)
        return None
    if ref and ref.file_uri:
        name = ref.display_name or ref.file_uri.rsplit("/", 1)[-1]
        mime = _mime(ref.mime_type, name)
        return Document(name, genai_types.Part(file_data=genai_types.FileData(file_uri=ref.file_uri, mime_type=mime)))
    return None


def from_content(content) -> list[Document]:
    """The documents attached to one turn."""
    return [d for d in map(_document, getattr(content, "parts", None) or []) if d]


def describe(content) -> list[str]:
    """What kinds of parts a turn carried, for the logs (shows how GE delivers uploads)."""
    return [p.inline_data.mime_type if p.inline_data else f"file:{p.file_data.mime_type}" if p.file_data else "text"
            for p in getattr(content, "parts", None) or []]


def latest(events, author: str = "user") -> list[Document]:
    """The most recently uploaded documents in this session, for follow-ups such as ELI5."""
    for event in reversed(events or []):
        if getattr(event, "author", None) == author:
            docs = from_content(getattr(event, "content", None))
            if docs:
                return docs
    return []
