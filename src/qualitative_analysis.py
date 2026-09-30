import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from rag import retrieve


# ============================================================
# CONFIGURATION
# ============================================================

COMPANIES = [
    "TCS",
    "Infosys",
    "HCLTech",
]

FISCAL_YEARS = [
    "FY2024",
    "FY2025",
]

OUTPUT_FILE = Path(
    "data/qualitative_analysis.json"
)

GEMINI_MODEL = "gemini-3.1-flash-lite"

# Number of chunks retrieved for each qualitative query
RETRIEVAL_K_PER_QUERY = 4

# Retry configuration for temporary Gemini errors
MAX_GEMINI_RETRIES = 3

# Small delay between retries
RETRY_DELAY_SECONDS = 3


# ============================================================
# QUALITATIVE CATEGORIES
# ============================================================

QUALITATIVE_CATEGORIES = [
    "strategic_changes",
    "management_changes",
    "sustainability_esg",
    "workforce_developments",
]


CATEGORY_LABELS = {
    "strategic_changes":
        "Strategic / Business Changes",

    "management_changes":
        "Management / Leadership Changes",

    "sustainability_esg":
        "Sustainability / ESG",

    "workforce_developments":
        "Workforce / Organizational Developments",
}


# ============================================================
# SEARCH QUERIES
# ============================================================

QUALITATIVE_QUERIES = {

    "strategic_changes": [
        "major strategic initiatives business strategy transformation growth priorities",
        "business transformation new services products markets expansion",
        "acquisitions divestitures restructuring investments strategic initiatives",
        "business outlook strategic priorities future growth opportunities",
    ],

    "management_changes": [
        "management leadership changes CEO CFO senior executives appointments resignations",
        "board of directors appointment resignation changes",
        "senior management changes executive leadership",
        "leadership transition organizational changes",
    ],

    "sustainability_esg": [
        "sustainability ESG environmental social governance initiatives",
        "carbon emissions net zero renewable energy climate targets",
        "diversity inclusion community social responsibility initiatives",
        "environmental sustainability performance targets progress",
    ],

    "workforce_developments": [
        "employee workforce hiring talent acquisition headcount developments",
        "reskilling upskilling employee learning development",
        "employee engagement workforce transformation initiatives",
        "attrition hiring organizational workforce changes",
    ],
}


# ============================================================
# PYDANTIC MODELS
# ============================================================

class QualitativeFinding(BaseModel):

    finding: str = Field(
        description=(
            "A concise factual statement describing a "
            "specific qualitative development."
        )
    )

    source_page: int = Field(
        description=(
            "The specific annual report page supporting "
            "the finding."
        )
    )

    evidence: str = Field(
        description=(
            "Short supporting evidence from the supplied "
            "annual report context."
        )
    )


class QualitativeAnalysis(BaseModel):

    strategic_changes: list[
        QualitativeFinding
    ] = Field(default_factory=list)

    management_changes: list[
        QualitativeFinding
    ] = Field(default_factory=list)

    sustainability_esg: list[
        QualitativeFinding
    ] = Field(default_factory=list)

    workforce_developments: list[
        QualitativeFinding
    ] = Field(default_factory=list)


# ============================================================
# ENVIRONMENT
# ============================================================

def get_gemini_client():

    from google import genai

    load_dotenv()

    api_key = os.getenv(
        "GOOGLE_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "GOOGLE_API_KEY not found in .env file"
        )

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# RETRIEVE QUALITATIVE EVIDENCE
# ============================================================

def retrieve_qualitative_evidence(
    company,
    fiscal_year
):

    all_chunks = []

    seen_ids = set()

    print(
        f"\nRetrieving qualitative evidence: "
        f"{company} | {fiscal_year}"
    )

    for category in QUALITATIVE_CATEGORIES:

        print(
            f"  Category: {category}"
        )

        queries = QUALITATIVE_QUERIES[
            category
        ]

        for query in queries:

            chunks = retrieve(
                query,
                k=RETRIEVAL_K_PER_QUERY,
                company=company,
                fiscal_year=fiscal_year,
            )

            for chunk in chunks:

                chunk_id = chunk["id"]

                if chunk_id in seen_ids:
                    continue

                seen_ids.add(
                    chunk_id
                )

                all_chunks.append(
                    chunk
                )

    print(
        f"  Unique evidence chunks: "
        f"{len(all_chunks)}"
    )

    return all_chunks


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_qualitative_context(
    chunks
):

    context_parts = []

    for chunk in chunks:

        source = Path(
            chunk["source_document"]
        ).stem

        page = chunk.get(
            "page"
        )

        label = (
            f"[{source}, p.{page}]"
        )

        context_parts.append(
            f"{label}\n"
            f"Company: {chunk.get('company')}\n"
            f"Fiscal Year: {chunk.get('fiscal_year')}\n"
            f"{chunk.get('text', '')}"
        )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# GEMINI PROMPT
# ============================================================

def build_prompt(
    company,
    fiscal_year,
    context
):

    return f"""
You are an evidence-grounded corporate research analyst.

You are analyzing the annual report of:

Company: {company}
Fiscal Year: {fiscal_year}

Use ONLY the supplied annual-report context.

Do NOT use outside knowledge.

Your job is to identify concrete qualitative developments
in four categories:

1. strategic_changes
2. management_changes
3. sustainability_esg
4. workforce_developments

IMPORTANT:

- Only report developments that are explicitly supported
  by the supplied context.
- Do not invent facts.
- Do not infer unsupported conclusions.
- Do not write generic descriptions of the company.
- Prefer concrete developments, initiatives, appointments,
  restructuring, acquisitions, expansions, targets,
  programs, or organizational changes.
- Every finding must contain a source_page.
- source_page MUST correspond to a page appearing in
  the supplied context.
- evidence must be directly supported by the context.
- If a category has no reliable evidence, return [].
- Do not create findings merely to fill categories.
- Keep each finding concise and business-oriented.

RETURN ONLY ONE JSON OBJECT.

The JSON MUST have exactly this structure:

{{
  "strategic_changes": [
    {{
      "finding": "concise factual finding",
      "source_page": 123,
      "evidence": "supporting evidence"
    }}
  ],

  "management_changes": [
    {{
      "finding": "concise factual finding",
      "source_page": 123,
      "evidence": "supporting evidence"
    }}
  ],

  "sustainability_esg": [
    {{
      "finding": "concise factual finding",
      "source_page": 123,
      "evidence": "supporting evidence"
    }}
  ],

  "workforce_developments": [
    {{
      "finding": "concise factual finding",
      "source_page": 123,
      "evidence": "supporting evidence"
    }}
  ]
}}

ANNUAL REPORT CONTEXT
=====================

{context}
"""


# ============================================================
# GEMINI CALL WITH RETRIES
# ============================================================

def call_gemini(
    client,
    prompt
):

    last_error = None

    for attempt in range(
        1,
        MAX_GEMINI_RETRIES + 1
    ):

        try:

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "temperature": 0,
                    "response_mime_type":
                        "application/json",
                }
            )

            return response.text

        except Exception as error:

            last_error = error

            print(
                f"  Gemini request failed "
                f"(attempt {attempt}/"
                f"{MAX_GEMINI_RETRIES})"
            )

            print(
                f"  Error: {error}"
            )

            if attempt < MAX_GEMINI_RETRIES:

                wait_time = (
                    RETRY_DELAY_SECONDS
                    * attempt
                )

                print(
                    f"  Retrying in "
                    f"{wait_time} seconds..."
                )

                time.sleep(
                    wait_time
                )

    raise last_error


# ============================================================
# EXTRACT JSON FROM GEMINI RESPONSE
# ============================================================

def extract_json_object(
    response_text
):

    text = response_text.strip()

    # --------------------------------------------------------
    # Remove markdown code fences if present
    # --------------------------------------------------------

    if text.startswith(
        "```"
    ):

        lines = text.splitlines()

        cleaned_lines = []

        for line in lines:

            if line.strip().startswith(
                "```"
            ):
                continue

            cleaned_lines.append(
                line
            )

        text = "\n".join(
            cleaned_lines
        ).strip()

    # --------------------------------------------------------
    # Direct JSON parsing
    # --------------------------------------------------------

    try:

        parsed = json.loads(
            text
        )

        if isinstance(
            parsed,
            dict
        ):

            return parsed

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Find the first JSON object
    # --------------------------------------------------------

    start = text.find(
        "{"
    )

    if start == -1:

        raise ValueError(
            "No JSON object found in Gemini response."
        )

    decoder = json.JSONDecoder()

    try:

        parsed, _ = decoder.raw_decode(
            text[start:]
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            "Gemini response contained invalid JSON."
        ) from error

    if not isinstance(
        parsed,
        dict
    ):

        raise ValueError(
            "Gemini response JSON was not an object."
        )

    return parsed


# ============================================================
# NORMALIZE CATEGORY
# ============================================================

def normalize_category(
    category
):

    if category is None:
        return None

    category = str(
        category
    ).strip().lower()

    category = (
        category
        .replace("_", " ")
        .replace("-", " ")
        .replace("&", "and")
        .replace("/", " ")
    )

    # Strategic
    if (
        "strateg" in category
        or "business change" in category
        or "business development" in category
        or "business transformation" in category
    ):

        return "strategic_changes"

    # Management
    if (
        "management" in category
        or "leadership" in category
        or "executive" in category
        or "board" in category
    ):

        return "management_changes"

    # ESG
    if (
        "sustain" in category
        or "esg" in category
        or "environment" in category
        or "climate" in category
        or "social responsibility" in category
    ):

        return "sustainability_esg"

    # Workforce
    if (
        "workforce" in category
        or "employee" in category
        or "organizational" in category
        or "talent" in category
        or "human resource" in category
    ):

        return "workforce_developments"

    return None


# ============================================================
# NORMALIZE GEMINI OUTPUT
# ============================================================

def normalize_gemini_output(
    response_text
):

    raw = extract_json_object(
        response_text
    )

    normalized = {
        "strategic_changes": [],
        "management_changes": [],
        "sustainability_esg": [],
        "workforce_developments": [],
    }

    # --------------------------------------------------------
    # Expected structured object
    # --------------------------------------------------------

    for category in QUALITATIVE_CATEGORIES:

        items = raw.get(
            category,
            []
        )

        if not isinstance(
            items,
            list
        ):

            continue

        for item in items:

            if not isinstance(
                item,
                dict
            ):

                continue

            finding_text = (
                item.get("finding")
                or item.get("insight")
                or item.get("summary")
            )

            page = (
                item.get("source_page")
                or item.get("page")
            )

            evidence = (
                item.get("evidence")
                or item.get("supporting_evidence")
                or ""
            )

            if not finding_text:
                continue

            if page is None:
                continue

            try:

                page = int(
                    str(page)
                    .replace("p.", "")
                    .strip()
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            normalized[
                category
            ].append(
                QualitativeFinding(
                    finding=str(
                        finding_text
                    ).strip(),

                    source_page=page,

                    evidence=str(
                        evidence
                    ).strip(),
                )
            )

    # --------------------------------------------------------
    # Also support flat list format if Gemini returns it
    # --------------------------------------------------------

    if not any(
        normalized.values()
    ):

        # Sometimes Gemini may return a flat list
        # under a generic key.

        possible_items = []

        for key in [
            "findings",
            "results",
            "items",
            "data",
        ]:

            value = raw.get(
                key
            )

            if isinstance(
                value,
                list
            ):

                possible_items.extend(
                    value
                )

        for item in possible_items:

            if not isinstance(
                item,
                dict
            ):

                continue

            category = normalize_category(
                item.get(
                    "category"
                )
            )

            if category is None:
                continue

            finding_text = (
                item.get("finding")
                or item.get("insight")
                or item.get("summary")
            )

            page = (
                item.get("source_page")
                or item.get("page")
            )

            evidence = (
                item.get("evidence")
                or item.get("supporting_evidence")
                or ""
            )

            if not finding_text:
                continue

            if page is None:
                continue

            try:

                page = int(
                    str(page)
                    .replace("p.", "")
                    .strip()
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            normalized[
                category
            ].append(
                QualitativeFinding(
                    finding=str(
                        finding_text
                    ).strip(),

                    source_page=page,

                    evidence=str(
                        evidence
                    ).strip(),
                )
            )

    return QualitativeAnalysis.model_validate(
        normalized
    )


# ============================================================
# VALIDATE SOURCE PAGES
# ============================================================

def validate_findings(
    analysis,
    chunks
):

    valid_pages = {
        int(chunk["page"])
        for chunk in chunks
        if chunk.get("page") is not None
    }

    for category in QUALITATIVE_CATEGORIES:

        findings = getattr(
            analysis,
            category
        )

        validated = []

        for finding in findings:

            if finding.source_page not in valid_pages:

                print(
                    f"  Removing unsupported "
                    f"page {finding.source_page}"
                )

                continue

            validated.append(
                finding
            )

        setattr(
            analysis,
            category,
            validated
        )

    return analysis


# ============================================================
# EXTRACT ONE COMPANY-YEAR
# ============================================================

def extract_qualitative_analysis(
    client,
    company,
    fiscal_year,
    chunks
):

    if not chunks:

        print(
            "  No evidence chunks retrieved."
        )

        return QualitativeAnalysis()

    context = build_qualitative_context(
        chunks
    )

    prompt = build_prompt(
        company,
        fiscal_year,
        context
    )

    response_text = call_gemini(
        client,
        prompt
    )

    analysis = normalize_gemini_output(
        response_text
    )

    analysis = validate_findings(
        analysis,
        chunks
    )

    return analysis


# ============================================================
# CONVERT RESULT TO JSON
# ============================================================

def analysis_to_dict(
    company,
    fiscal_year,
    analysis,
    chunks
):

    return {

        "company":
            company,

        "fiscal_year":
            fiscal_year,

        "source_documents":
            sorted(
                list(
                    {
                        chunk[
                            "source_document"
                        ]
                        for chunk in chunks
                    }
                )
            ),

        "evidence_chunks_used":
            len(chunks),

        "strategic_changes":
            [
                finding.model_dump()
                for finding
                in analysis.strategic_changes
            ],

        "management_changes":
            [
                finding.model_dump()
                for finding
                in analysis.management_changes
            ],

        "sustainability_esg":
            [
                finding.model_dump()
                for finding
                in analysis.sustainability_esg
            ],

        "workforce_developments":
            [
                finding.model_dump()
                for finding
                in analysis.workforce_developments
            ],
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "TRUSTRAG QUALITATIVE INTELLIGENCE ENGINE"
    )
    print("=" * 70)

    client = get_gemini_client()

    all_results = []

    for company in COMPANIES:

        for fiscal_year in FISCAL_YEARS:

            print("\n" + "-" * 70)

            print(
                f"COMPANY: {company}"
            )

            print(
                f"FISCAL YEAR: {fiscal_year}"
            )

            print("-" * 70)

            try:

                # ------------------------------------------------
                # Retrieve evidence
                # ------------------------------------------------

                chunks = retrieve_qualitative_evidence(
                    company,
                    fiscal_year
                )

                # ------------------------------------------------
                # Extract findings
                # ------------------------------------------------

                analysis = extract_qualitative_analysis(
                    client,
                    company,
                    fiscal_year,
                    chunks
                )

                # ------------------------------------------------
                # Store result
                # ------------------------------------------------

                result = analysis_to_dict(
                    company,
                    fiscal_year,
                    analysis,
                    chunks
                )

                all_results.append(
                    result
                )

                print(
                    f"\nStrategic findings: "
                    f"{len(result['strategic_changes'])}"
                )

                print(
                    f"Management findings: "
                    f"{len(result['management_changes'])}"
                )

                print(
                    f"ESG findings: "
                    f"{len(result['sustainability_esg'])}"
                )

                print(
                    f"Workforce findings: "
                    f"{len(result['workforce_developments'])}"
                )

            except Exception as error:

                # ------------------------------------------------
                # Do not kill the entire six-company run
                # ------------------------------------------------

                print(
                    f"\nERROR processing "
                    f"{company} {fiscal_year}:"
                )

                print(
                    error
                )

                # Store an explicit error record
                # rather than losing the whole run.

                all_results.append({

                    "company":
                        company,

                    "fiscal_year":
                        fiscal_year,

                    "source_documents":
                        [],

                    "evidence_chunks_used":
                        0,

                    "strategic_changes":
                        [],

                    "management_changes":
                        [],

                    "sustainability_esg":
                        [],

                    "workforce_developments":
                        [],

                    "error":
                        str(error),
                })

                continue

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    output = {

        "metadata": {

            "description":
                "TrustRAG qualitative intelligence "
                "extracted from annual reports",

            "companies":
                COMPANIES,

            "fiscal_years":
                FISCAL_YEARS,

            "categories":
                CATEGORY_LABELS,
        },

        "company_year_analysis":
            all_results,
    }

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
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 70)
    print(
        "QUALITATIVE ANALYSIS COMPLETE"
    )
    print("=" * 70)

    print(
        f"Company-year records: "
        f"{len(all_results)}"
    )

    successful = sum(
        1
        for result in all_results
        if "error" not in result
    )

    print(
        f"Successful records: "
        f"{successful}"
    )

    print(
        f"Saved to: "
        f"{OUTPUT_FILE}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()