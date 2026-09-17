import camelot
import pandas as pd


def extract_tables(pdf_path: str) -> list[dict]:
    """
    Extracts tables from a PDF using Camelot's "lattice" mode, which
    looks for visible grid lines (like Excel-style borders).
    Only works on PDFs with a native text layer (not scanned images) -
    Camelot reads the PDF's internal structure, not pixel data.

    Note: the "stream" fallback mode (whitespace-based detection) was
    intentionally removed - it produced false positives, misreading
    plain paragraphs as single-column "tables". Lattice mode is more
    conservative: it only finds tables that actually have drawn borders.
    """
    tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")

    results = []
    for i, table in enumerate(tables):
        results.append({
            "table_index": i,
            "page": table.page,
            "accuracy": round(table.parsing_report.get("accuracy", 0), 2),
            "columns": table.df.columns.tolist(),
            "data": table.df.values.tolist(),
        })

    return results


def table_to_text(table: dict) -> str:
    """
    Converts a table's columns and rows into a descriptive text block,
    so it can be embedded and searched like normal text.
    Assumes the first data row is the actual header (Camelot's lattice
    extraction puts the real header inside 'data', not in 'columns').
    """
    data = table["data"]
    if not data:
        return ""

    header = data[0]
    rows = data[1:]

    lines = []
    for row in rows:
        row_description = ", ".join(
            f"{col_name}: {value}" for col_name, value in zip(header, row)
        )
        lines.append(row_description)

    return "\n".join(lines)


def table_to_dataframe(table: dict) -> pd.DataFrame:
    """
    Converts a table's raw data into a pandas DataFrame for display,
    using the first data row as the header (same quirk as table_to_text).
    """
    data = table["data"]
    if not data:
        return pd.DataFrame()

    header = data[0]
    rows = data[1:]
    return pd.DataFrame(rows, columns=header)