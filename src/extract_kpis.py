import json
import os
import time
import random
from pathlib import Path
from typing import Optional

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

CHROMA_DIR = "./chroma_db"
COLLECTION_NAME = "chunks_350_v2"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
GEMINI_MODEL = "gemini-3.5-flash-lite"
TOP_K_PER_QUERY = 3

# ============================================================
# EXTRACTION TARGET
# ============================================================

COMPANIES = [
    "TCS",
    "Infosys",
    "HCLTech",
]

TARGET_FISCAL_YEAR = "FY2025"

OUTPUT_FILE = Path(
    f"data/kpis_{TARGET_FISCAL_YEAR}.json"
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


# ============================================================
# EMBEDDING + CHROMADB
# ============================================================

print("Loading embedding model...")

embedding_model = SentenceTransformer(
    EMBEDDING_MODEL
)

chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR
)

collection = chroma_client.get_collection(
    name=COLLECTION_NAME
)


# ============================================================
# KPI SCHEMA
# ============================================================

class KPIResult(BaseModel):

    status: str = Field(
        description=(
            "Use exactly one of: "
            "'reported', 'not_found', 'not_comparable'."
        )
    )

    value: Optional[float] = Field(
        default=None,
        description="Numeric value for the requested fiscal year if supported."
    )

    unit: Optional[str] = Field(
        default=None,
        description="Unit such as INR crore, %, INR, employees."
    )

    reported_label: Optional[str] = Field(
        default=None,
        description="Company's own terminology for this metric."
    )

    fiscal_year: Optional[str] = Field(
        default=None,
        description="Financial year of the value."
    )

    source_page: Optional[int] = Field(
        default=None,
        description="PDF page supporting the value."
    )

    evidence: Optional[str] = Field(
        default=None,
        description="Short supporting evidence excerpt."
    )

    notes: Optional[str] = Field(
        default=None,
        description="Definition or comparability caveat."
    )


class CompanyKPIResults(BaseModel):

    company: str

    revenue: KPIResult
    revenue_growth: KPIResult
    operating_margin: KPIResult
    pat: KPIResult
    eps: KPIResult
    roe: KPIResult
    free_cash_flow: KPIResult
    capex: KPIResult
    operating_cash_flow: KPIResult
    cash_liquid_assets: KPIResult
    employees: KPIResult
    attrition: KPIResult



# ============================================================
# KPI SEARCH QUERIES
# ============================================================

def build_kpi_queries(fiscal_year):

    year_number = int(fiscal_year.replace("FY", ""))
    previous_year = f"FY{year_number - 1}"

    return [
        f"revenue from operations {fiscal_year} {previous_year}",
        f"revenue growth year on year {fiscal_year}",
        f"operating margin EBIT operating profit ratio {fiscal_year}",
        f"profit after tax PAT {fiscal_year}",
        f"diluted earnings per share EPS {fiscal_year}",
        f"return on equity ROE return on net worth {fiscal_year}",
        f"free cash flow {fiscal_year}",
        f"capital expenditure capex {fiscal_year}",
        f"cash flow from operating activities operating cash flow CFO {fiscal_year}",
        f"cash cash equivalents liquid investments {fiscal_year}",
        f"employee headcount total employees {fiscal_year}",
        f"employee attrition attrition rate {fiscal_year}",
    ]


# ============================================================
# RETRIEVAL
# ============================================================

def retrieve_company_evidence(company, fiscal_year="FY2024"):

    all_chunks = {}

    kpi_queries = build_kpi_queries(fiscal_year)

    for query in kpi_queries:

        query_embedding = embedding_model.encode(
            [query]
        ).tolist()

        # Retrieve extra candidates because we apply
        # fiscal-year filtering after Chroma retrieval.
        retrieval_k = TOP_K_PER_QUERY * 5

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=retrieval_k,
            where={"company": company},
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        if not results["documents"]:
            continue

        for i in range(len(results["documents"][0])):

            metadata = results["metadatas"][0][i]

            # Fiscal-year filtering is done client-side
            # because the installed Chroma version does
            # not support the required multi-condition filter.
            if metadata.get("fiscal_year") != fiscal_year:
                continue

            chunk_id = results["ids"][0][i]

            all_chunks[chunk_id] = {
                "id": chunk_id,
                "text": results["documents"][0][i],
                "company": metadata.get("company"),
                "fiscal_year": metadata.get("fiscal_year"),
                "source_document": metadata.get("source_document"),
                "page": metadata.get("page"),
                "distance": results["distances"][0][i],
            }

    return list(all_chunks.values())

# ============================================================
# CONTEXT
# ============================================================

def build_context(chunks):

    chunks = sorted(
        chunks,
        key=lambda x: x["distance"]
    )

    parts = []

    for chunk in chunks:

        parts.append(
            f"""
SOURCE: {chunk['company']}
PAGE: {chunk['page']}
CHUNK_ID: {chunk['id']}

TEXT:
{chunk['text']}
"""
        )

    return "\n\n".join(parts)


# ============================================================
# GEMINI EXTRACTION
# ============================================================

def extract_company_kpis(company, chunks, fiscal_year="FY2024"):

    context = build_context(chunks)

    prompt = f"""
You are a financial-document extraction engine.

COMPANY:
{company}

FINANCIAL YEAR:
{fiscal_year}

Your task is to extract the following financial and
operational KPIs from the supplied annual-report evidence:

1. Revenue from Operations
2. Revenue Growth
3. Operating / EBIT Margin
4. Profit After Tax
5. Diluted EPS
6. Return on Equity
7. Free Cash Flow 
8. Capital Expenditure
9. Operating Cash Flow
10. Cash & Liquid Investments
11. Employee Headcount
12. Employee Attrition

IMPORTANT RULES:

1. Use ONLY the supplied annual-report evidence.
2. Do NOT use outside knowledge.
3. Do NOT guess.
4. Prefer {fiscal_year} over the previous fiscal year.
5. If a KPI is not clearly supported, use:
   status = "not_found"
6. If a metric exists but its definition is materially
   different or cannot reasonably be compared, use:
   status = "not_comparable"
7. Preserve the company's own terminology.
8. Give the exact page containing the supporting evidence.
9. Evidence must come from the supplied context.
10. Do not calculate derived metrics.
11. For revenue growth, use the company's explicitly
    reported growth rate if available.
12. Do not confuse standalone and consolidated figures.
13. Prefer consolidated figures where the annual report
    clearly presents them as the company's primary
    financial performance figures.
14. If multiple values appear, select the value that
    corresponds to {fiscal_year} and explain any ambiguity
    in notes.
15. Every reported value must have supporting evidence.
16. Extract Operating Cash Flow from the consolidated
    statement of cash flows when available.

17. Prefer the actual statement of cash flows over
    management commentary or narrative discussion.

18. For Capital Expenditure, prefer cash expenditure
    on property, plant and equipment and intangible
    assets when clearly supported by the annual report.

19. Do NOT calculate Free Cash Flow.

20. Do NOT calculate Operating Cash Flow.

21. If Operating Cash Flow is not clearly supported
    by the supplied evidence, use status = "not_found".

22. If Capital Expenditure is not clearly supported
    by the supplied evidence, use status = "not_found".

23. Preserve the company's reported terminology
    for Operating Cash Flow and Capital Expenditure.

24. Make sure Operating Cash Flow and Capital Expenditure
    correspond to the same fiscal year and consolidated/
    standalone basis.

OUTPUT:
OUTPUT:

Return one structured result for each of the 12 KPIs.

The 12 KPIs are:

1. revenue
2. revenue_growth
3. operating_margin
4. pat
5. eps
6. roe
7. free_cash_flow
8. capex
9. operating_cash_flow
10. cash_liquid_assets
11. employees
12. attrition

SUPPLIED ANNUAL-REPORT EVIDENCE:

{context}
"""

    max_retries = 4

    for attempt in range(1, max_retries + 1):

        try:

            print(
                f"Gemini attempt {attempt}/{max_retries}..."
            )

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                    response_schema=CompanyKPIResults,
                ),
            )

            print("Gemini extraction successful.")

            company_result = CompanyKPIResults.model_validate_json(
                response.text
            )
            for metric_name in [
                "revenue",
                "revenue_growth",
                "operating_margin",
                "pat",
                "eps",
                "roe",
                "free_cash_flow",
                "capex",
                "operating_cash_flow",
                "cash_liquid_assets",
                "employees",
                "attrition",
            ]:
                metric = getattr(company_result, metric_name)

                if metric is not None:
                    metric.fiscal_year = fiscal_year

            return company_result

        except Exception as e:

            error_text = str(e)

            # ------------------------------------------------
            # 503: Temporary Gemini server/model overload
            # ------------------------------------------------
            if "503" in error_text or "UNAVAILABLE" in error_text:

                if attempt == max_retries:
                    print(
                        "503 persisted after all retries."
                    )
                    raise

                # Exponential backoff:
                # 5s → 10s → 20s
                wait_time = (5 * (2 ** (attempt - 1))) + random.uniform(0, 2)

                print(
                    f"Gemini returned 503. "
                    f"Waiting {wait_time:.1f} seconds before retry..."
                )

                time.sleep(wait_time)

            # ------------------------------------------------
            # 429: Quota exceeded
            # ------------------------------------------------
            elif "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:

                # Daily quota cannot be fixed by retrying.
                if "PerDay" in error_text or "per_day" in error_text.lower():

                    print(
                        "Daily Gemini quota reached. "
                        "Retrying will not help until the quota resets."
                    )

                    raise

                # For temporary per-minute quota limits,
                # retry after a cooldown.
                if attempt == max_retries:
                    print(
                        "429 persisted after all retries."
                    )
                    raise

                wait_time = (15 * attempt) + random.uniform(0, 3)

                print(
                    f"Gemini returned 429. "
                    f"Waiting {wait_time:.1f} seconds before retry..."
                )

                time.sleep(wait_time)

            else:
                # Any other error should not be blindly retried.
                raise



# ============================================================
# MAIN
# ============================================================

def main():

    results = []

    start = time.perf_counter()

    print()
    print("=" * 70)
    print("TRUSTRAG BATCH KPI EXTRACTION")
    print("=" * 70)

    print(
        f"Companies: {len(COMPANIES)}"
    )

    print(
        "Gemini extraction calls: 1 per company"
    )

    print(
        f"Expected total Gemini calls: {len(COMPANIES)}"
    )

    print()

    for company_index, company in enumerate(
        COMPANIES,
        start=1
    ):

        print("-" * 70)
        print(
            f"[{company_index}/{len(COMPANIES)}] "
            f"Processing {company}"
        )
        print("-" * 70)

        try:

            print(
                "Retrieving evidence..."
            )

            chunks = retrieve_company_evidence(
                company,
                fiscal_year=TARGET_FISCAL_YEAR
            )

            print(
                f"Retrieved {len(chunks)} unique chunks."
            )

            print(
                "Sending ONE structured extraction request..."
            )

            result = extract_company_kpis(
                company,
                chunks,
                fiscal_year=TARGET_FISCAL_YEAR
            )

            results.append(
                result.model_dump()
            )

            print(
                f"{company} extraction successful."
            )

            # Print quick summary

            for metric_name in [
                "revenue",
                "operating_margin",
                "pat",
                "eps",
                "roe",
                "employees",
            ]:

                metric = getattr(result,
                    metric_name
                )

                print(
                    f"  {metric_name}: "
                    f"{metric.value} "
                    f"| {metric.status} "
                    f"| p.{metric.source_page}"
                )

            # Small pause between companies
            # to avoid hitting request-per-minute limits.

            if company_index < len(COMPANIES):

                print(
                    "\nWaiting 5 seconds before next company..."
                )

                time.sleep(5)

        except Exception as e:

            print(
                f"ERROR processing {company}: {e}"
            )

            results.append(
                {
                    "company": company,
                    "error": str(e),
                }
            )

    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    elapsed = time.perf_counter() - start

    print()
    print("=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print(
        f"Total runtime: {elapsed:.2f} seconds"
    )


if __name__ == "__main__":
    main()