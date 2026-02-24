"""
PDF conversion tools — converts any document or image type to PDF.
Supports: docx, xlsx, pptx, txt, html, md, csv, jpg, png, gif, bmp, tiff, webp
"""
import os
import subprocess
from pathlib import Path
from typing import Optional

import img2pdf
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from utils.logger import log


def convert_image_to_pdf(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert a single image to PDF.

    Args:
        input_path: Path to the image file
        output_path: Optional output PDF path. Auto-generated if not provided.

    Returns:
        Path to the generated PDF file
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    supported_formats = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
    if input_file.suffix.lower() not in supported_formats:
        raise ValueError(f"Unsupported image format: {input_file.suffix}")

    if output_path is None:
        output_path = str(input_file.with_suffix(".pdf"))

    os.makedirs(Path(output_path).parent, exist_ok=True)

    try:
        img = Image.open(input_path)
        if img.mode in ("RGBA", "LA", "P"):
            rgb_path = str(input_file.with_stem(input_file.stem + "_rgb").with_suffix(".jpg"))
            img = img.convert("RGB")
            img.save(rgb_path)
            convert_source = rgb_path
        else:
            convert_source = input_path

        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(convert_source))

        if convert_source != input_path and os.path.exists(convert_source):
            os.remove(convert_source)

        log.success(f"Image converted to PDF: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"Failed to convert image to PDF: {e}")
        raise


def convert_docx_to_pdf(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert a Word document (.docx) to PDF using LibreOffice.

    Args:
        input_path: Path to the .docx file
        output_path: Optional output PDF path

    Returns:
        Path to the generated PDF file
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = str(input_file.with_suffix(".pdf"))

    output_dir = str(Path(output_path).parent)
    os.makedirs(output_dir, exist_ok=True)

    try:
        soffice = _find_libreoffice()
        result = subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", output_dir, input_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            lo_output = Path(output_dir) / (input_file.stem + ".pdf")
            if lo_output.exists() and str(lo_output) != output_path:
                lo_output.rename(output_path)
            log.success(f"DOCX converted to PDF: {output_path}")
            return output_path
        raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        log.error(f"LibreOffice not available or timed out: {exc}")
        raise RuntimeError(
            "LibreOffice is required for DOCX → PDF conversion. "
            "Install from https://www.libreoffice.org/"
        ) from exc


def convert_text_to_pdf(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert plain text, markdown, CSV, or HTML file to PDF using ReportLab.

    Args:
        input_path: Path to the text-based file
        output_path: Optional output PDF path

    Returns:
        Path to the generated PDF file
    """
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = str(input_file.with_suffix(".pdf"))

    os.makedirs(Path(output_path).parent, exist_ok=True)

    try:
        with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        c.setFont("Helvetica", 11)

        x_margin = 60
        y_position = height - 60
        line_height = 16

        for line in content.split("\n"):
            while len(line) > 90:
                c.drawString(x_margin, y_position, line[:90])
                line = line[90:]
                y_position -= line_height
                if y_position < 60:
                    c.showPage()
                    c.setFont("Helvetica", 11)
                    y_position = height - 60

            c.drawString(x_margin, y_position, line)
            y_position -= line_height

            if y_position < 60:
                c.showPage()
                c.setFont("Helvetica", 11)
                y_position = height - 60

        c.save()
        log.success(f"Text converted to PDF: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"Text to PDF conversion failed: {e}")
        raise


def convert_any_to_pdf(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Universal PDF converter — auto-detects file type and routes to correct converter.

    Supported: docx, xlsx, pptx, txt, md, csv, html, jpg, jpeg, png, gif, bmp, tiff, webp

    Args:
        input_path: Path to any supported file
        output_path: Optional output PDF path

    Returns:
        Path to the generated PDF file
    """
    ext = Path(input_path).suffix.lower()

    image_types = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp"}
    doc_types = {".docx", ".doc"}
    office_types = {".xlsx", ".xls", ".pptx", ".ppt"}
    text_types = {".txt", ".md", ".csv", ".html", ".htm"}

    log.info(f"Converting {ext} file to PDF: {input_path}")

    if ext in image_types:
        return convert_image_to_pdf(input_path, output_path)
    elif ext in doc_types:
        return convert_docx_to_pdf(input_path, output_path)
    elif ext in office_types:
        return _convert_via_libreoffice(input_path, output_path)
    elif ext in text_types:
        return convert_text_to_pdf(input_path, output_path)
    else:
        raise ValueError(f"Unsupported file type for PDF conversion: {ext}")


def _convert_via_libreoffice(input_path: str, output_path: Optional[str] = None) -> str:
    """Convert Office files (xlsx, pptx) to PDF via LibreOffice headless."""
    input_file = Path(input_path)

    if output_path is None:
        output_path = str(input_file.with_suffix(".pdf"))

    output_dir = str(Path(output_path).parent)
    os.makedirs(output_dir, exist_ok=True)

    try:
        soffice = _find_libreoffice()
        result = subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", output_dir, input_path],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

        lo_output = Path(output_dir) / (input_file.stem + ".pdf")
        if lo_output.exists() and str(lo_output) != output_path:
            lo_output.rename(output_path)

        log.success(f"File converted to PDF: {output_path}")
        return output_path

    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("LibreOffice conversion timed out after 120 seconds") from exc
    except FileNotFoundError as exc:
        raise RuntimeError(
            "LibreOffice is not installed. Download from https://www.libreoffice.org/"
        ) from exc


def _find_libreoffice() -> str:
    """Return the LibreOffice executable path, checking common Windows locations."""
    import shutil

    # Try PATH first
    candidate = shutil.which("soffice") or shutil.which("libreoffice")
    if candidate:
        return candidate

    # Common Windows install paths
    windows_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for p in windows_paths:
        if os.path.isfile(p):
            return p

    raise FileNotFoundError("LibreOffice executable not found.")
