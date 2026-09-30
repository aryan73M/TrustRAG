import json
from pathlib import Path

import pandas as pd
import streamlit as st

from google import genai
from google.genai import types
from dotenv import load_dotenv
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    research_client = genai.Client(
        api_key=GOOGLE_API_KEY
    )
else:
    research_client = None

RESEARCH_MODEL = "gemini-3.5-flash-lite"

# ============================================================
# CONFIG
# ============================================================

DATA_FILE = Path("data/validated_kpis.json")
EXCEL_FILE = Path("data/TrustRAG_Benchmarking_Report.xlsx")


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="TrustRAG | Corporate Intelligence",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    with open(
        DATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


companies = load_data()


# ============================================================
# HELPERS
# ============================================================

def get_value(company, metric):

    obj = company.get(metric, {})

    if obj.get("status") in [
        "reported",
        "derived"
    ]:

        return obj.get("value")

    return None


def get_metric(company, metric):

    return company.get(
        metric,
        {}
    )


# ============================================================
# HEADER
# ============================================================

st.title(
    "📊 TrustRAG"
)

st.subheader(
    "Corporate Intelligence & Benchmarking Platform"
)

st.caption(
    "Auditable financial research powered by "
    "retrieval-augmented generation."
)


st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Analysis Controls")

company_names = [
    company["company"]
    for company in companies
]

selected_companies = st.sidebar.multiselect(
    "Select companies",
    company_names,
    default=company_names
)


if not selected_companies:

    st.warning(
        "Please select at least one company."
    )

    st.stop()


selected = [
    company
    for company in companies
    if company["company"]
    in selected_companies
]


# ============================================================
# EXECUTIVE KPI CARDS
# ============================================================

st.header("Executive Snapshot")

cols = st.columns(len(selected))

for col, company in zip(cols, selected):

    with col:

        st.markdown(
            f"### {company['company']}"
        )

        revenue = get_value(
            company,
            "revenue"
        )

        growth = get_value(
            company,
            "revenue_growth"
        )

        margin = get_value(
            company,
            "operating_margin"
        )

        pat_margin = get_value(
            company,
            "pat_margin"
        )

        employees = get_value(
            company,
            "employees"
        )

        st.metric(
            "Revenue",
            f"₹{revenue:,.0f} Cr"
            if revenue is not None
            else "N/A"
        )

        st.metric(
            "Revenue Growth",
            f"{growth:.1f}%"
            if growth is not None
            else "N/A"
        )

        st.metric(
            "Operating Margin",
            f"{margin:.1f}%"
            if margin is not None
            else "N/A"
        )

        st.metric(
            "PAT Margin",
            f"{pat_margin:.2f}%"
            if pat_margin is not None
            else "N/A"
        )

        st.metric(
            "Employees",
            f"{employees:,.0f}"
            if employees is not None
            else "N/A"
        )


st.divider()


# ============================================================
# FINANCIAL BENCHMARK
# ============================================================

st.header("Financial Benchmark")

financial_metrics = {
    "Revenue (₹ Cr)": "revenue",
    "Revenue Growth (%)": "revenue_growth",
    "Operating Margin (%)": "operating_margin",
    "PAT (₹ Cr)": "pat",
    "PAT Margin (%)": "pat_margin",
    "EPS (₹)": "eps",
    "ROE (%)": "roe",
}


financial_data = []

for company in selected:

    row = {
        "Company": company["company"]
    }

    for label, metric in financial_metrics.items():

        row[label] = get_value(
            company,
            metric
        )

    financial_data.append(row)


financial_df = pd.DataFrame(
    financial_data
)

st.dataframe(
    financial_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# CHART
# ============================================================

st.subheader(
    "Revenue vs Operating Margin"
)

chart_data = financial_df[
    [
        "Company",
        "Revenue (₹ Cr)",
        "Operating Margin (%)"
    ]
].set_index("Company")

st.bar_chart(
    chart_data
)


# ============================================================
# WORKFORCE
# ============================================================

st.header("Workforce Intelligence")

workforce_data = []

for company in selected:

    workforce_data.append({

        "Company":
            company["company"],

        "Employees":
            get_value(
                company,
                "employees"
            ),

        "Attrition (%)":
            get_value(
                company,
                "attrition"
            ),

        "Revenue / Employee":
            get_value(
                company,
                "revenue_per_employee"
            ),

        "Employee Growth (%)":
            get_value(
                company,
                "employee_growth"
            ),
    })


workforce_df = pd.DataFrame(
    workforce_data
)

st.dataframe(
    workforce_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# EVIDENCE EXPLORER
# ============================================================

st.header("🔎 Evidence Explorer")

company_choice = st.selectbox(
    "Company",
    selected_companies
)

company = next(
    c for c in companies
    if c["company"] == company_choice
)


metric_options = [
    "revenue",
    "revenue_growth",
    "operating_margin",
    "pat",
    "eps",
    "roe",
    "free_cash_flow",
    "capex",
    "cash_liquid_assets",
    "employees",
    "attrition",
    "pat_margin",
    "revenue_per_employee",
]


metric_choice = st.selectbox(
    "KPI",
    metric_options
)


metric = get_metric(
    company,
    metric_choice
)


col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Status",
        metric.get(
            "status",
            "N/A"
        )
    )

with col2:

    value = metric.get("value")

    st.metric(
        "Value",
        str(value)
        if value is not None
        else "N/A"
    )

with col3:

    st.metric(
        "Source Page",
        str(
            metric.get(
                "source_page",
                "N/A"
            )
        )
    )


if metric.get("evidence"):

    st.markdown(
        "**Evidence**"
    )

    st.info(
        metric["evidence"]
    )


if metric.get("reported_label"):

    st.markdown(
        f"**Reported label:** "
        f"{metric['reported_label']}"
    )


if metric.get("notes"):

    st.markdown(
        f"**Notes:** "
        f"{metric['notes']}"
    )


# ============================================================
# COMPARABILITY
# ============================================================

st.header("⚖️ Comparability")

comparability = company.get(
    "comparability",
    {}
)

if metric_choice in comparability:

    details = comparability[
        metric_choice
    ]

    st.write(
        f"**Comparability level:** "
        f"{details.get('level', 'N/A')}"
    )

    st.write(
        details.get(
            "reason",
            ""
        )
    )

else:

    st.caption(
        "No comparability note available."
    )


# ============================================================
# KPI COVERAGE
# ============================================================

st.header("📋 KPI Coverage")

coverage_rows = []

for company in selected:

    reported = 0
    total = 0

    for metric_name in financial_metrics.values():

        total += 1

        if get_metric(
            company,
            metric_name
        ).get("status") == "reported":

            reported += 1

    coverage_rows.append({

        "Company":
            company["company"],

        "Available KPIs":
            reported,

        "Total KPIs":
            total,

        "Coverage (%)":
            round(
                reported / total * 100,
                1
            ),
    })


coverage_df = pd.DataFrame(
    coverage_rows
)

st.dataframe(
    coverage_df,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# RESEARCH COPILOT
# ============================================================

st.header("🤖 Research Copilot")

st.caption(
    "Ask questions about the validated FY2024 benchmark. "
    "Responses are generated only from the extracted evidence."
)

research_question = st.text_area(
    "Ask a corporate research question",
    placeholder=(
        "Example: Compare TCS, Infosys and HCLTech "
        "on profitability and workforce efficiency."
    ),
    height=100
)


def build_research_context(selected_companies):

    context_parts = []

    for company in selected_companies:

        context_parts.append(
            f"\n\n===== {company['company']} ====="
        )

        metrics = [
            "revenue",
            "revenue_growth",
            "operating_margin",
            "pat",
            "pat_margin",
            "eps",
            "roe",
            "employees",
            "attrition",
            "revenue_per_employee",
            "employee_growth",
            "free_cash_flow",
            "capex",
            "cash_liquid_assets",
        ]

        for metric_name in metrics:

            metric = company.get(
                metric_name,
                {}
            )

            value = metric.get("value")

            if value is None:
                continue

            context_parts.append(
                f"""
Metric: {metric_name}
Value: {value}
Unit: {metric.get('unit')}
Status: {metric.get('status')}
Reported Label: {metric.get('reported_label')}
Source Page: {metric.get('source_page')}
Evidence: {metric.get('evidence')}
Notes: {metric.get('notes')}
"""
            )

    return "\n".join(context_parts)


if research_question:

    if research_client is None:

        st.error(
            "GOOGLE_API_KEY was not found in the environment."
        )

    else:

        if st.button(
            "🔍 Analyze",
            type="primary"
        ):

            research_context = build_research_context(
                selected
            )

            research_prompt = f"""
You are TrustRAG, an evidence-grounded corporate
research assistant.

Answer the user's question using ONLY the supplied
validated FY2024 company data and evidence.

USER QUESTION:
{research_question}

SUPPLIED DATA:
{research_context}

RULES:

1. Do not use outside knowledge.
2. Do not invent missing values.
3. If a metric is unavailable, explicitly say
   "Not available in the extracted evidence."
4. Preserve the company's reported terminology.
5. Clearly distinguish reported metrics from
   derived metrics.
6. Cite source pages inline using:
   [Company, p.X]
7. Mention comparability caveats whenever relevant.
8. Do not create unsupported rankings.
9. Keep the answer concise and business-oriented.
10. If the question cannot be answered from the
    supplied data, say so.

Return a professional corporate research response.
"""

            with st.spinner(
                "Analyzing validated evidence..."
            ):

                try:

                    response = research_client.models.generate_content(
                        model=RESEARCH_MODEL,
                        contents=research_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1
                        )
                    )

                    st.markdown("### Research Output")

                    st.markdown(
                        response.text
                    )

                except Exception as e:

                    st.error(
                        f"Research request failed: {e}"
                    )

# ============================================================
# DOWNLOAD EXCEL
# ============================================================

st.header("📥 Research Output")

if EXCEL_FILE.exists():

    with open(
        EXCEL_FILE,
        "rb"
    ) as f:

        st.download_button(
            label="Download Excel Benchmarking Report",
            data=f,
            file_name="TrustRAG_Benchmarking_Report.xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
        )

else:

    st.warning(
        "Excel benchmarking report not found."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "TrustRAG | Evidence-grounded corporate intelligence "
    "| FY2024 annual reports"
)   