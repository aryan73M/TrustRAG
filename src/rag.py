import json
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "chunks_350_v2"

MODEL_NAME = "BAAI/bge-small-en-v1.5"
GEMINI_MODEL = "gemini-3.1-flash-lite"

TOP_K = 5


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# LAZY RESOURCES
# ============================================================

_embedding_model = None
_chroma_client = None
_collection = None
_client = None


# ============================================================
# GEMINI CLIENT
# ============================================================

def get_gemini_client():
    global _client

    if _client is None:

        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is not configured. "
                "Add it to Streamlit Cloud Secrets."
            )

        _client = genai.Client(
            api_key=api_key
        )

    return _client


# ============================================================
# EMBEDDING MODEL
# ============================================================

def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:

        print("Loading embedding model...")

        _embedding_model = SentenceTransformer(
            MODEL_NAME
        )

    return _embedding_model


# ============================================================
# CHROMADB COLLECTION
# ============================================================

def get_collection():

    global _chroma_client
    global _collection

    if _collection is None:

        chroma_path = Path(CHROMA_DIR)

        if not chroma_path.exists():

            raise RuntimeError(
                "ChromaDB data was not found on this deployment. "
                "The local chroma_db directory is not included "
                "in the GitHub deployment."
            )

        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_DIR
        )

        try:

            _collection = _chroma_client.get_collection(
                name=COLLECTION_NAME
            )

        except Exception as e:

            raise RuntimeError(
                f"ChromaDB collection '{COLLECTION_NAME}' "
                f"is not available: {e}"
            )

    return _collection


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve(
    question,
    k=TOP_K,
    company=None,
    fiscal_year=None,
):
    """
    Retrieve annual-report evidence relevant to a question.

    Parameters
    ----------
    question : str
        User's research question.

    k : int
        Number of final chunks to return.

    company : str, optional
        Company filter.

    fiscal_year : str, optional
        Fiscal-year filter such as FY2024 or FY2025.

    Returns
    -------
    list[dict]
        Retrieved evidence chunks.
    """

    embedding_model = get_embedding_model()

    collection = get_collection()

    # --------------------------------------------------------
    # Create query embedding
    # --------------------------------------------------------

    query_embedding = embedding_model.encode(
        question,
        normalize_embeddings=True,
    ).tolist()

    # --------------------------------------------------------
    # Build Chroma query
    # --------------------------------------------------------

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": max(k * 5, 20),
        "include": [
            "documents",
            "metadatas",
            "distances",
        ],
    }

    # Chroma can directly filter company.
    if company:

        query_kwargs["where"] = {
            "company": company
        }

    # --------------------------------------------------------
    # Query ChromaDB
    # --------------------------------------------------------

    results = collection.query(
        **query_kwargs
    )

    # --------------------------------------------------------
    # Handle empty result
    # --------------------------------------------------------

    if not results.get("documents"):
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    retrieved = []

    # --------------------------------------------------------
    # Apply fiscal-year filtering client-side
    # --------------------------------------------------------

    for i in range(len(documents)):

        metadata = metadatas[i] or {}

        if (
            fiscal_year
            and metadata.get("fiscal_year") != fiscal_year
        ):
            continue

        retrieved.append(
            {
                "id": ids[i],
                "text": documents[i],
                "company": metadata.get(
                    "company"
                ),
                "fiscal_year": metadata.get(
                    "fiscal_year"
                ),
                "source_document": metadata.get(
                    "source_document"
                ),
                "page": metadata.get(
                    "page"
                ),
                "distance": distances[i],
            }
        )

    # --------------------------------------------------------
    # Sort by semantic distance
    # --------------------------------------------------------

    retrieved.sort(
        key=lambda x: x["distance"]
    )

    # --------------------------------------------------------
    # Return top-k
    # --------------------------------------------------------

    return retrieved[:k]


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(chunks):

    if not chunks:
        return ""

    chunks = sorted(
        chunks,
        key=lambda x: x.get(
            "distance",
            999999
        ),
    )

    parts = []

    for chunk in chunks:

        parts.append(
            f"""
SOURCE:
{chunk.get("company", "Unknown")}

FISCAL YEAR:
{chunk.get("fiscal_year", "Unknown")}

PAGE:
{chunk.get("page", "N/A")}

DOCUMENT:
{chunk.get("source_document", "annual_report")}

CHUNK ID:
{chunk.get("id", "N/A")}

TEXT:
{chunk.get("text", "")}
"""
        )

    return "\n\n".join(parts)


# ============================================================
# SIMPLE GEMINI ANSWER FUNCTION
# ============================================================

def answer(
    question,
    company=None,
    fiscal_year=None,
    k=TOP_K,
):
    """
    Retrieve evidence and generate an evidence-grounded
    answer.

    This function is optional for dashboard_final.py.
    The dashboard currently performs its own Gemini
    generation after calling retrieve().
    """

    chunks = retrieve(
        question=question,
        k=k,
        company=company,
        fiscal_year=fiscal_year,
    )

    if not chunks:

        return {
            "answer": (
                "I could not find sufficient annual-report "
                "evidence for this question."
            ),
            "sources": [],
        }

    context = build_context(chunks)

    prompt = f"""
You are TrustRAG, an evidence-grounded corporate
research copilot.

USER QUESTION:
{question}

ANNUAL-REPORT EVIDENCE:
{context}

RULES:

1. Use ONLY the supplied annual-report evidence.

2. Do not use outside knowledge.

3. Do not invent numbers, facts, or conclusions.

4. If the evidence is insufficient, explicitly say so.

5. Distinguish reported facts from derived calculations.

6. Cite report evidence as:
   [Company | FY202X | p.X]

7. Do not make unsupported causal claims.

8. Mention important comparability caveats.

9. Answer in a professional consulting/research style.

10. Keep the answer concise but useful.

Structure the response as:

### Key Findings

### Evidence

### Caveats
"""

    client = get_gemini_client()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return {
        "answer": response.text
        if response and response.text
        else "No response was returned.",
        "sources": chunks,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("TrustRAG RAG TEST")
    print("=" * 60)

    test_question = (
        "What was TCS revenue in FY2025?"
    )

    try:

        results = retrieve(
            question=test_question,
            k=5,
            company="TCS",
            fiscal_year="FY2025",
        )

        print(
            f"\nRetrieved {len(results)} chunks.\n"
        )

        for i, result in enumerate(
            results,
            start=1,
        ):

            print(
                f"--- Result {i} ---"
            )

            print(
                f"Company: "
                f"{result.get('company')}"
            )

            print(
                f"Fiscal Year: "
                f"{result.get('fiscal_year')}"
            )

            print(
                f"Page: "
                f"{result.get('page')}"
            )

            print(
                f"Distance: "
                f"{result.get('distance')}"
            )

            print(
                f"Source: "
                f"{result.get('source_document')}"
            )

            print(
                f"Text:\n"
                f"{result.get('text', '')[:500]}"
            )

            print()

    except Exception as e:

        print(
            "\nRAG test failed:"
        )

        print(e)