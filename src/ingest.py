import json
import random
from pathlib import Path

import pymupdf


# Project directories
DATA_DIR = Path("data")
OUTPUT_FILE = DATA_DIR / "chunks.json"


# PDF filename -> company name
PDFS = {
    "tcs_fy24.pdf": "TCS",
    "infosys_fy24.pdf": "Infosys",
    "hcltech_fy24.pdf": "HCLTech",
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
        end = min(start + chunk_size, len(words))

        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks


def ingest_pdf(pdf_path, company):
    """
    Extract text page-by-page and create chunks.
    Chunks never cross page boundaries.
    """
    results = []

    doc = pymupdf.open(pdf_path)

    print(f"\nProcessing {company}: {pdf_path}")
    print(f"Pages: {len(doc)}")

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text().strip()

        # Skip empty pages
        if not text:
            continue

        page_chunks = chunk_text(text)

        for chunk_number, chunk in enumerate(page_chunks, start=1):
            chunk_id = f"{company.lower()}_p{page_number}_c{chunk_number}"

            results.append(
                {
                    "id": chunk_id,
                    "company": company,
                    "page": page_number,
                    "text": chunk,
                }
            )

    doc.close()

    return results


def main():
    all_chunks = []

    for filename, company in PDFS.items():
        pdf_path = DATA_DIR / filename

        if not pdf_path.exists():
            print(f"ERROR: Could not find {pdf_path}")
            continue

        chunks = ingest_pdf(pdf_path, company)
        all_chunks.extend(chunks)

        print(f"Chunks created for {company}: {len(chunks)}")

    # Save all chunks
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Saved to: {OUTPUT_FILE}")
    print("=" * 60)

    # Print 10 random chunks for manual inspection
    if all_chunks:
        sample_size = min(10, len(all_chunks))

        print("\n10 RANDOM CHUNKS:")
        print("=" * 60)

        for chunk in random.sample(all_chunks, sample_size):
            print(f"\nID: {chunk['id']}")
            print(f"Company: {chunk['company']}")
            print(f"Page: {chunk['page']}")
            print(f"Text:\n{chunk['text'][:1000]}")
            print("-" * 60)


if __name__ == "__main__":
    main()