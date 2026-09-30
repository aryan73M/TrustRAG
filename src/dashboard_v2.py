import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

from rag import retrieve


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="TrustRAG | Corporate Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


QUANT_FILE = Path("data/quantitative_analysis.json")
MULTIYEAR_FILE = Path("data/multiyear_kpis.json")
QUAL_FILE = Path("data/qualitative_analysis.json")
EXCEL_FILE = Path("data/TrustRAG_Benchmarking_Report.xlsx")

COMPANIES = [
    "TCS",
    "Infosys",
    "HCLTech",
]

YEARS = [
    "FY2024",
    "FY2025",
]

RESEARCH_MODEL = "gemini-3.1-flash-lite"


# ============================================================
# METRIC CONFIGURATION
# ============================================================

METRIC_LABELS = {

    "revenue":
        "Revenue (₹ Cr)",

    "revenue_growth":
        "Revenue Growth (%)",

    "operating_margin":
        "Operating Margin (%)",

    "pat":
        "PAT (₹ Cr)",

    "pat_margin":
        "PAT Margin (%)",

    "eps":
        "EPS (₹)",

    "roe":
        "ROE (%)",

    "free_cash_flow":
        "Reported FCF",

    "standardized_fcf":
        "Standardized FCF (₹ Cr)",

    "capex":
        "Capex (₹ Cr)",

    "operating_cash_flow":
        "Operating Cash Flow (₹ Cr)",

    "cash_liquid_assets":
        "Cash / Liquid Assets (₹ Cr)",

    "employees":
        "Employees",

    "attrition":
        "Attrition (%)",

    "revenue_per_employee":
        "Revenue / Employee",

    "employee_growth":
        "Employee Growth (%)",

    "fcf_margin":
        "FCF Margin (%)",
}


RATE_METRICS = {

    "revenue_growth",

    "operating_margin",

    "roe",

    "attrition",

    "pat_margin",

    "fcf_margin",

    "employee_growth",
}


QUAL_CATEGORIES = {

    "strategic_changes":
        "Strategic / Business Changes",

    "management_changes":
        "Management / Leadership",

    "sustainability_esg":
        "Sustainability / ESG",

    "workforce_developments":
        "Workforce / Organization",
}


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    .stApp {
        background: #f5f7fb;
    }

    .main .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
        padding-bottom: 3rem;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {

        background:
            linear-gradient(
                180deg,
                #111827 0%,
                #172033 100%
            );

        border-right:
            1px solid #263244;
    }

    section[data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: white;
    }

    section[data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
        font-weight: 600;
    }


    /* ========================================================
       HEADER
       ======================================================== */

    .trust-header {

        background:
            linear-gradient(
                135deg,
                #0f172a 0%,
                #1e293b 55%,
                #26364d 100%
            );

        border-radius: 18px;

        padding:
            1.9rem 2.2rem;

        margin-bottom: 1.5rem;

        box-shadow:
            0 12px 30px
            rgba(15, 23, 42, 0.14);
    }

    .trust-title {

        color: white;

        font-size: 2.45rem;

        font-weight: 850;

        letter-spacing: -1px;

        line-height: 1.05;
    }

    .trust-subtitle {

        color: #cbd5e1;

        font-size: 1rem;

        margin-top: 0.35rem;

        margin-bottom: 0.9rem;
    }

    .trust-badge {

        display: inline-block;

        padding:
            0.32rem 0.7rem;

        margin-right: 0.4rem;

        margin-bottom: 0.2rem;

        border-radius: 999px;

        background:
            rgba(255,255,255,0.09);

        border:
            1px solid
            rgba(255,255,255,0.12);

        color: #e2e8f0;

        font-size: 0.73rem;

        font-weight: 650;
    }


    /* ========================================================
       SECTION HEADERS
       ======================================================== */

    .section-kicker {

        color: #64748b;

        font-size: 0.73rem;

        font-weight: 800;

        text-transform: uppercase;

        letter-spacing: 1.1px;

        margin-bottom: 0.25rem;
    }

    .section-title {

        color: #0f172a;

        font-size: 1.55rem;

        font-weight: 800;

        letter-spacing: -0.4px;

        margin-bottom: 0.2rem;
    }

    .section-description {

        color: #64748b;

        font-size: 0.88rem;

        margin-bottom: 1rem;
    }


    /* ========================================================
       COMPANY CARDS
       ======================================================== */

    .company-card {

        background: white;

        border:
            1px solid #e2e8f0;

        border-radius: 16px;

        padding: 1.25rem;

        min-height: 245px;

        box-shadow:
            0 5px 18px
            rgba(15, 23, 42, 0.055);

        transition:
            transform 0.15s ease,
            box-shadow 0.15s ease;
    }

    .company-card:hover {

        transform:
            translateY(-2px);

        box-shadow:
            0 10px 28px
            rgba(15, 23, 42, 0.09);
    }

    .company-name {

        color: #0f172a;

        font-size: 1.15rem;

        font-weight: 800;

        margin-bottom: 0.1rem;
    }

    .company-year {

        color: #94a3b8;

        font-size: 0.74rem;

        margin-bottom: 1rem;
    }

    .company-stat-label {

        color: #64748b;

        font-size: 0.68rem;

        font-weight: 700;

        text-transform: uppercase;

        letter-spacing: 0.45px;
    }

    .company-stat-value {

        color: #111827;

        font-size: 1.05rem;

        font-weight: 800;

        margin-bottom: 0.65rem;
    }


    /* ========================================================
       KPI CARDS
       ======================================================== */

    .metric-card {

        background: white;

        border:
            1px solid #e2e8f0;

        border-radius: 14px;

        padding: 1.05rem 1.15rem;

        min-height: 110px;

        box-shadow:
            0 4px 14px
            rgba(15,23,42,0.045);
    }

    .metric-label {

        color: #64748b;

        font-size: 0.7rem;

        text-transform: uppercase;

        letter-spacing: 0.55px;

        font-weight: 750;
    }

    .metric-value {

        color: #0f172a;

        font-size: 1.55rem;

        font-weight: 850;

        margin-top: 0.35rem;
    }

    .metric-sub {

        color: #94a3b8;

        font-size: 0.72rem;

        margin-top: 0.15rem;
    }


    /* ========================================================
       INSIGHT CARDS
       ======================================================== */

    .insight-card {

        background: white;

        border:
            1px solid #e2e8f0;

        border-radius: 13px;

        padding: 1rem 1.1rem;

        margin-bottom: 0.75rem;

        box-shadow:
            0 3px 10px
            rgba(15,23,42,0.035);
    }

    .insight-title {

        color: #111827;

        font-size: 0.92rem;

        font-weight: 750;

        margin-bottom: 0.35rem;
    }

    .insight-text {

        color: #475569;

        font-size: 0.84rem;

        line-height: 1.55;
    }


    /* ========================================================
       EVIDENCE
       ======================================================== */

    .evidence-box {

        background: #f8fafc;

        border-left:
            4px solid #475569;

        border-radius:
            0 9px 9px 0;

        padding:
            0.85rem 1rem;

        margin:
            0.6rem 0 0.8rem 0;

        color: #475569;

        font-size: 0.84rem;

        line-height: 1.55;
    }

    .source-tag {

        display: inline-block;

        background: #f1f5f9;

        color: #475569;

        border-radius: 999px;

        padding:
            0.25rem 0.55rem;

        font-size: 0.68rem;

        font-weight: 700;
    }


    /* ========================================================
       STATUS
       ======================================================== */

    .status-good {

        display: inline-block;

        background: #f0fdf4;

        color: #166534;

        border:
            1px solid #bbf7d0;

        border-radius: 999px;

        padding:
            0.22rem 0.55rem;

        font-size: 0.68rem;

        font-weight: 700;
    }


    /* ========================================================
       TABLES
       ======================================================== */

    div[data-testid="stDataFrame"] {

        border-radius: 11px;

        overflow: hidden;

        border:
            1px solid #e2e8f0;
    }


    /* ========================================================
       TABS
       ======================================================== */

    button[data-baseweb="tab"] {

        font-weight: 700;

        font-size: 0.86rem;
    }

    button[data-baseweb="tab"][aria-selected="true"] {

        color: #0f172a;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {

        border-radius: 9px;

        font-weight: 700;

        min-height: 2.5rem;
    }


    /* ========================================================
       DOWNLOAD
       ======================================================== */

    .stDownloadButton > button {

        width: 100%;

        border-radius: 9px;

        font-weight: 700;
    }


    /* ========================================================
       FOOTER
       ======================================================== */

    .trust-footer {

        text-align: center;

        color: #94a3b8;

        font-size: 0.72rem;

        padding:
            1.5rem 0;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_json(path):

    if not path.exists():
        return {}

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception:

        return {}


quant = load_json(QUANT_FILE)

multiyear = load_json(
    MULTIYEAR_FILE
)

qual = load_json(
    QUAL_FILE
)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_records(data):

    if isinstance(data, list):

        return [
            x for x in data
            if isinstance(x, dict)
        ]

    if isinstance(data, dict):

        possible_keys = [

            "company_year_data",

            "records",

            "data",

            "company_year_analysis",

            "results",
        ]

        for key in possible_keys:

            value = data.get(key)

            if isinstance(value, list):

                return [
                    x for x in value
                    if isinstance(x, dict)
                ]

    return []


records = normalize_records(
    multiyear
)

qual_records = normalize_records(
    qual
)


# ============================================================
# DATA HELPERS
# ============================================================

def get_record(
    company,
    year
):

    for record in records:

        if (
            record.get("company")
            == company
            and
            record.get("fiscal_year")
            == year
        ):

            return record

    return None


def get_qual_record(
    company,
    year
):

    for record in qual_records:

        if (
            record.get("company")
            == company
            and
            record.get("fiscal_year")
            == year
        ):

            return record

    return None


def metric_obj(
    record,
    metric
):

    if not record:
        return {}

    value = record.get(
        metric
    )

    if isinstance(
        value,
        dict
    ):

        return value

    return {
        "value": value
    }


def metric_value(
    record,
    metric
):

    obj = metric_obj(
        record,
        metric
    )

    value = obj.get(
        "value"
    )

    if isinstance(
        value,
        (int, float)
    ):

        return value

    return None


def fmt_value(
    value,
    metric
):

    if value is None:
        return "N/A"

    if metric in RATE_METRICS:

        return f"{value:.1f}%"

    if metric == "eps":

        return f"₹{value:,.2f}"

    if metric == "revenue_per_employee":

        return f"{value:,.3f}"

    if metric == "employees":

        return f"{value:,.0f}"

    return f"₹{value:,.0f} Cr"


def safe_num(
    value
):

    if isinstance(
        value,
        (int, float)
    ):

        return value

    return None


# ============================================================
# QUANTITATIVE HELPERS
# ============================================================

def yoy_for(
    company,
    metric
):

    data = quant.get(
        "yoy_analysis",
        {}
    )

    company_data = data.get(
        company,
        {}
    )

    block = company_data.get(
        "FY2024_to_FY2025",
        {}
    )

    return block.get(
        metric,
        {}
    )


def cagr_for(
    company,
    metric
):

    data = quant.get(
        "cagr_analysis",
        {}
    )

    company_data = data.get(
        company,
        {}
    )

    metrics = company_data.get(
        "metrics",
        {}
    )

    return metrics.get(
        metric,
        {}
    )


def cross_company_for(
    year,
    metric
):

    data = quant.get(
        "cross_company_analysis",
        {}
    )

    return (
        data
        .get(year, {})
        .get(metric, {})
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

@st.cache_resource
def get_research_client():

    load_dotenv()

    api_key = os.getenv(
        "GOOGLE_API_KEY"
    )

    if not api_key:

        return None

    return genai.Client(
        api_key=api_key
    )


research_client = (
    get_research_client()
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
    <div class="trust-header">

        <div class="trust-title">
            📊 TrustRAG
        </div>

        <div class="trust-subtitle">
            Corporate Intelligence & Benchmarking Platform
        </div>

        <span class="trust-badge">
            FY2024–FY2025
        </span>

        <span class="trust-badge">
            Evidence Grounded
        </span>

        <span class="trust-badge">
            Quantitative + Qualitative + RAG
        </span>

    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
    <div style="
        font-size:1.45rem;
        font-weight:850;
        color:white;
        letter-spacing:-0.4px;
    ">
        TrustRAG
    </div>

    <div style="
        font-size:0.76rem;
        color:#94a3b8;
        margin-top:0.15rem;
        margin-bottom:1.5rem;
    ">
        Corporate Intelligence Platform
    </div>
    """,
    unsafe_allow_html=True,
)


st.sidebar.markdown(
    "### Analysis Controls"
)


available_companies = [

    company

    for company in COMPANIES

    if any(
        record.get("company")
        == company

        for record in records
    )
]


selected_companies = (
    st.sidebar.multiselect(
        "Companies",
        available_companies,
        default=available_companies,
    )
)


if not selected_companies:

    st.warning(
        "Select at least one company from the sidebar."
    )

    st.stop()


selected_year = (
    st.sidebar.selectbox(
        "Fiscal Year",
        YEARS,
        index=1,
    )
)


st.sidebar.markdown("---")


st.sidebar.markdown(
    "### Platform Modules"
)


st.sidebar.markdown(
    "📊 **Quantitative Intelligence**"
)

st.sidebar.caption(
    "KPIs, trends, YoY, CAGR and peer benchmarking."
)


st.sidebar.markdown(
    "🔎 **Qualitative Intelligence**"
)

st.sidebar.caption(
    "Strategy, leadership, ESG and workforce developments."
)


st.sidebar.markdown(
    "🤖 **Research Copilot**"
)

st.sidebar.caption(
    "Evidence-grounded natural-language research."
)


st.sidebar.markdown(
    "📚 **Evidence & Quality**"
)

st.sidebar.caption(
    "Source pages, validation and data coverage."
)


st.sidebar.markdown("---")


st.sidebar.caption(
    "TrustRAG v2.0"
)

st.sidebar.caption(
    "Annual-report intelligence engine"
)


# ============================================================
# EXECUTIVE SNAPSHOT
# ============================================================

st.markdown(
    '<div class="section-kicker">EXECUTIVE VIEW</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-title">'
    'Corporate Snapshot'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="section-description">'
    f'Peer-level view of validated financial and workforce indicators for '
    f'<b>{selected_year}</b>.'
    f'</div>',
    unsafe_allow_html=True,
)


company_cols = st.columns(
    len(selected_companies)
)


for col, company in zip(
    company_cols,
    selected_companies
):

    record = get_record(
        company,
        selected_year
    )

    revenue = metric_value(
        record,
        "revenue"
    )

    growth = metric_value(
        record,
        "revenue_growth"
    )

    margin = metric_value(
        record,
        "operating_margin"
    )

    pat = metric_value(
        record,
        "pat"
    )

    employees = metric_value(
        record,
        "employees"
    )

    attrition = metric_value(
        record,
        "attrition"
    )

    with col:

        st.markdown(
            f"""
            <div class="company-card">

                <div class="company-name">
                    {company}
                </div>

                <div class="company-year">
                    {selected_year} • Validated dataset
                </div>

                <div class="company-stat-label">
                    Revenue
                </div>

                <div class="company-stat-value">
                    {fmt_value(revenue, "revenue")}
                </div>

                <div style="
                    display:grid;
                    grid-template-columns:1fr 1fr;
                    column-gap:1rem;
                ">

                    <div>

                        <div class="company-stat-label">
                            Revenue Growth
                        </div>

                        <div class="company-stat-value">
                            {fmt_value(growth, "revenue_growth")}
                        </div>

                    </div>

                    <div>

                        <div class="company-stat-label">
                            Operating Margin
                        </div>

                        <div class="company-stat-value">
                            {fmt_value(margin, "operating_margin")}
                        </div>

                    </div>

                    <div>

                        <div class="company-stat-label">
                            PAT
                        </div>

                        <div class="company-stat-value">
                            {fmt_value(pat, "pat")}
                        </div>

                    </div>

                    <div>

                        <div class="company-stat-label">
                            Employees
                        </div>

                        <div class="company-stat-value">
                            {fmt_value(employees, "employees")}
                        </div>

                    </div>

                </div>

                <div class="company-stat-label">
                    Attrition
                </div>

                <div class="company-stat-value">
                    {fmt_value(attrition, "attrition")}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# MAIN TABS
# ============================================================

(
    tab_overview,
    tab_quant,
    tab_qual,
    tab_copilot,
    tab_evidence,
) = st.tabs(
    [
        "🏠 Overview",
        "📊 Quantitative Intelligence",
        "🔎 Qualitative Intelligence",
        "🤖 Research Copilot",
        "📚 Evidence & Quality",
    ]
)


# ============================================================
# OVERVIEW
# ============================================================

with tab_overview:

    st.markdown(
        '<div class="section-kicker">BENCHMARKING</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Peer Benchmark'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Compare selected companies on a common KPI basis.'
        '</div>',
        unsafe_allow_html=True,
    )


    overview_metric = st.selectbox(

        "Benchmark metric",

        list(
            METRIC_LABELS.keys()
        ),

        format_func=lambda x:
            METRIC_LABELS[x],

        key="overview_metric",
    )


    rows = []


    for company in selected_companies:

        record = get_record(
            company,
            selected_year
        )

        rows.append(
            {
                "Company":
                    company,

                METRIC_LABELS[
                    overview_metric
                ]:
                    metric_value(
                        record,
                        overview_metric
                    ),
            }
        )


    overview_df = pd.DataFrame(
        rows
    )


    chart_col, table_col = st.columns(
        [1.45, 1]
    )


    with chart_col:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True,
        )

        if (
            not overview_df.empty
            and
            overview_df.iloc[:, 1]
            .notna()
            .any()
        ):

            chart_df = (
                overview_df
                .set_index("Company")
            )

            st.bar_chart(
                chart_df,
                height=320,
            )

        else:

            st.info(
                "No chartable data available."
            )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )


    with table_col:

        st.markdown(
            '<div class="content-card">',
            unsafe_allow_html=True,
        )

        st.dataframe(
            overview_df,
            use_container_width=True,
            hide_index=True,
            height=320,
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )


    # ========================================================
    # REVENUE TREND
    # ========================================================

    st.markdown(
        '<div class="section-kicker">PERFORMANCE TREND</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Revenue Trajectory'
        '</div>',
        unsafe_allow_html=True,
    )


    trend_rows = []


    for company in selected_companies:

        for year in YEARS:

            record = get_record(
                company,
                year
            )

            value = metric_value(
                record,
                "revenue"
            )

            if value is not None:

                trend_rows.append(
                    {
                        "Company":
                            company,

                        "Fiscal Year":
                            year,

                        "Revenue":
                            value,
                    }
                )


    trend_df = pd.DataFrame(
        trend_rows
    )


    if not trend_df.empty:

        trend_pivot = (
            trend_df
            .pivot(
                index="Fiscal Year",
                columns="Company",
                values="Revenue",
            )
        )

        st.line_chart(
            trend_pivot,
            height=350,
        )


    # ========================================================
    # YOY SUMMARY
    # ========================================================

    st.markdown(
        '<div class="section-kicker">YEAR-OVER-YEAR</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'FY2024 → FY2025 Change'
        '</div>',
        unsafe_allow_html=True,
    )


    yoy_rows = []


    for company in selected_companies:

        yoy = yoy_for(
            company,
            "revenue"
        )

        yoy_rows.append(
            {
                "Company":
                    company,

                "FY2024 Revenue":
                    yoy.get(
                        "previous_value"
                    ),

                "FY2025 Revenue":
                    yoy.get(
                        "current_value"
                    ),

                "Absolute Change (₹ Cr)":
                    yoy.get(
                        "absolute_change"
                    ),

                "Percentage Change (%)":
                    yoy.get(
                        "percentage_change"
                    ),
            }
        )


    st.dataframe(
        pd.DataFrame(
            yoy_rows
        ),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# QUANTITATIVE INTELLIGENCE
# ============================================================

with tab_quant:

    st.markdown(
        '<div class="section-kicker">PILLAR 01</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Quantitative Intelligence'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Deterministic financial analysis across companies and fiscal years.'
        '</div>',
        unsafe_allow_html=True,
    )


    metric = st.selectbox(

        "Select KPI",

        list(
            METRIC_LABELS.keys()
        ),

        format_func=lambda x:
            METRIC_LABELS[x],

        key="quant_metric",
    )


    # ========================================================
    # KPI SUMMARY
    # ========================================================

    st.markdown(
        "### Selected KPI"
    )


    kpi_cols = st.columns(
        len(selected_companies)
    )


    for col, company in zip(
        kpi_cols,
        selected_companies
    ):

        record = get_record(
            company,
            selected_year
        )

        value = metric_value(
            record,
            metric
        )

        with col:

            st.markdown(
                f"""
                <div class="metric-card">

                    <div class="metric-label">
                        {company}
                    </div>

                    <div class="metric-value">
                        {fmt_value(value, metric)}
                    </div>

                    <div class="metric-sub">
                        {METRIC_LABELS[metric]}
                        • {selected_year}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


    st.markdown("<br>", unsafe_allow_html=True)


    # ========================================================
    # YEAR BY YEAR
    # ========================================================

    st.markdown(
        "### Year-by-Year Analysis"
    )


    year_rows = []


    for company in selected_companies:

        for year in YEARS:

            record = get_record(
                company,
                year
            )

            value = metric_value(
                record,
                metric
            )

            year_rows.append(
                {
                    "Company":
                        company,

                    "Fiscal Year":
                        year,

                    METRIC_LABELS[
                        metric
                    ]:
                        value,
                }
            )


    year_df = pd.DataFrame(
        year_rows
    )


    chart_col, table_col = st.columns(
        [1.45, 1]
    )


    with chart_col:

        chart_df = (
            year_df
            .pivot(
                index="Fiscal Year",
                columns="Company",
                values=METRIC_LABELS[
                    metric
                ],
            )
        )

        if chart_df.notna().any().any():

            st.line_chart(
                chart_df,
                height=350,
            )


    with table_col:

        st.dataframe(
            year_df,
            use_container_width=True,
            hide_index=True,
            height=350,
        )


    # ========================================================
    # YOY
    # ========================================================

    st.markdown(
        "### FY2024 → FY2025 YoY Analysis"
    )


    yoy_rows = []


    for company in selected_companies:

        yoy = yoy_for(
            company,
            metric
        )


        row = {

            "Company":
                company,

            "Previous":
                yoy.get(
                    "previous_value"
                ),

            "Current":
                yoy.get(
                    "current_value"
                ),

            "Absolute Change":
                yoy.get(
                    "absolute_change"
                ),
        }


        if metric in RATE_METRICS:

            row[
                "Percentage-Point Change"
            ] = yoy.get(
                "absolute_change"
            )

        else:

            row[
                "Percentage Change (%)"
            ] = yoy.get(
                "percentage_change"
            )


        yoy_rows.append(
            row
        )


    st.dataframe(
        pd.DataFrame(
            yoy_rows
        ),
        use_container_width=True,
        hide_index=True,
    )


    # ========================================================
    # CAGR
    # ========================================================

    st.markdown(
        "### FY2024 → FY2025 Long-Term Change"
    )


    cagr_rows = []


    for company in selected_companies:

        cagr = cagr_for(
            company,
            metric
        )


        cagr_rows.append(
            {

                "Company":
                    company,

                "Start Value":
                    cagr.get(
                        "start_value"
                    ),

                "End Value":
                    cagr.get(
                        "end_value"
                    ),

                "CAGR (%)":
                    cagr.get(
                        "cagr_percent"
                    ),

                "Change (pp)":
                    cagr.get(
                        "change_percentage_points"
                    ),

            }
        )


    st.dataframe(
        pd.DataFrame(
            cagr_rows
        ),
        use_container_width=True,
        hide_index=True,
    )


    # ========================================================
    # PEER BENCHMARK
    # ========================================================

    st.markdown(
        "### Peer Benchmark"
    )


    cross = cross_company_for(
        selected_year,
        metric
    )


    benchmark_rows = []


    for company in selected_companies:

        benchmark_rows.append(
            {
                "Company":
                    company,

                METRIC_LABELS[
                    metric
                ]:
                    cross.get(
                        company
                    ),
            }
        )


    benchmark_df = pd.DataFrame(
        benchmark_rows
    )


    chart_col, table_col = st.columns(
        [1.45, 1]
    )


    with chart_col:

        if not benchmark_df.empty:

            st.bar_chart(
                benchmark_df.set_index(
                    "Company"
                ),
                height=320,
            )


    with table_col:

        st.dataframe(
            benchmark_df,
            use_container_width=True,
            hide_index=True,
            height=320,
        )


    # ========================================================
    # CAVEAT
    # ========================================================

    st.info(
        "Comparisons should be interpreted together with "
        "TrustRAG's comparability notes. Definitions such as "
        "operating margin, ROE, attrition, cash/liquid assets "
        "and FCF may differ across companies."
    )


# ============================================================
# QUALITATIVE INTELLIGENCE
# ============================================================

with tab_qual:

    st.markdown(
        '<div class="section-kicker">PILLAR 02</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Qualitative Corporate Intelligence'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Evidence-backed developments extracted from annual reports.'
        '</div>',
        unsafe_allow_html=True,
    )


    qual_company = st.selectbox(

        "Company",

        selected_companies,

        key="qual_company",
    )


    qual_year = st.selectbox(

        "Fiscal Year",

        YEARS,

        index=1,

        key="qual_year",
    )


    qrecord = get_qual_record(
        qual_company,
        qual_year,
    )


    if not qrecord:

        st.warning(
            "No qualitative analysis record was found "
            "for this company-year."
        )

    else:

        source_documents = qrecord.get(
            "source_documents",
            []
        )


        evidence_chunks = qrecord.get(
            "evidence_chunks_used",
            "N/A"
        )


        top1, top2 = st.columns(2)


        with top1:

            st.markdown(
                f"""
                <div class="metric-card">

                    <div class="metric-label">
                        SOURCE DOCUMENTS
                    </div>

                    <div class="metric-value"
                         style="font-size:1.15rem;">

                        {len(source_documents)}

                    </div>

                    <div class="metric-sub">
                        Annual-report sources
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


        with top2:

            st.markdown(
                f"""
                <div class="metric-card">

                    <div class="metric-label">
                        EVIDENCE CHUNKS
                    </div>

                    <div class="metric-value"
                         style="font-size:1.15rem;">

                        {evidence_chunks}

                    </div>

                    <div class="metric-sub">
                        Retrieval context used
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


        if source_documents:

            st.caption(
                "Sources: "
                +
                ", ".join(
                    source_documents
                )
            )


        st.markdown("<br>", unsafe_allow_html=True)


        qtabs = st.tabs(
            list(
                QUAL_CATEGORIES.values()
            )
        )


        for tab, (
            category,
            label
        ) in zip(
            qtabs,
            QUAL_CATEGORIES.items()
        ):

            with tab:

                findings = qrecord.get(
                    category,
                    []
                )


                if not findings:

                    st.info(
                        "No supported finding was extracted "
                        "for this category."
                    )


                for i, finding in enumerate(
                    findings,
                    1
                ):

                    finding_text = (
                        finding.get(
                            "finding",
                            "N/A"
                        )
                    )


                    source_page = (
                        finding.get(
                            "source_page",
                            "N/A"
                        )
                    )


                    evidence = (
                        finding.get(
                            "evidence",
                            ""
                        )
                    )


                    st.markdown(
                        f"""
                        <div class="insight-card">

                            <div class="insight-title">
                                {i}. {finding_text}
                            </div>

                            <span class="source-tag">
                                Annual Report • Page {source_page}
                            </span>

                            <div class="evidence-box">
                                <b>Evidence</b><br>
                                {evidence}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


        # ====================================================
        # QUALITATIVE COVERAGE
        # ====================================================

        st.markdown(
            "### Intelligence Coverage"
        )


        coverage = []


        for category, label in QUAL_CATEGORIES.items():

            coverage.append(
                {
                    "Category":
                        label,

                    "Supported Findings":
                        len(
                            qrecord.get(
                                category,
                                []
                            )
                        ),
                }
            )


        st.dataframe(
            pd.DataFrame(
                coverage
            ),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# RESEARCH COPILOT
# ============================================================

with tab_copilot:

    st.markdown(
        '<div class="section-kicker">PILLAR 03</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Research Copilot'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Ask evidence-grounded corporate research questions across '
        'financial and qualitative data.'
        '</div>',
        unsafe_allow_html=True,
    )


    copilot_companies = st.multiselect(

        "Research scope — companies",

        available_companies,

        default=selected_companies,

        key="copilot_companies",
    )


    copilot_years = st.multiselect(

        "Research scope — fiscal years",

        YEARS,

        default=YEARS,

        key="copilot_years",
    )


    question = st.text_area(

        "Research question",

        placeholder=(
            "Example: Compare the revenue growth, operating "
            "margin and workforce developments of TCS, Infosys "
            "and HCLTech between FY2024 and FY2025."
        ),

        height=125,

        key="copilot_question",
    )


    analyze = st.button(
        "🔍 Analyze with TrustRAG",
        type="primary",
        use_container_width=True,
        key="copilot_analyze",
    )


    # ========================================================
    # CONTEXT BUILDER
    # ========================================================

    def build_copilot_context():

        parts = []


        # ----------------------------------------------------
        # QUANTITATIVE
        # ----------------------------------------------------

        parts.append(
            "===== VALIDATED QUANTITATIVE DATA ====="
        )


        for company in copilot_companies:

            for year in copilot_years:

                record = get_record(
                    company,
                    year
                )


                if not record:
                    continue


                parts.append(
                    f"\n--- {company} | {year} ---"
                )


                for metric_name in METRIC_LABELS:

                    obj = metric_obj(
                        record,
                        metric_name
                    )


                    value = obj.get(
                        "value"
                    )


                    if value is None:
                        continue


                    parts.append(
                        f"{METRIC_LABELS[metric_name]}: "
                        f"{value}"
                    )


        # ----------------------------------------------------
        # QUALITATIVE
        # ----------------------------------------------------

        parts.append(
            "\n===== QUALITATIVE INTELLIGENCE ====="
        )


        for company in copilot_companies:

            for year in copilot_years:

                q = get_qual_record(
                    company,
                    year
                )


                if not q:
                    continue


                parts.append(
                    f"\n--- {company} | {year} ---"
                )


                for (
                    category,
                    label
                ) in QUAL_CATEGORIES.items():

                    findings = q.get(
                        category,
                        []
                    )


                    for finding in findings:

                        parts.append(
                            f"{label}: "
                            f"{finding.get('finding')}; "
                            f"Page: "
                            f"{finding.get('source_page')}; "
                            f"Evidence: "
                            f"{finding.get('evidence')}"
                        )


        # ----------------------------------------------------
        # RAG EVIDENCE
        # ----------------------------------------------------

        parts.append(
            "\n===== RETRIEVED ANNUAL-REPORT EVIDENCE ====="
        )


        if question.strip():

            for company in copilot_companies:

                for year in copilot_years:

                    try:

                        chunks = retrieve(

                            question,

                            k=4,

                            company=company,

                            fiscal_year=year,

                        )

                    except Exception:

                        chunks = []


                    for chunk in chunks:

                        source = Path(
                            chunk[
                                "source_document"
                            ]
                        ).stem


                        parts.append(
                            f"\n[{company}, "
                            f"{year}, "
                            f"{source}, "
                            f"p.{chunk['page']}]\n"
                            f"{chunk['text']}"
                        )


        return "\n".join(
            parts
        )


    # ========================================================
    # RUN COPILOT
    # ========================================================

    if analyze:

        if not question.strip():

            st.warning(
                "Enter a research question first."
            )

        elif not copilot_companies:

            st.warning(
                "Select at least one company."
            )

        elif not copilot_years:

            st.warning(
                "Select at least one fiscal year."
            )

        elif research_client is None:

            st.error(
                "GOOGLE_API_KEY was not found. "
                "Check your .env file."
            )

        else:

            with st.spinner(
                "Retrieving annual-report evidence..."
            ):

                try:

                    context = (
                        build_copilot_context()
                    )


                    prompt = f"""
You are TrustRAG, an evidence-grounded corporate research copilot.

USER QUESTION:
{question}

SOURCE CONTEXT:
{context}

RULES:

1. Use ONLY the supplied context.

2. Do not use outside knowledge.

3. Never invent a number, event, person, date or source.

4. If evidence is insufficient, explicitly say:

"The available TrustRAG evidence is insufficient to answer this."

5. Distinguish reported values from derived calculations.

6. For qualitative claims, cite:

[Company, FY202X, p.X]

7. For quantitative claims, cite:

[Company, FY202X]

8. Mention relevant comparability caveats.

9. Do not create unsupported conclusions from missing data.

10. Do not turn a reported change into a causal claim unless the supplied evidence explicitly states the cause.

11. Keep the response concise and business-oriented.

12. Use bullets and small tables where useful.

13. Clearly distinguish annual-report evidence from deterministic calculations.

Return a professional corporate research answer.
"""


                    with st.spinner(
                        "Generating evidence-grounded analysis..."
                    ):

                        response = (
                            research_client
                            .models
                            .generate_content(

                                model=RESEARCH_MODEL,

                                contents=prompt,

                                config=(
                                    types
                                    .GenerateContentConfig(
                                        temperature=0.1,
                                    )
                                ),
                            )
                        )


                    st.markdown(
                        "### Research Output"
                    )


                    st.markdown(
                        response.text
                    )


                except Exception as exc:

                    st.error(
                        f"Research request failed: {exc}"
                    )


# ============================================================
# EVIDENCE & QUALITY
# ============================================================

with tab_evidence:

    st.markdown(
        '<div class="section-kicker">AUDITABILITY</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Evidence & Data Quality'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-description">'
        'Trace reported KPIs back to their annual-report evidence '
        'and inspect dataset coverage.'
        '</div>',
        unsafe_allow_html=True,
    )


    evidence_company = st.selectbox(

        "Company",

        selected_companies,

        key="evidence_company",
    )


    evidence_year = st.selectbox(

        "Fiscal Year",

        YEARS,

        index=1,

        key="evidence_year",
    )


    evidence_record = get_record(
        evidence_company,
        evidence_year,
    )


    evidence_metric = st.selectbox(

        "KPI",

        list(
            METRIC_LABELS.keys()
        ),

        format_func=lambda x:
            METRIC_LABELS[x],

        key="evidence_metric",
    )


    obj = metric_obj(
        evidence_record,
        evidence_metric
    )


    # ========================================================
    # EVIDENCE KPI CARDS
    # ========================================================

    c1, c2, c3 = st.columns(3)


    with c1:

        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    VALUE
                </div>

                <div class="metric-value">
                    {fmt_value(
                        obj.get("value"),
                        evidence_metric
                    )}
                </div>

                <div class="metric-sub">
                    {METRIC_LABELS[evidence_metric]}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with c2:

        status = obj.get(
            "status",
            "N/A"
        )


        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    VALIDATION STATUS
                </div>

                <div class="metric-value"
                     style="font-size:1.25rem;">

                    {status}

                </div>

                <div class="metric-sub">
                    TrustRAG validation layer
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with c3:

        page = obj.get(
            "source_page",
            "N/A"
        )


        st.markdown(
            f"""
            <div class="metric-card">

                <div class="metric-label">
                    SOURCE PAGE
                </div>

                <div class="metric-value"
                     style="font-size:1.4rem;">

                    {page}

                </div>

                <div class="metric-sub">
                    Annual report evidence
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # ========================================================
    # REPORTED LABEL
    # ========================================================

    if obj.get(
        "reported_label"
    ):

        st.markdown(
            f"""
            <div class="insight-card">

                <div class="insight-title">
                    Reported Label
                </div>

                <div class="insight-text">
                    {obj["reported_label"]}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # ========================================================
    # EVIDENCE
    # ========================================================

    if obj.get(
        "evidence"
    ):

        st.markdown(
            "### Source Evidence"
        )

        st.markdown(
            f"""
            <div class="evidence-box">

                <b>Annual Report Evidence</b>
                <br><br>

                {obj["evidence"]}

            </div>
            """,
            unsafe_allow_html=True,
        )


    if obj.get(
        "notes"
    ):

        st.markdown(
            "### Notes"
        )

        st.info(
            obj["notes"]
        )


    st.divider()


    # ========================================================
    # COMPARABILITY
    # ========================================================

    st.markdown(
        "### Comparability"
    )


    comparability = quant.get(
        "comparability",
        {}
    )


    if isinstance(
        comparability,
        dict
    ):

        company_comp = comparability.get(
            evidence_company,
            {}
        )

    else:

        company_comp = {}


    if isinstance(
        company_comp,
        dict
    ):

        comp_details = company_comp.get(
            evidence_metric,
            {}
        )

    else:

        comp_details = {}


    if comp_details:

        level = comp_details.get(
            "level",
            "N/A"
        )


        reason = comp_details.get(
            "reason",
            ""
        )


        st.markdown(
            f"""
            <div class="insight-card">

                <div class="insight-title">
                    Comparability Level: {level}
                </div>

                <div class="insight-text">
                    {reason}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

    else:

        st.info(
            "No additional comparability note is available "
            "for this KPI/company combination."
        )


    st.divider()


    # ========================================================
    # DATA COVERAGE
    # ========================================================

    st.markdown(
        "### Dataset Coverage"
    )


    coverage_rows = []


    for company in available_companies:

        for year in YEARS:

            record = get_record(
                company,
                year
            )


            reported = 0


            total = len(
                METRIC_LABELS
            )


            for metric_name in METRIC_LABELS:

                obj2 = metric_obj(
                    record,
                    metric_name
                )


                if obj2.get(
                    "value"
                ) is not None:

                    reported += 1


            coverage_rows.append(
                {
                    "Company":
                        company,

                    "Fiscal Year":
                        year,

                    "Available Metrics":
                        reported,

                    "Total Metrics":
                        total,

                    "Coverage (%)":
                        round(
                            reported
                            /
                            total
                            *
                            100,
                            1
                        ),
                }
            )


    coverage_df = pd.DataFrame(
        coverage_rows
    )


    st.dataframe(
        coverage_df,
        use_container_width=True,
        hide_index=True,
    )


    # ========================================================
    # COVERAGE CHART
    # ========================================================

    if not coverage_df.empty:

        coverage_chart = (
            coverage_df
            .assign(
                Period=lambda x:
                x["Company"]
                + " "
                + x["Fiscal Year"]
            )
            .set_index(
                "Period"
            )[
                ["Coverage (%)"]
            ]
        )


        st.bar_chart(
            coverage_chart,
            height=300,
        )


    st.divider()


    # ========================================================
    # EXCEL OUTPUT
    # ========================================================

    st.markdown(
        "### Research Output"
    )


    if EXCEL_FILE.exists():

        with open(
            EXCEL_FILE,
            "rb"
        ) as f:

            excel_bytes = f.read()


        st.download_button(

            "📥 Download TrustRAG Benchmarking Report",

            data=excel_bytes,

            file_name=(
                "TrustRAG_Benchmarking_Report.xlsx"
            ),

            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),

            use_container_width=True,
        )

    else:

        st.info(
            "Excel benchmarking report not found."
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="trust-footer">

        TrustRAG • Corporate Intelligence & Benchmarking
        <br>
        Evidence-grounded quantitative analysis •
        qualitative intelligence • research copilot

    </div>
    """,
    unsafe_allow_html=True,
)