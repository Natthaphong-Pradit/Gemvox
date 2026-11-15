"""
Document & URL Text Extraction for Gemvox.

Supports local documents (.txt, .md, .script, .csv, .log, .srt, .vtt, .docx, .pdf, .html, .htm)
as well as Google Docs links and general web pages via urllib + BeautifulSoup.
"""

from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Optional
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import xml.etree.ElementTree as ET


SUPPORTED_DOC_EXTENSIONS = (
    ".txt",
    ".md",
    ".script",
    ".csv",
    ".log",
    ".srt",
    ".vtt",
    ".docx",
    ".pdf",
    ".html",
    ".htm",
    ".xhtml",
)

_DOC_FILE_FILTER = (
    "Supported Documents (*.txt *.md *.script *.docx *.pdf *.html *.htm);;"
    "Word Documents (*.docx);;"
    "PDF Documents (*.pdf);;"
    "HTML Files (*.html *.htm);;"
    "Text & Script Files (*.txt *.md *.script *.csv *.log *.srt *.vtt);;"
    "All Files (*.*)"
)

_GOOGLE_DOC_ID_RE = re.compile(
    r"https?://docs\.google\.com/document/(?:u/\d+/)?d/([a-zA-Z0-9_-]+)(?:/|$|\?)"
)
_GOOGLE_DOC_PUB_RE = re.compile(
    r"https?://docs\.google\.com/document/(?:u/\d+/)?d/e/([a-zA-Z0-9_-]+)/pub(?:/|$|\?)"
)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


class DocumentLoadError(Exception):
    """Base error raised when a document or URL cannot be loaded or parsed."""


class GoogleDocsAccessError(DocumentLoadError):
    """Raised when a Google Docs URL is restricted, missing, or unreachable."""

    def __init__(self, reason: str, message: str = ""):
        self.reason = reason  # "restricted" | "not_found" | "invalid_url" | "network"
        super().__init__(message or reason)


def get_document_file_filter() -> str:
    """Return the QFileDialog filter string for all supported document types."""
    return _DOC_FILE_FILTER


def _normalize_text(text: str) -> str:
    """Normalize line endings and collapse excessive blank lines."""
    if not text:
        return ""
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def read_text_with_fallback(path: Path | str) -> str:
    """Read a plain-text file trying UTF-8 first, then common Windows/Thai encodings."""
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp874", "tis-620", "cp1252", "latin-1"):
        try:
            return _normalize_text(raw.decode(enc))
        except UnicodeDecodeError:
            continue
    return _normalize_text(raw.decode("utf-8", errors="replace"))


_read_text_with_fallback = read_text_with_fallback


class _FallbackHTMLTextExtractor(HTMLParser):
    """Minimal stdlib HTML-to-text extractor if BeautifulSoup is unavailable."""

    _SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "meta", "link"}
    _BLOCK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"}

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self._SKIP_TAGS:
            self._skip_depth += 1
        elif t in self._BLOCK_TAGS and self._skip_depth == 0:
            self._chunks.append("\n")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif t in self._BLOCK_TAGS and self._skip_depth == 0:
            self._chunks.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0 and data:
            self._chunks.append(data)

    def get_text(self) -> str:
        return _normalize_text("".join(self._chunks))


def extract_text_from_html(html_content: str, container_id: Optional[str] = None) -> str:
    """Extract readable text from HTML using BeautifulSoup (with stdlib fallback)."""
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg", "head", "meta", "link"]):
            tag.decompose()

        target = soup.find(id=container_id) if container_id else None
        if target is None:
            target = soup.body or soup
        if container_id == "contents" and target is not None:
            for chrome_id in ("header", "footer"):
                chrome = target.find(id=chrome_id)
                if chrome is not None:
                    chrome.decompose()

        raw_text = target.get_text(separator="\n")
        return _normalize_text(raw_text)
    except ImportError:
        parser = _FallbackHTMLTextExtractor()
        parser.feed(html_content)
        return parser.get_text()


def _extract_docx_text(path: Path) -> str:
    """Extract paragraphs and table text from a .docx file."""
    try:
        import docx

        document = docx.Document(str(path))
        parts: list[str] = []
        for para in document.paragraphs:
            t = para.text.strip()
            if t:
                parts.append(t)
        for table in document.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    parts.append(" | ".join(row_cells))
        return _normalize_text("\n\n".join(parts))
    except ImportError:
        # Pure-stdlib fallback reading word/document.xml
        try:
            with zipfile.ZipFile(path, "r") as zf:
                xml_bytes = zf.read("word/document.xml")
            root = ET.fromstring(xml_bytes)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for p in root.findall(".//w:p", ns):
                texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
                line = "".join(texts).strip()
                if line:
                    paragraphs.append(line)
            return _normalize_text("\n\n".join(paragraphs))
        except Exception as e:
            raise DocumentLoadError(f"Failed to read DOCX file: {e}") from e
    except Exception as e:
        raise DocumentLoadError(f"Failed to read DOCX file: {e}") from e


def _extract_pdf_text(path: Path) -> str:
    """Extract text from a PDF file using pypdf (with PySide6.QtPdf fallback)."""
    pypdf_err: Optional[Exception] = None
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        if reader.is_encrypted:
            try:
                # Attempt empty-password unlock for owner-locked PDFs
                if reader.decrypt("") == 0:
                    raise DocumentLoadError("PDF is password-protected / encrypted.")
            except DocumentLoadError:
                raise
            except Exception as e:
                raise DocumentLoadError("PDF is password-protected / encrypted.") from e

        pages_text: list[str] = []
        for page in reader.pages:
            txt = page.extract_text() or ""
            txt = txt.strip()
            if txt:
                pages_text.append(txt)
        result = _normalize_text("\n\n".join(pages_text))
        if result:
            return result
    except DocumentLoadError:
        raise
    except Exception as e:
        pypdf_err = e

    # Fallback: PySide6.QtPdf.QPdfDocument
    try:
        from PySide6.QtPdf import QPdfDocument

        doc = QPdfDocument()
        status = doc.load(str(path))
        if status == QPdfDocument.Error.None_:
            pages_text = []
            for i in range(doc.pageCount()):
                sel = doc.getAllText(i)
                txt = sel.text().strip() if sel else ""
                if txt:
                    pages_text.append(txt)
            result = _normalize_text("\n\n".join(pages_text))
            if result:
                return result
    except Exception:
        pass

    if pypdf_err is not None:
        raise DocumentLoadError(f"Failed to read PDF file: {pypdf_err}") from pypdf_err
    raise DocumentLoadError("No extractable text found in PDF (it may be a scanned image PDF).")


def load_document_from_file(path: Path | str) -> str:
    """Load and extract plain text from a supported local document file."""
    p = Path(path)
    if not p.is_file():
        raise DocumentLoadError(f"File not found: {p}")

    ext = p.suffix.lower()
    if ext == ".doc":
        raise DocumentLoadError(
            "Legacy binary .doc format is not supported. Please save as .docx or .txt."
        )
    if ext == ".docx":
        text = _extract_docx_text(p)
    elif ext == ".pdf":
        text = _extract_pdf_text(p)
    elif ext in (".html", ".htm", ".xhtml"):
        html_raw = _read_text_with_fallback(p)
        text = extract_text_from_html(html_raw)
    else:
        text = _read_text_with_fallback(p)

    if not text.strip():
        raise DocumentLoadError(f"Document '{p.name}' contains no extractable text.")
    return text


def is_google_docs_url(url: str) -> bool:
    """Return True if the URL points to Google Docs."""
    parsed = urllib.parse.urlparse((url or "").strip())
    return parsed.scheme in ("http", "https") and "docs.google.com" in parsed.netloc.lower()


def extract_google_doc_info(url: str) -> tuple[Optional[str], bool]:
    """Return (doc_id_or_pub_id, is_published_web_url) for a Google Docs URL."""
    clean = (url or "").strip()
    pub_match = _GOOGLE_DOC_PUB_RE.match(clean)
    if pub_match:
        return pub_match.group(1), True
    doc_match = _GOOGLE_DOC_ID_RE.match(clean)
    if doc_match:
        return doc_match.group(1), False
    return None, False


def _looks_like_google_access_blocked(final_url: str, content_type: str, body_text: str) -> bool:
    """Detect whether Google redirected to sign-in or returned an access-denied HTML page."""
    lower_url = (final_url or "").lower()
    if "accounts.google.com" in lower_url or "servicelogin" in lower_url:
        return True
    if "text/html" in (content_type or "").lower():
        sample = (body_text or "")[:4000].lower()
        markers = (
            "accounts.google.com",
            "servicelogin",
            "you need access",
            "request access",
            "sign in",
            "docs-drivestore",
            "access denied",
        )
        if any(m in sample for m in markers):
            return True
    return False


def _decode_http_bytes(raw: bytes, headers) -> str:
    charset = None
    if headers is not None and hasattr(headers, "get_content_charset"):
        charset = headers.get_content_charset()
    for enc in ([charset] if charset else []) + ["utf-8-sig", "utf-8", "cp874", "cp1252", "latin-1"]:
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", errors="replace")


def load_document_from_url(url: str, timeout: int = 20) -> tuple[str, str]:
    """
    Fetch and extract text from a Google Docs link or general HTTP/HTTPS web page.

    Returns (extracted_text, display_label).
    Raises GoogleDocsAccessError if a Google Docs link is restricted/missing/invalid.
    Raises DocumentLoadError for other network or parsing failures.
    """
    clean_url = (url or "").strip()
    parsed = urllib.parse.urlparse(clean_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise GoogleDocsAccessError("invalid_url", "Please enter a valid http:// or https:// URL.")

    if is_google_docs_url(clean_url):
        doc_id, is_pub = extract_google_doc_info(clean_url)
        if not doc_id:
            raise GoogleDocsAccessError(
                "invalid_url",
                "Could not find a Google Docs document ID in this URL.",
            )

        if is_pub:
            fetch_url = f"https://docs.google.com/document/d/e/{doc_id}/pub"
        else:
            fetch_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"

        req = urllib.request.Request(fetch_url, headers={"User-Agent": _USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                final_url = resp.geturl()
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read()
                body = _decode_http_bytes(raw, resp.headers)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise GoogleDocsAccessError("restricted", f"HTTP {e.code}") from e
            if e.code == 404:
                raise GoogleDocsAccessError("not_found", f"HTTP {e.code}") from e
            raise GoogleDocsAccessError("network", f"HTTP {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise GoogleDocsAccessError("network", str(e.reason)) from e
        except Exception as e:
            raise GoogleDocsAccessError("network", str(e)) from e

        if _looks_like_google_access_blocked(final_url, content_type, body):
            raise GoogleDocsAccessError("restricted", "Google Docs permission required.")

        if is_pub or "text/html" in content_type.lower():
            text = extract_text_from_html(body, container_id="contents")
        else:
            text = _normalize_text(body)

        if not text:
            raise DocumentLoadError("The Google Docs document appears to be empty.")
        return text, f"Google Docs ({doc_id[:12]}...)"

    # General HTTP/HTTPS HTML or text page
    req = urllib.request.Request(clean_url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            raw = resp.read()
            body = _decode_http_bytes(raw, resp.headers)
    except urllib.error.HTTPError as e:
        raise DocumentLoadError(f"HTTP {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise DocumentLoadError(f"Network error: {e.reason}") from e
    except Exception as e:
        raise DocumentLoadError(str(e)) from e

    if "html" in content_type or "<html" in body[:500].lower():
        text = extract_text_from_html(body)
    else:
        text = _normalize_text(body)

    if not text:
        raise DocumentLoadError("No readable text found at the provided URL.")
    return text, parsed.netloc
