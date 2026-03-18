"""
Report Generator Agent Tools

Additional tools for enhanced report generation capabilities.
"""

from .pdf_converter import (
    convert_html_to_pdf,
    convert_html_to_pdf_async,
    convert_html_file_to_pdf,
    convert_url_to_pdf,
    PDF_PRESETS,
)

try:
    from .chart_generator import generate_chart_svg
except ImportError:
    def generate_chart_svg(*args, **kwargs):
        return "<p>Chart generator not available</p>"

__all__ = [
    "convert_html_to_pdf",
    "convert_html_to_pdf_async",
    "convert_html_file_to_pdf",
    "convert_url_to_pdf",
    "PDF_PRESETS",
    "generate_chart_svg",
]
