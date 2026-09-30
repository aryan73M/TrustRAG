import json
import random
from pathlib import Path

import pymupdf


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DATA_DIR = Path("data")
OUTPUT_FILE = DATA_DIR / "chunks_v2.json"


PDFS = {
    "tcs_fy24.pdf": {
        "company": "TCS",
        "fiscal_year": "FY2024",
    },
    "infosys_fy24.pdf": {
        "company": "Infosys",
        "fiscal_year": "FY2024",
    },
    "hcltech_fy24.pdf": {
        "company": "HCLTech",
        "fiscal_year": "FY2024",
    },
    "tcs_fy25.pdf": {
        "company": "TCS",
        "fiscal_year": "FY2025",
    },
    "infosys_fy25.pdf": {
        "company": "Infosys",
        "fiscal_year": "FY2025",
    },
    "hcltech_fy25.pdf": {
        "company": "HCLTech",
        "fiscal_year": "FY2025",
    },
}


CHUNK_SIZE = 350
OVERLAP = 50


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """
    Split text into word-based chunks with overlap.
    """
    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0

    while start < len(words):

        end = min(
            start + chunk_size,
            len(words)
        )

        chunk = " ".join(
            words[start:end]
        )

        chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks


def ingest_pdf(
    pdf_path,
    company,
    fiscal_year
):
    """
    Extract text page-by-page and create chunks.

    Chunks never cross page boundaries.
    """

    results = []

    doc = pymupdf.open(pdf_path)

    print(
        f"\nProcessing "
        f"{company} {fiscal_year}: "
        f"{pdf_path}"
    )

    print(
        f"Pages: {len(doc)}"
    )

    for page_number, page in enumerate(
        doc,
        start=1
    ):

        text = page.get_text().strip()

        if not text:
            continue

        page_chunks = chunk_text(text)

        for chunk_number, chunk in enumerate(
            page_chunks,
            start=1
        ):

            chunk_id = (
                f"{company.lower()}_"
                f"{fiscal_year.lower()}_"
                f"p{page_number}_"
                f"c{chunk_number}"
            )

            results.append(
                {
                    "id": chunk_id,
                    "company": company,
                    "fiscal_year": fiscal_year,
                    "source_document": pdf_path.name,
                    "page": page_number,
                    "text": chunk,
                }
            )

    doc.close()

    return results


def main():

    all_chunks = []

    # --------------------------------------------------
    # Process every PDF
    # --------------------------------------------------

    for filename, metadata in PDFS.items():

        pdf_path = DATA_DIR / filename

        company = metadata["company"]
        fiscal_year = metadata["fiscal_year"]

        if not pdf_path.exists():

            print(
                f"ERROR: Could not find "
                f"{pdf_path}"
            )

            continue

        chunks = ingest_pdf(
            pdf_path,
            company,
            fiscal_year
        )

        all_chunks.extend(chunks)

        print(
            f"Chunks created for "
            f"{company} {fiscal_year}: "
            f"{len(chunks)}"
        )

    # --------------------------------------------------
    # Save chunks
    # --------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_chunks,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n" + "=" * 60)

    print(
        f"Total chunks: "
        f"{len(all_chunks)}"
    )

    print(
        f"Saved to: "
        f"{OUTPUT_FILE}"
    )

    print("=" * 60)

    # --------------------------------------------------
    # Verify companies
    # --------------------------------------------------

    companies = {}

    for chunk in all_chunks:

        company = chunk["company"]

        companies[company] = (
            companies.get(company, 0) + 1
        )

    print("\nCHUNK COUNTS BY COMPANY:")

    for company, count in companies.items():

        print(
            f"{company}: {count}"
        )

    # --------------------------------------------------
    # Verify duplicate IDs
    # --------------------------------------------------

    unique_ids = len(
        set(
            chunk["id"]
            for chunk in all_chunks
        )
    )

    print(
        f"\nUnique IDs: "
        f"{unique_ids}"
    )

    print(
        f"Duplicate IDs: "
        f"{len(all_chunks) - unique_ids}"
    )

    # --------------------------------------------------
    # Random inspection
    # --------------------------------------------------

    if all_chunks:

        sample_size = min(
            5,
            len(all_chunks)
        )

        print(
            "\nRANDOM CHUNKS:"
        )

        print("=" * 60)

        for chunk in random.sample(
            all_chunks,
            sample_size
        ):

            print(
                f"\nID: {chunk['id']}"
            )

            print(
                f"Company: "
                f"{chunk['company']}"
            )

            print(
                f"Fiscal Year: "
                f"{chunk['fiscal_year']}"
            )

            print(
                f"Source Document: "
                f"{chunk['source_document']}"
            )

            print(
                f"Page: "
                f"{chunk['page']}"
            )

            print(
                f"Text: "
                f"{chunk['text'][:500]}"
            )

            print(
                "-" * 60
            )


if __name__ == "__main__":
    main()