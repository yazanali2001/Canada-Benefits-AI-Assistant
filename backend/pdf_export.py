"""
Generates a simple PDF summary of the user's eligibility results,
so they can save or hand it to someone (e.g. a government caseworker).
"""

import logging
import re
from fpdf import FPDF

logger = logging.getLogger(__name__)

# Unicode punctuation the PDF's core font can't render, mapped to
# plain ASCII equivalents so nothing turns into a stray "?" in the output.
_UNICODE_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'",    # curly single quotes
    "\u201c": '"', "\u201d": '"',    # curly double quotes
    "\u2013": "-", "\u2014": "-",    # en dash, em dash
    "\u2026": "...",                  # ellipsis
    "\u00a0": " ",                    # non-breaking space
    "\u2022": "-",                    # bullet point
}


def _clean_text_for_pdf(text: str) -> str:
    """
    Convert an LLM-generated Markdown answer into clean, readable plain
    text: strips Markdown syntax (headers, bold, tables, <br> tags) and
    maps Unicode punctuation to plain ASCII, so the PDF never shows a
    literal "?", "**", "###", "<br>", or raw table pipes.
    """
    for bad, good in _UNICODE_REPLACEMENTS.items():
        text = text.replace(bad, good)

    # <br> tags -> real newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # Remove Markdown table separator lines, e.g. |---|---|---|
    text = re.sub(r"^\s*\|[\s\-:|]+\|\s*$", "", text, flags=re.MULTILINE)

    # Convert remaining table rows "| a | b | c |" into "a - b - c"
    def _row_to_line(match: "re.Match") -> str:
        cells = [c.strip() for c in match.group(0).strip().strip("|").split("|")]
        return " - ".join(cell for cell in cells if cell)

    text = re.sub(r"^\s*\|.+\|\s*$", _row_to_line, text, flags=re.MULTILINE)

    # Strip Markdown headers (#, ##, ###...) but keep the heading text
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)

    # Strip bold/italic markers (**text**, *text*) but keep the text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)

    # Collapse excess blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def build_summary_pdf(username: str, summary_text: str) -> bytes:
    """
    Build a simple one-page PDF containing a cleaned, readable version
    of the eligibility summary text. Returns raw PDF bytes.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Canada Benefits AI - Eligibility Summary", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Prepared for: {username}", ln=True)
    pdf.ln(4)

    cleaned = _clean_text_for_pdf(summary_text)

    # Any remaining unsupported character is dropped silently (not
    # shown as "?") — after the mapping above, this should be rare.
    safe_text = cleaned.encode("latin-1", "ignore").decode("latin-1")

    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 7, safe_text)

    pdf.set_font("Helvetica", "I", 9)
    pdf.ln(6)
    pdf.multi_cell(
        0, 6,
        "Disclaimer: This is an AI-generated informational summary, not an "
        "official eligibility determination. Please confirm all details on "
        "the official Canada.ca website before applying.",
    )

    return bytes(pdf.output())