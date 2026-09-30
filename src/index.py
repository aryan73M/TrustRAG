import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# Configuration
# --------------------------------------------------

DATA_FILE = Path("data/chunks_v2.json")
CHROMA_DIR = "./chroma_db"

MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "chunks_350_v2"

BATCH_SIZE = 64

model = SentenceTransformer(MODEL_NAME)


# --------------------------------------------------
# Load chunks
# --------------------------------------------------

def load_chunks():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------
# Create embeddings and index them
# --------------------------------------------------

def build_index():

    print("Loading embedding model...")

    print("Loading chunks...")
    chunks = load_chunks()

    print(f"Total chunks: {len(chunks)}")

    # Create persistent Chroma database
    client = chromadb.PersistentClient(
        path=CHROMA_DIR
    )

    # Create/get NEW v2 collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    # Process chunks in batches
    for start in range(
        0,
        len(chunks),
        BATCH_SIZE
    ):

        batch = chunks[
            start:start + BATCH_SIZE
        ]

        texts = [
            chunk["text"]
            for chunk in batch
        ]

        ids = [
            chunk["id"]
            for chunk in batch
        ]

        metadatas = [
            {
                "company": chunk["company"],
                "fiscal_year": chunk["fiscal_year"],
                "source_document": chunk["source_document"],
                "page": chunk["page"],
            }
            for chunk in batch
        ]

        print(
            f"Embedding chunks "
            f"{start + 1}-"
            f"{min(start + BATCH_SIZE, len(chunks))}"
            f" of {len(chunks)}"
        )

        embeddings = model.encode(
            texts,
            show_progress_bar=False
        ).tolist()

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    print("\nIndexing complete!")
    print(f"Collection: {COLLECTION_NAME}")
    print(
        f"Total documents: "
        f"{collection.count()}"
    )


# --------------------------------------------------
# Search
# --------------------------------------------------

def search(query, k=5):
    """
    Search the v2 Chroma collection and return
    the top k chunks with fiscal-year metadata.
    """

    client = chromadb.PersistentClient(
        path=CHROMA_DIR
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    query_embedding = model.encode(
        [query]
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=[
            "documents",
            "metadatas",
            "distances"
        ],
    )

    output = []

    for i in range(
        len(results["documents"][0])
    ):

        metadata = results[
            "metadatas"
        ][0][i]

        output.append(
            {
                "text": results[
                    "documents"
                ][0][i],

                "company": metadata[
                    "company"
                ],

                "fiscal_year": metadata[
                    "fiscal_year"
                ],

                "source_document": metadata[
                    "source_document"
                ],

                "page": metadata[
                    "page"
                ],

                "score": results[
                    "distances"
                ][0][i],
            }
        )

    return output


# --------------------------------------------------
# Test searches
# --------------------------------------------------

def run_tests():

    queries = [
        "total revenue FY24",
        "employee headcount",
        "operating margin",
        "artificial intelligence strategy",
        "sustainability initiatives",
    ]

    for query in queries:

        print(
            "\n" + "=" * 70
        )

        print(
            f"QUERY: {query}"
        )

        print(
            "=" * 70
        )

        results = search(
            query,
            k=3
        )

        for rank, result in enumerate(
            results,
            start=1
        ):

            print(
                f"\nResult #{rank}"
            )

            print(
                f"Company: "
                f"{result['company']}"
            )

            print(
                f"Fiscal Year: "
                f"{result['fiscal_year']}"
            )

            print(
                f"Source: "
                f"{result['source_document']}"
            )

            print(
                f"Page: "
                f"{result['page']}"
            )

            print(
                f"Distance: "
                f"{result['score']}"
            )

            print(
                f"Text: "
                f"{result['text'][:500]}"
            )


# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    build_index()

    run_tests()