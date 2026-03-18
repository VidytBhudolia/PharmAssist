"""
PDF Converter Tool

Converts HTML reports to PDF format using Playwright.
Playwright uses Chromium for pixel-perfect HTML/CSS rendering.

Install: pip install playwright && playwright install chromium
"""

import asyncio
import tempfile
import os
from typing import Optional, Union, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Thread pool for running Playwright sync API from async context
_pdf_executor = ThreadPoolExecutor(max_workers=2)

# Default PDF options for A4 professional report
_DEFAULT_PDF_OPTIONS = {
    "format": "A4",
    "print_background": True,
    "margin": {
        "top": "15mm",
        "right": "15mm",
        "bottom": "15mm",
        "left": "15mm",
    },
    "display_header_footer": False,
    "prefer_css_page_size": True,
}


def _generate_pdf_sync(
    html_content: str,
    output_path: Optional[str] = None,
    pdf_options: Optional[Dict[str, Any]] = None,
) -> Union[bytes, str]:
    """
    Generate PDF using Playwright's SYNC API.
    This runs in a separate thread to avoid event loop conflicts.
    """
    from playwright.sync_api import sync_playwright
    
    options = {**_DEFAULT_PDF_OPTIONS}
    if pdf_options:
        options.update(pdf_options)
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        print(f"--- PDF CONVERTER [sync thread]: Attempt {attempt}/{max_retries}")
        try:
            print(f"--- PDF CONVERTER [sync thread]: Launching Playwright Chromium...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                print(f"--- PDF CONVERTER [sync thread]: ✓ Chromium launched")
                try:
                    page = browser.new_page()
                    print(f"--- PDF CONVERTER [sync thread]: ✓ Page created")
                    
                    print(f"--- PDF CONVERTER [sync thread]: Setting content ({len(html_content)} chars)...")
                    page.set_content(html_content, wait_until="networkidle")
                    print(f"--- PDF CONVERTER [sync thread]: ✓ Content set")
                    
                    print(f"--- PDF CONVERTER [sync thread]: Waiting for fonts and images...")
                    page.wait_for_timeout(1000)  # Increased wait time for rendering
                    print(f"--- PDF CONVERTER [sync thread]: ✓ Wait complete")
                    
                    if output_path:
                        print(f"--- PDF CONVERTER [sync thread]: Generating PDF to {output_path}...")
                        page.pdf(path=output_path, **options)
                        print(f"--- PDF CONVERTER [sync thread]: ✓ PDF saved successfully")
                        return output_path
                    else:
                        print(f"--- PDF CONVERTER [sync thread]: Generating PDF as bytes...")
                        pdf_bytes = page.pdf(**options)
                        print(f"--- PDF CONVERTER [sync thread]: ✓ PDF generated successfully, {len(pdf_bytes)} bytes")
                        return pdf_bytes
                except Exception as page_err:
                    error_msg = str(page_err)
                    print(f"--- PDF CONVERTER [sync thread]: ✗ Page error on attempt {attempt}: {error_msg}")
                    
                    # Check for specific deployment-related errors
                    if "Printing failed" in error_msg or "printToPDF" in error_msg:
                        print(f"--- PDF CONVERTER [sync thread]: This is likely a deployment environment issue")
                        print(f"--- PDF CONVERTER [sync thread]: Missing system libraries (glibc, libx11, etc.)")
                        print(f"--- PDF CONVERTER [sync thread]: Retrying with simplified rendering...")
                    
                    if attempt < max_retries:
                        print(f"--- PDF CONVERTER [sync thread]: Retrying (attempt {attempt + 1}/{max_retries})...")
                        continue
                    else:
                        raise
                finally:
                    print(f"--- PDF CONVERTER [sync thread]: Closing browser")
                    browser.close()
                    print(f"--- PDF CONVERTER [sync thread]: ✓ Browser closed")
                    
        except Exception as e:
            error_msg = str(e)
            print(f"--- PDF CONVERTER [sync thread]: ✗ FATAL ERROR on attempt {attempt}: {error_msg}")
            import traceback
            traceback.print_exc()
            
            if attempt < max_retries:
                import time
                wait_time = (2 ** (attempt - 1))  # Exponential backoff: 1s, 2s, 4s
                print(f"--- PDF CONVERTER [sync thread]: Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                # All retries failed - provide helpful error message
                if "Printing failed" in error_msg or "printToPDF" in error_msg:
                    detailed_msg = (
                        f"PDF conversion failed after {max_retries} retries: {error_msg}\n"
                        "DEPLOYMENT ISSUE: Missing system libraries.\n"
                        "The deployed server likely doesn't have required dependencies:\n"
                        "  - libx11-6, libxcomposite1, libxdamage1, libxext6\n"
                        "  - libxfixes3, libxrandr2, libxtst6, libxkbcommon0\n"
                        "  - glibc, libgcc1, libnss3, libssl3\n"
                        "Add these to your Docker image or deployment environment."
                    )
                else:
                    detailed_msg = (
                        f"PDF conversion failed after {max_retries} retries: {error_msg}\n"
                        "This may be due to:\n"
                        "  1. Playwright browser not installed (run: playwright install chromium)\n"
                        "  2. Missing system dependencies\n"
                        "  3. Insufficient memory or disk space\n"
                        "  4. HTML content too complex to render"
                    )
                raise Exception(detailed_msg)


async def convert_html_to_pdf_async(
    html_content: str,
    output_path: Optional[str] = None,
    pdf_options: Optional[Dict[str, Any]] = None,
) -> Union[bytes, str]:
    """
    Convert HTML content to PDF using Playwright (async-safe).
    
    Runs Playwright's sync API in a thread pool to avoid issues with 
    Playwright's async API inside uvicorn's event loop on Windows.
    
    Args:
        html_content: HTML string to convert
        output_path: Optional file path to save PDF. If None, returns bytes.
        pdf_options: Optional Playwright PDF options
        
    Returns:
        PDF bytes if no output_path, otherwise the path to saved file
    """
    print(f"\n--- PDF CONVERTER: convert_html_to_pdf_async called ---")
    print(f"--- PDF CONVERTER: html_content length={len(html_content)}, output_path={output_path}")
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _pdf_executor,
        _generate_pdf_sync,
        html_content,
        output_path,
        pdf_options,
    )
    
    print(f"--- PDF CONVERTER: Async wrapper complete")
    return result


def convert_html_to_pdf(
    html_content: str,
    output_path: Optional[str] = None,
    pdf_options: Optional[Dict[str, Any]] = None,
) -> Union[bytes, str]:
    """
    Convert HTML content to PDF using Playwright (sync).
    
    This is the main entry point for synchronous code.
    Uses Chromium for pixel-perfect rendering.
    
    Args:
        html_content: HTML string to convert
        output_path: Optional file path to save PDF. If None, returns bytes.
        pdf_options: Optional Playwright PDF options
        
    Returns:
        PDF bytes if no output_path, otherwise the path to saved file
    """
    return _generate_pdf_sync(html_content, output_path, pdf_options)


def convert_html_file_to_pdf(
    html_file_path: str,
    output_path: Optional[str] = None,
    pdf_options: Optional[Dict[str, Any]] = None,
) -> Union[bytes, str]:
    """
    Convert an HTML file to PDF.
    
    Args:
        html_file_path: Path to the HTML file
        output_path: Optional output path for PDF (defaults to same name with .pdf)
        pdf_options: Optional Playwright PDF options
        
    Returns:
        PDF bytes or path to saved file
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    if output_path is None:
        output_path = str(Path(html_file_path).with_suffix('.pdf'))
    
    return convert_html_to_pdf(html_content, output_path, pdf_options)


def convert_url_to_pdf(
    url: str,
    output_path: Optional[str] = None,
    pdf_options: Optional[Dict[str, Any]] = None,
) -> Union[bytes, str]:
    """
    Convert a web page URL to PDF.
    
    Args:
        url: URL of the page to convert
        output_path: Optional output path for PDF
        pdf_options: Optional Playwright PDF options
        
    Returns:
        PDF bytes or path to saved file
    """
    async def _convert():
        from playwright.async_api import async_playwright
        
        default_options = {
            "format": "A4",
            "print_background": True,
            "margin": {"top": "15mm", "right": "15mm", "bottom": "15mm", "left": "15mm"},
            "tagged": True,
        }
        
        if pdf_options:
            default_options.update(pdf_options)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--font-render-hinting=none',
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            try:
                page = await browser.new_page(device_scale_factor=2)
                await page.goto(url, wait_until="networkidle")
                
                # Wait for fonts to load
                await page.evaluate("() => document.fonts.ready")
                await page.wait_for_timeout(1500)
                
                # Emulate print media
                await page.emulate_media(media='print')
                
                if output_path:
                    await page.pdf(path=output_path, **default_options)
                    return output_path
                else:
                    return await page.pdf(**default_options)
            finally:
                await browser.close()
    
    return asyncio.run(_convert())


# PDF generation options presets
PDF_PRESETS = {
    "a4_portrait": {
        "format": "A4",
        "print_background": True,
        "margin": {"top": "15mm", "right": "15mm", "bottom": "15mm", "left": "15mm"},
    },
    "a4_landscape": {
        "format": "A4",
        "landscape": True,
        "print_background": True,
        "margin": {"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
    },
    "letter_portrait": {
        "format": "Letter",
        "print_background": True,
        "margin": {"top": "0.5in", "right": "0.5in", "bottom": "0.5in", "left": "0.5in"},
    },
    "full_page": {
        "format": "A4",
        "print_background": True,
        "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
    },
    "presentation": {
        "width": "1920px",
        "height": "1080px",
        "print_background": True,
        "margin": {"top": "0", "right": "0", "bottom": "0", "left": "0"},
    },
}
