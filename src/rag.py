import json
import os
import time
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# Configuration
# --------------------------------------------------

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "chunks_350_v2"

MODEL_NAME = "BAAI/bge-small-en-v1.5"
GEMINI_MODEL = "gemini-3.1-flash-lite"

TOP_K = 5
SYSTEM_PROMPT = """
You answer questions using ONLY the context provided.

CITATION RULES:
1. Every factual claim must have a citation.
2. Use exactly this format: [source, p.X]
3. Cite the specific page that supports the claim.
4. Do NOT combine multiple pages into one citation such as [source, p.X, p.Y].
5. If different claims are supported by different pages, give each claim its own citation.
6. Never invent a page number.
7. Do not cite information that is not supported by the provided context.

If the context does not contain the answer, reply exactly:

"Not found in the provided documents."

Do not use outside knowledge.
Do not guess numbers.

Keep answers concise and directly answer the question.
"""


# --------------------------------------------------
# Environment
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)


# --------------------------------------------------
# Embedding model + ChromaDB
# --------------------------------------------------

print("Loading embedding model...")

embedding_model = SentenceTransformer(MODEL_NAME)

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)


# --------------------------------------------------
# System prompt
# --------------------------------------------------


# --------------------------------------------------
# Retrieve relevant chunks
# --------------------------------------------------
def retrieve(question, k=TOP_K, company=None, fiscal_year=None):
    """
    Retrieve relevant chunks from ChromaDB.

    Company filtering is handled by ChromaDB.
    Fiscal-year filtering is handled client-side because
    the installed ChromaDB version does not support the
    required multi-condition `where` filter in get/query.
    """

    query_embedding = embedding_model.encode(
        question,
        normalize_embeddings=True
    ).tolist()

    # Retrieve extra candidates when fiscal-year filtering
    # may be required.
    retrieval_k = k * 5 if fiscal_year else k

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": retrieval_k,
        "include": ["documents", "metadatas", "distances"],
    }

    # ChromaDB supports this single-condition filter.
    if company:
        query_kwargs["where"] = {
            "company": company
        }

    results = collection.query(**query_kwargs)

    retrieved = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    for chunk_id, text, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances
    ):
        # Client-side fiscal year filtering
        if fiscal_year and metadata.get("fiscal_year") != fiscal_year:
            continue

        retrieved.append({
            "id": chunk_id,
            "text": text,
            "company": metadata.get("company"),
            "fiscal_year": metadata.get("fiscal_year"),
            "source_document": metadata.get("source_document"),
            "page": metadata.get("page"),
            "distance": distance,
        })

        if len(retrieved) >= k:
            break

    return retrieved


# --------------------------------------------------
# Build context for Gemini
# --------------------------------------------------

def build_context(chunks):

    context_parts = []

    for chunk in chunks:

        source = Path(
            chunk["source_document"]
        ).stem

        label = (
            f"[{source}, "
            f"p.{chunk['page']}]"
        )

        context_parts.append(
            f"{label}\n"
            f"Company: {chunk['company']}\n"
            f"Fiscal Year: {chunk['fiscal_year']}\n"
            f"{chunk['text']}"
        )

    return "\n\n".join(context_parts)

# --------------------------------------------------
# Answer question
# --------------------------------------------------

def answer(question, k=TOP_K):

    start_time = time.perf_counter()

    # Retrieve
    chunks = retrieve(question, k)

    retrieval_time = time.perf_counter()

    context = build_context(chunks)

    prompt = f"""

{SYSTEM_PROMPT}

CONTEXT:

{context}

QUESTION:

{question}
"""

    # Gemini call
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0
        }
    )

    end_time = time.perf_counter()

    answer_text = response.text

    # Token information if available
    usage = getattr(response, "usage_metadata", None)

    if usage:
        input_tokens = getattr(
            usage,
            "prompt_token_count",
            None
        )

        output_tokens = getattr(
            usage,
            "candidates_token_count",
            None
        )
    else:
        input_tokens = None
        output_tokens = None

        # Log evaluation data
    log_file = Path("evals/log.jsonl")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "question": question,
        "retrieved_chunk_ids": [
            chunk["id"] for chunk in chunks
        ],
        "answer": answer_text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "retrieval_latency_ms":
            (retrieval_time - start_time) * 1000,
        "total_latency_ms":
            (end_time - start_time) * 1000,
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                log_entry,
                ensure_ascii=False
            ) + "\n"
        )

    return {
        "question": question,
        "answer": answer_text,
        "retrieved_chunks": chunks,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "retrieval_latency_ms":
            (retrieval_time - start_time) * 1000,
        "total_latency_ms":
            (end_time - start_time) * 1000,
    }


# --------------------------------------------------
# Test
# --------------------------------------------------

if __name__ == "__main__":

    question = "What was TCS revenue in FY24?"

    result = answer(question)

    print("\n" + "=" * 70)
    print("QUESTION")
    print("=" * 70)

    print(result["question"])

    print("\n" + "=" * 70)
    print("ANSWER")
    print("=" * 70)

    print(result["answer"])

    print("\n" + "=" * 70)
    print("RETRIEVED CHUNKS")
    print("=" * 70)

    for chunk in result["retrieved_chunks"]:

        print(
            f"\n{chunk['company']} | "
            f"{chunk['fiscal_year']} | "
            f"{chunk['source_document']} | "
            f"Page {chunk['page']} | "
            f"Distance {chunk['distance']:.4f}"
        )       
    print("\n" + "=" * 70)
    print("METRICS")
    print("=" * 70)

    print(
        f"Input tokens: {result['input_tokens']}"
    )

    print(
        f"Output tokens: {result['output_tokens']}"
    )

    print(
        f"Retrieval latency: "
        f"{result['retrieval_latency_ms']:.2f} ms"
    )

    print(
        f"Total latency: "
        f"{result['total_latency_ms']:.2f} ms"
    )