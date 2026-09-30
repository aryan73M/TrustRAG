import json
import os
from pathlib import Path
from textwrap import dedent

import pandas as pd
import streamlit as st
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="TrustRAG | Corporate Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


DATA_DIR = Path("data")

QUANT_FILE = DATA_DIR / "quantitative_analysis.json"

# Raw KPI files used to build the multi-year dataset
FY2024_FILE = DATA_DIR / "calculated_kpis.json"
FY2025_FILE = DATA_DIR / "calculated_kpis_FY2025.json"

QUAL_FILE = DATA_DIR / "qualitative_analysis.json"
EXCEL_FILE = DATA_DIR / "TrustRAG_Benchmarking_Report.xlsx"

COMPANIES = [
    "TCS",
    "Infosys",
    "HCLTech",
]

YEARS = [
    "FY2024",
    "FY2025",
]

METRICS = {
    "revenue": "Revenue",
    "revenue_growth": "Revenue Growth",
    "operating_margin": "Operating Margin",
    "pat": "PAT",
    "pat_margin": "PAT Margin",
    "eps": "EPS",
    "roe": "ROE",
    "free_cash_flow": "Reported FCF",
    "standardized_fcf": "Standardized FCF",
    "capex": "Capex",
    "operating_cash_flow": "Operating Cash Flow",
    "cash_liquid_assets": "Cash / Liquid Assets",
    "employees": "Employees",
    "attrition": "Attrition",
    "revenue_per_employee": "Revenue / Employee",
    "employee_growth": "Employee Growth",
    "fcf_margin": "FCF Margin",
}

RATE_METRICS = {
    "revenue_growth",
    "operating_margin",
    "pat_margin",
    "roe",
    "attrition",
    "employee_growth",
    "fcf_margin",
}

QUAL_CATEGORIES = {
    "strategic_changes": (
        "Strategy & Business"
    ),
    "management_changes": (
        "Management & Leadership"
    ),
    "sustainability_esg": (
        "Sustainability & ESG"
    ),
    "workforce_developments": (
        "Workforce & Organization"
    ),
}

load_dotenv()


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    dedent(
        """
        <style>

        /* ==================================================
           GLOBAL
        ================================================== */

        .block-container {
            max-width: 1450px;
            padding-top: 1.2rem;
            padding-bottom: 2.5rem;
        }

        [data-testid="stAppViewContainer"] {
            background:
                linear-gradient(
                    180deg,
                    #f8fafc 0%,
                    #ffffff 35%
                );
        }

        h1, h2, h3 {
            letter-spacing: -0.025em;
        }

        /* ==================================================
           HEADER
        ================================================== */

        .hero {
            background:
                linear-gradient(
                    135deg,
                    #0f172a 0%,
                    #172554 55%,
                    #1e3a8a 100%
                );

            padding: 2rem 2.2rem;
            border-radius: 20px;
            margin-bottom: 1.4rem;

            box-shadow:
                0 12px 35px
                rgba(15, 23, 42, 0.18);

            color: white;
        }

        .hero-title {
            font-size: 2.45rem;
            font-weight: 850;
            line-height: 1.05;
            margin-bottom: 0.35rem;
        }

        .hero-subtitle {
            font-size: 1rem;
            color: #cbd5e1;
            margin-bottom: 1rem;
        }

        .pill {
            display: inline-block;
            padding: 0.38rem 0.7rem;
            margin-right: 0.4rem;
            margin-top: 0.25rem;

            border-radius: 999px;

            background:
                rgba(255, 255, 255, 0.10);

            border:
                1px solid
                rgba(255, 255, 255, 0.14);

            color: #e2e8f0;

            font-size: 0.75rem;
            font-weight: 700;
        }

        /* ==================================================
           SECTION HEADERS
        ================================================== */

        .section-title {
            font-size: 1.35rem;
            font-weight: 800;
            color: #0f172a;
            margin-top: 0.4rem;
            margin-bottom: 0.2rem;
        }

        .section-subtitle {
            color: #64748b;
            font-size: 0.88rem;
            margin-bottom: 1rem;
        }

        /* ==================================================
           KPI CARDS
        ================================================== */

        .kpi-card {
            background: white;

            border:
                1px solid
                #e2e8f0;

            border-radius: 16px;

            padding:
                1rem 1.1rem;

            min-height: 120px;

            box-shadow:
                0 5px 18px
                rgba(15, 23, 42, 0.055);

            margin-bottom: 0.8rem;
        }

        .kpi-label {
            color: #64748b;

            font-size: 0.73rem;

            font-weight: 800;

            text-transform:
                uppercase;

            letter-spacing:
                0.06em;
        }

        .kpi-company {
            color: #94a3b8;
            font-size: 0.72rem;
            margin-top: 0.35rem;
        }

        .kpi-value {
            color: #0f172a;

            font-size: 1.5rem;

            font-weight: 850;

            margin-top: 0.35rem;
        }

        /* ==================================================
           COMPANY CARDS
        ================================================== */

        .company-card {
            background: white;

            border:
                1px solid
                #e2e8f0;

            border-radius: 16px;

            padding: 1.1rem;

            box-shadow:
                0 5px 18px
                rgba(15, 23, 42, 0.05);
        }

        .company-name {
            font-size: 1.05rem;
            font-weight: 800;
            color: #0f172a;
        }

        .company-meta {
            color: #64748b;
            font-size: 0.78rem;
            margin-top: 0.2rem;
        }

        /* ==================================================
           INSIGHT CARDS
        ================================================== */

        .insight {
            background: white;

            border:
                1px solid
                #e2e8f0;

            border-radius: 14px;

            padding:
                1rem 1.1rem;

            margin:
                0.55rem 0;

            box-shadow:
                0 4px 15px
                rgba(15, 23, 42, 0.045);
        }

        .insight-title {
            font-weight: 750;
            color: #0f172a;
            margin-bottom: 0.25rem;
        }

        .insight-source {
            color: #64748b;
            font-size: 0.75rem;
        }

        /* ==================================================
           EVIDENCE
        ================================================== */

        .evidence {
            background: #f8fafc;

            border-left:
                4px solid
                #2563eb;

            border-radius:
                0 10px 10px 0;

            padding:
                0.85rem 1rem;

            margin-top:
                0.65rem;

            color: #334155;

            font-size: 0.88rem;
        }

        /* ==================================================
           MODULE CARDS
        ================================================== */

        .module-card {
            background: white;

            border:
                1px solid
                #e2e8f0;

            border-radius: 18px;

            padding: 1.3rem;

            min-height: 155px;

            box-shadow:
                0 7px 22px
                rgba(15, 23, 42, 0.055);
        }

        .module-icon {
            font-size: 1.65rem;
        }

        .module-title {
            font-weight: 800;
            font-size: 1rem;
            margin-top: 0.4rem;
        }

        .module-text {
            color: #64748b;
            font-size: 0.82rem;
            line-height: 1.45;
            margin-top: 0.35rem;
        }

        /* ==================================================
           CHAT
        ================================================== */

        .chat-context {
            background:
                #eff6ff;

            border:
                1px solid
                #bfdbfe;

            border-radius:
                12px;

            padding:
                0.8rem 1rem;

            color:
                #1e3a8a;

            font-size:
                0.82rem;
        }

        /* ==================================================
           SIDEBAR
        ================================================== */

        section[data-testid="stSidebar"] {
            background:
                #0f172a;
        }

        section[data-testid="stSidebar"] * {
            color: #e2e8f0;
        }

        section[data-testid="stSidebar"]
        div[data-baseweb="select"] > div {
            background: #1e293b;
            border-color: #334155;
        }

        /* ==================================================
           TABLE
        ================================================== */

        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
        }

        </style>
        """
    ),
    unsafe_allow_html=True,
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_json(path):

    if not path.exists():
        return {}

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            return json.load(file)

    except Exception:

        return {}


quant = load_json(
    QUANT_FILE
)

fy2024_data = load_json(
    FY2024_FILE
)

fy2025_data = load_json(
    FY2025_FILE
)

qual = load_json(
    QUAL_FILE
)


# ============================================================
# NORMALIZE RECORDS
# ============================================================

def records_from(
    data,
    keys=(
        "company_year_data",
        "company_year_analysis",
        "records",
        "data",
    ),
):

    if isinstance(
        data,
        list,
    ):

        return [
            x
            for x in data
            if isinstance(x, dict)
        ]

    if isinstance(
        data,
        dict,
    ):

        for key in keys:

            candidate = data.get(
                key
            )

            if isinstance(
                candidate,
                list,
            ):

                return [
                    x
                    for x in candidate
                    if isinstance(x, dict)
                ]

    return []


# ============================================================
# BUILD COMPANY-YEAR RECORDS DIRECTLY FROM KPI FILES
# ============================================================

def normalize_kpi_records(
    data,
    fiscal_year,
):

    raw_records = records_from(
        data
    )

    normalized = []

    for item in raw_records:

        item = dict(item)

        item["fiscal_year"] = fiscal_year

        normalized.append(
            item
        )

    return normalized


records = (
    normalize_kpi_records(
        fy2024_data,
        "FY2024",
    )
    +
    normalize_kpi_records(
        fy2025_data,
        "FY2025",
    )
)

qual_records = records_from(
    qual
)


# ============================================================
# HELPERS
# ============================================================

def record(
    company,
    year,
):

    for item in records:

        if (
            item.get("company") == company
            and item.get("fiscal_year") == year
        ):

            return item

    return None


def qrecord(
    company,
    year,
):

    return next(
        (
            item
            for item in qual_records
            if item.get("company")
            == company
            and item.get("fiscal_year")
            == year
        ),
        None,
    )


def obj(
    data,
    metric,
):

    if not data:
        return {}

    value = data.get(
        metric
    )

    if isinstance(
        value,
        dict,
    ):

        return value

    return {
        "value": value
    }


def numeric_value(
    data,
    metric,
):

    item = obj(
        data,
        metric,
    )

    value = item.get(
        "value"
    )

    if isinstance(
        value,
        bool,
    ):

        return None

    if isinstance(
        value,
        (int, float),
    ):

        return value

    return None


def fmt(
    value,
    metric,
):

    if value is None:

        return "N/A"

    try:

        if metric in RATE_METRICS:

            return f"{value:.1f}%"

        if metric == "eps":

            return f"₹{value:,.2f}"

        if metric == "employees":

            return f"{value:,.0f}"

        if metric == "revenue_per_employee":

            return f"{value:.3f}"

        if metric in {
            "revenue",
            "pat",
            "free_cash_flow",
            "standardized_fcf",
            "capex",
            "operating_cash_flow",
            "cash_liquid_assets",
        }:

            return f"₹{value:,.0f} Cr"

        return f"{value:,.2f}"

    except Exception:

        return str(value)


def yoy_data(
    company,
    metric,
):

    return (
        quant
        .get(
            "yoy_analysis",
            {}
        )
        .get(
            company,
            {}
        )
        .get(
            "FY2024_to_FY2025",
            {}
        )
        .get(
            metric,
            {}
        )
    )


def cagr_data(
    company,
    metric,
):

    return (
        quant
        .get(
            "cagr_analysis",
            {}
        )
        .get(
            company,
            {}
        )
        .get(
            "metrics",
            {}
        )
        .get(
            metric,
            {}
        )
    )


def cross_data(
    year,
    metric,
):

    return (
        quant
        .get(
            "cross_company_analysis",
            {}
        )
        .get(
            year,
            {}
        )
        .get(
            metric,
            {}
        )
    )


# ============================================================
# AVAILABLE COMPANIES
# ============================================================

available_companies = [
    company
    for company in COMPANIES
    if any(
        item.get("company")
        == company
        for item in records
    )
]


# ============================================================
# HEADER
# ============================================================

# ============================================================
# TRUSTRAG HEADER
# ============================================================

st.html(
    """
    <div style="
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #172554 55%,
            #1e3a8a 100%
        );
        padding: 30px 34px;
        border-radius: 18px;
        margin-bottom: 22px;
        box-shadow: 0 10px 30px rgba(15,23,42,.15);
        color: white;
    ">

        <div style="
            font-size: 38px;
            font-weight: 800;
            margin-bottom: 7px;
        ">
            📊 TrustRAG
        </div>

        <div style="
            font-size: 17px;
            color: #cbd5e1;
            margin-bottom: 18px;
        ">
            Corporate Intelligence & Benchmarking Platform
        </div>

        <div>

            <span style="
                display:inline-block;
                padding:7px 12px;
                margin-right:7px;
                margin-bottom:5px;
                border-radius:20px;
                background:rgba(255,255,255,.10);
                border:1px solid rgba(255,255,255,.15);
                font-size:12px;
                font-weight:600;
            ">
                📈 Quantitative Intelligence
            </span>

            <span style="
                display:inline-block;
                padding:7px 12px;
                margin-right:7px;
                margin-bottom:5px;
                border-radius:20px;
                background:rgba(255,255,255,.10);
                border:1px solid rgba(255,255,255,.15);
                font-size:12px;
                font-weight:600;
            ">
                🔎 Qualitative Intelligence
            </span>

            <span style="
                display:inline-block;
                padding:7px 12px;
                margin-right:7px;
                margin-bottom:5px;
                border-radius:20px;
                background:rgba(255,255,255,.10);
                border:1px solid rgba(255,255,255,.15);
                font-size:12px;
                font-weight:600;
            ">
                🤖 Research Copilot
            </span>

            <span style="
                display:inline-block;
                padding:7px 12px;
                margin-bottom:5px;
                border-radius:20px;
                background:rgba(255,255,255,.10);
                border:1px solid rgba(255,255,255,.15);
                font-size:12px;
                font-weight:600;
            ">
                📚 Evidence Grounded
            </span>

        </div>

    </div>
    """
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "## TrustRAG"
    )

    st.caption(
        "Corporate Intelligence Platform"
    )

    st.divider()

    st.markdown(
        "### Analysis Controls"
    )

    selected_companies = st.multiselect(
        "Companies",
        available_companies,
        default=available_companies,
    )

    if not selected_companies:

        st.warning(
            "Select at least one company."
        )

        st.stop()

    selected_year = st.selectbox(
        "Fiscal Year",
        YEARS,
        index=1,
    )

    st.divider()

    st.markdown(
        "### Platform Modules"
    )

    st.markdown(
        "📈 **Quantitative Intelligence**"
    )

    st.caption(
        "KPIs • Trends • YoY • CAGR • Benchmarking"
    )

    st.markdown(
        "🔎 **Qualitative Intelligence**"
    )

    st.caption(
        "Strategy • Leadership • ESG • Workforce"
    )

    st.markdown(
        "🤖 **Research Copilot**"
    )

    st.caption(
        "Evidence-grounded annual-report research"
    )

    st.markdown(
        "📚 **Evidence Explorer**"
    )

    st.caption(
        "Source pages • Evidence • Data coverage"
    )

    st.divider()

    st.caption(
        "Dataset: FY2024–FY2025"
    )

    st.caption(
        "TCS • Infosys • HCLTech"
    )


# ============================================================
# EXECUTIVE SNAPSHOT
# ============================================================

st.markdown(
    '<div class="section-title">Executive Snapshot</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-subtitle">'
    'Current-year view of the selected companies'
    '</div>',
    unsafe_allow_html=True,
)


snapshot_metrics = [
    (
        "revenue",
        "Revenue",
    ),
    (
        "revenue_growth",
        "Revenue Growth",
    ),
    (
        "operating_margin",
        "Operating Margin",
    ),
    (
        "pat",
        "Profit After Tax",
    ),
    (
        "employees",
        "Employees",
    ),
    (
        "attrition",
        "Attrition",
    ),
]


for start in range(
    0,
    len(snapshot_metrics),
    3,
):

    cols = st.columns(
        3,
        gap="medium",
    )

    for col, (
        metric,
        label,
    ) in zip(
        cols,
        snapshot_metrics[
            start:start + 3
        ],
    ):

        with col:

            company_lines = []

            for company in selected_companies:

                data = record(
                    company,
                    selected_year,
                )

                company_lines.append(
                    (
                        company,
                        fmt(
                            numeric_value(
                                data,
                                metric,
                            ),
                            metric,
                        ),
                    )
                )

            html = (
                '<div class="kpi-card">'
                f'<div class="kpi-label">{label}</div>'
            )

            for company, value_text in company_lines:

                html += (
                    f'<div class="kpi-value">'
                    f'{value_text}'
                    f'</div>'
                    f'<div class="kpi-company">'
                    f'{company} · {selected_year}'
                    f'</div>'
                )

            html += "</div>"

            st.markdown(
                html,
                unsafe_allow_html=True,
            )


st.divider()


# ============================================================
# MAIN TABS
# ============================================================

overview_tab, quantitative_tab, qualitative_tab, copilot_tab, evidence_tab = st.tabs(
    [
        "🏠 Overview",
        "📈 Quantitative",
        "🔎 Qualitative",
        "🤖 Research Copilot",
        "📚 Evidence",
    ]
)


# ============================================================
# OVERVIEW
# ============================================================

with overview_tab:

    st.markdown(
        '<div class="section-title">'
        'Corporate Intelligence Overview'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'A consolidated view of financial performance, '
        'workforce indicators and peer benchmarking.'
        '</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # MODULE CARDS
    # --------------------------------------------------------

    c1, c2, c3 = st.columns(
        3,
        gap="medium",
    )

    with c1:

        st.markdown(
            """
            <div class="module-card">
                <div class="module-icon">📈</div>
                <div class="module-title">
                    Quantitative Intelligence
                </div>
                <div class="module-text">
                    Compare revenue, margins, PAT,
                    EPS, ROE, cash flow and workforce
                    metrics across companies and years.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            """
            <div class="module-card">
                <div class="module-icon">🔎</div>
                <div class="module-title">
                    Qualitative Intelligence
                </div>
                <div class="module-text">
                    Surface strategic, management,
                    ESG and workforce developments
                    with annual-report evidence.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:

        st.markdown(
            """
            <div class="module-card">
                <div class="module-icon">🤖</div>
                <div class="module-title">
                    Research Copilot
                </div>
                <div class="module-text">
                    Ask natural-language questions
                    and retrieve supporting annual-report
                    evidence before generating an answer.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    st.markdown(
        "### Revenue Benchmark"
    )

    benchmark_metric = st.selectbox(
        "Select KPI",
        list(METRICS),
        format_func=lambda x:
            METRICS[x],
        key="overview_metric",
    )

    benchmark_rows = []

    for company in selected_companies:

        benchmark_rows.append(
            {
                "Company":
                    company,

                METRICS[
                    benchmark_metric
                ]:
                    numeric_value(
                        record(
                            company,
                            selected_year,
                        ),
                        benchmark_metric,
                    ),
            }
        )

    benchmark_df = pd.DataFrame(
        benchmark_rows
    )

    st.dataframe(
        benchmark_df,
        width="stretch",
        hide_index=True,
    )

    numeric_column = METRICS[
        benchmark_metric
    ]

    if (
        not benchmark_df.empty
        and benchmark_df[
            numeric_column
        ].notna().any()
    ):

        st.bar_chart(
            benchmark_df.set_index(
                "Company"
            )[
                numeric_column
            ]
        )


    st.markdown(
        "### Two-Year Revenue Trend"
    )

    revenue_rows = []

    for company in selected_companies:

        for year in YEARS:

            revenue_rows.append(
                {
                    "Company":
                        company,

                    "Fiscal Year":
                        year,

                    "Revenue":
                        numeric_value(
                            record(
                                company,
                                year,
                            ),
                            "revenue",
                        ),
                }
            )

    revenue_df = pd.DataFrame(
        revenue_rows
    )

    revenue_pivot = (
        revenue_df
        .pivot_table(
            index="Fiscal Year",
            columns="Company",
            values="Revenue",
            aggfunc="first",
        )
    )

    st.line_chart(
        revenue_pivot
    )


    st.markdown(
        "### FY2024 → FY2025 Revenue Movement"
    )

    revenue_change = []

    for company in selected_companies:

        data = yoy_data(
            company,
            "revenue",
        )

        revenue_change.append(
            {
                "Company":
                    company,

                "FY2024":
                    data.get(
                        "previous_value"
                    ),

                "FY2025":
                    data.get(
                        "current_value"
                    ),

                "Change (₹ Cr)":
                    data.get(
                        "absolute_change"
                    ),

                "Change (%)":
                    data.get(
                        "percentage_change"
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(
            revenue_change
        ),
        width="stretch",
        hide_index=True,
    )


# ============================================================
# QUANTITATIVE
# ============================================================

with quantitative_tab:

    st.markdown(
        '<div class="section-title">'
        'Quantitative Intelligence'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Financial performance, operational efficiency, '
        'cash flow and workforce benchmarking.'
        '</div>',
        unsafe_allow_html=True,
    )

    quantitative_metric = st.selectbox(
        "Select KPI",
        list(METRICS),
        format_func=lambda x:
            METRICS[x],
        key="quantitative_metric",
    )

    metric_rows = []

    for company in selected_companies:

        for year in YEARS:

            metric_rows.append(
                {
                    "Company":
                        company,

                    "Fiscal Year":
                        year,

                    METRICS[
                        quantitative_metric
                    ]:
                        numeric_value(
                            record(
                                company,
                                year,
                            ),
                            quantitative_metric,
                        ),
                }
            )

    metric_df = pd.DataFrame(
        metric_rows
    )

    st.dataframe(
        metric_df,
        width="stretch",
        hide_index=True,
    )

    metric_column = METRICS[
        quantitative_metric
    ]

    metric_pivot = (
        metric_df
        .pivot_table(
            index="Fiscal Year",
            columns="Company",
            values=metric_column,
            aggfunc="first",
        )
    )

    if metric_pivot.notna().any().any():

        st.line_chart(
            metric_pivot
        )


    st.markdown(
        "### Year-over-Year Analysis"
    )

    yoy_rows = []

    for company in selected_companies:

        data = yoy_data(
            company,
            quantitative_metric,
        )

        row = {
            "Company":
                company,

            "Previous":
                data.get(
                    "previous_value"
                ),

            "Current":
                data.get(
                    "current_value"
                ),

            "Absolute Change":
                data.get(
                    "absolute_change"
                ),
        }

        if quantitative_metric in RATE_METRICS:

            row[
                "Change (percentage points)"
            ] = data.get(
                "absolute_change"
            )

        else:

            row[
                "Change (%)"
            ] = data.get(
                "percentage_change"
            )

        yoy_rows.append(
            row
        )

    st.dataframe(
        pd.DataFrame(
            yoy_rows
        ),
        width="stretch",
        hide_index=True,
    )


    st.markdown(
        "### Long-Term Change / CAGR"
    )

    cagr_rows = []

    for company in selected_companies:

        data = cagr_data(
            company,
            quantitative_metric,
        )

        cagr_rows.append(
            {
                "Company":
                    company,

                "Start":
                    data.get(
                        "start_value"
                    ),

                "End":
                    data.get(
                        "end_value"
                    ),

                "CAGR (%)":
                    data.get(
                        "cagr_percent"
                    ),

                "Change (pp)":
                    data.get(
                        "change_percentage_points"
                    ),
            }
        )

    st.dataframe(
        pd.DataFrame(
            cagr_rows
        ),
        width="stretch",
        hide_index=True,
    )


    st.markdown(
        f"### {selected_year} Peer Benchmark"
    )

    peer_rows = []

    peer_data = cross_data(
        selected_year,
        quantitative_metric,
    )

    for company in selected_companies:

        peer_rows.append(
            {
                "Company":
                    company,

                METRICS[
                    quantitative_metric
                ]:
                    peer_data.get(
                        company
                    ),
            }
        )

    peer_df = pd.DataFrame(
        peer_rows
    )

    st.dataframe(
        peer_df,
        width="stretch",
        hide_index=True,
    )

    if (
        not peer_df.empty
        and peer_df[
            METRICS[
                quantitative_metric
            ]
        ].notna().any()
    ):

        st.bar_chart(
            peer_df.set_index(
                "Company"
            )
        )


    st.info(
        "Comparisons should be interpreted with "
        "company-specific definitions and source "
        "comparability notes."
    )


# ============================================================
# QUALITATIVE
# ============================================================

with qualitative_tab:

    st.markdown(
        '<div class="section-title">'
        'Qualitative Corporate Intelligence'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Evidence-supported developments across strategy, '
        'leadership, ESG and workforce.'
        '</div>',
        unsafe_allow_html=True,
    )

    qualitative_company = st.selectbox(
        "Company",
        selected_companies,
        key="qualitative_company",
    )

    qualitative_year = st.selectbox(
        "Fiscal Year",
        YEARS,
        index=1,
        key="qualitative_year",
    )

    qualitative_record = qrecord(
        qualitative_company,
        qualitative_year,
    )

    if not qualitative_record:

        st.warning(
            "No qualitative analysis is available "
            "for this company-year."
        )

    else:

        source_documents = (
            qualitative_record.get(
                "source_documents",
                [],
            )
        )

        if source_documents:

            st.caption(
                "Source: "
                + ", ".join(
                    source_documents
                )
            )

        qualitative_tabs = st.tabs(
            list(
                QUAL_CATEGORIES.values()
            )
        )

        for tab, (
            category,
            label,
        ) in zip(
            qualitative_tabs,
            QUAL_CATEGORIES.items(),
        ):

            with tab:

                findings = (
                    qualitative_record.get(
                        category,
                        [],
                    )
                )

                if not findings:

                    st.info(
                        "No supported finding was "
                        "extracted for this category."
                    )

                for index, finding in enumerate(
                    findings,
                    1,
                ):

                    st.markdown(
                        f"""
<div class="insight">
<div class="insight-title">
{index}. {finding.get("finding", "N/A")}
</div>

<div class="insight-source">
Source:
{
    source_documents[0]
    if source_documents
    else "annual report"
}
&nbsp; • &nbsp;
Page {finding.get("source_page", "N/A")}
</div>
</div>
""",
                        unsafe_allow_html=True,
                    )

                    evidence = finding.get(
                        "evidence"
                    )

                    if evidence:

                        st.markdown(
                            f"""
<div class="evidence">
<strong>Evidence</strong><br>
{evidence}
</div>
""",
                            unsafe_allow_html=True,
                        )


# ============================================================
# RESEARCH COPILOT
# ============================================================

with copilot_tab:

    st.markdown(
        '<div class="section-title">'
        '🤖 Research Copilot'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Ask questions about the annual reports. '
        'TrustRAG retrieves supporting evidence before '
        'generating the response.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="chat-context">
<strong>Evidence-grounded research</strong><br>
Answers are generated using the TrustRAG retrieval
pipeline and the selected annual-report corpus.
</div>
""",
        unsafe_allow_html=True,
    )

    st.write("")

    chat_companies = st.multiselect(
        "Companies",
        available_companies,
        default=selected_companies,
        key="chat_companies",
    )

    chat_years = st.multiselect(
        "Fiscal Years",
        YEARS,
        default=YEARS,
        key="chat_years",
    )

    question = st.text_area(
        "Research Question",
        placeholder=(
            "Example: Compare revenue growth, "
            "operating margin and workforce "
            "developments between FY2024 and FY2025."
        ),
        height=110,
        key="research_question",
    )

    ask = st.button(
        "🔍 Ask TrustRAG",
        type="primary",
        width="stretch",
    )

    if ask:

        if not question.strip():

            st.warning(
                "Please enter a research question."
            )

        elif not chat_companies:

            st.warning(
                "Select at least one company."
            )

        elif not chat_years:

            st.warning(
                "Select at least one fiscal year."
            )

        else:

            with st.spinner(
                "Retrieving annual-report evidence..."
            ):

                try:

                    # Import only when the chatbot
                    # is actually used.
                    from rag import retrieve

                    from google import genai
                    from google.genai import types

                    api_key = os.getenv(
                        "GOOGLE_API_KEY"
                    )

                    if not api_key:

                        raise RuntimeError(
                            "GOOGLE_API_KEY is missing "
                            "from your .env file."
                        )

                    client = genai.Client(
                        api_key=api_key
                    )

                    context = []

                    # --------------------------------
                    # Quantitative context
                    # --------------------------------

                    context.append(
                        "===== QUANTITATIVE DATA ====="
                    )

                    for company in chat_companies:

                        for fiscal_year in chat_years:

                            data = record(
                                company,
                                fiscal_year,
                            )

                            if not data:

                                continue

                            context.append(
                                f"--- {company} | "
                                f"{fiscal_year} ---"
                            )

                            for metric, label in (
                                METRICS.items()
                            ):

                                value = numeric_value(
                                    data,
                                    metric,
                                )

                                if value is not None:

                                    context.append(
                                        f"{label}: {value}"
                                    )


                    # --------------------------------
                    # Qualitative context
                    # --------------------------------

                    context.append(
                        "===== QUALITATIVE DATA ====="
                    )

                    for company in chat_companies:

                        for fiscal_year in chat_years:

                            data = qrecord(
                                company,
                                fiscal_year,
                            )

                            if not data:

                                continue

                            context.append(
                                f"--- {company} | "
                                f"{fiscal_year} ---"
                            )

                            for category, label in (
                                QUAL_CATEGORIES.items()
                            ):

                                for finding in (
                                    data.get(
                                        category,
                                        [],
                                    )
                                ):

                                    context.append(
                                        f"{label}: "
                                        f"{finding.get('finding')}; "
                                        f"Page: "
                                        f"{finding.get('source_page')}; "
                                        f"Evidence: "
                                        f"{finding.get('evidence')}"
                                    )


                    # --------------------------------
                    # RAG evidence
                    # --------------------------------

                    context.append(
                        "===== ANNUAL REPORT EVIDENCE ====="
                    )

                    for company in chat_companies:

                        for fiscal_year in chat_years:

                            try:

                                chunks = retrieve(
                                    question,
                                    k=5,
                                    company=company,
                                    fiscal_year=fiscal_year,
                                )

                            except Exception:

                                chunks = []

                            for chunk in chunks:

                                source = Path(
                                    chunk.get(
                                        "source_document",
                                        "annual_report",
                                    )
                                ).stem

                                context.append(
                                    f"""
[{company} |
{fiscal_year} |
{source} |
p.{chunk.get("page", "N/A")}]

{chunk.get("text", "")}
"""
                                )


                    prompt = f"""
You are TrustRAG, an evidence-grounded
corporate research copilot.

USER QUESTION:
{question}

TRUSTRAG CONTEXT:
{chr(10).join(context)}

RULES:

1. Use ONLY the supplied TrustRAG context.
2. Do not use outside knowledge.
3. Do not invent numbers or facts.
4. If evidence is insufficient, say so.
5. Distinguish reported metrics from derived metrics.
6. Cite quantitative claims as:
   [Company | FY202X]
7. Cite report evidence as:
   [Company | FY202X | p.X]
8. Do not make unsupported causal claims.
9. Mention important comparability caveats.
10. Answer in a professional consulting/research style.

Structure the response as:

### Key Findings

### Evidence

### Caveats

Only include sections that are useful.
"""

                    response = client.models.generate_content(
                        model="gemini-3.1-flash-lite",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                        ),
                    )

                    st.markdown(
                        "### Research Output"
                    )

                    if response and response.text:

                        st.markdown(
                            response.text
                        )

                    else:

                        st.warning(
                            "No response was returned."
                        )

                except Exception as error:

                    st.error(
                        "The Research Copilot could not "
                        "complete the request."
                    )

                    st.code(
                        str(error)
                    )

                    st.info(
                        "The rest of the dashboard does not "
                        "depend on the chatbot. Check your "
                        "RAG environment and API key if this "
                        "message appears."
                    )


# ============================================================
# EVIDENCE
# ============================================================

with evidence_tab:

    st.markdown(
        '<div class="section-title">'
        '📚 Evidence & Auditability'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Trace extracted metrics back to the underlying '
        'annual-report evidence.'
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

    evidence_metric = st.selectbox(
        "KPI",
        list(METRICS),
        format_func=lambda x:
            METRICS[x],
        key="evidence_metric",
    )

    evidence_record = record(
        evidence_company,
        evidence_year,
    )

    evidence_object = obj(
        evidence_record,
        evidence_metric,
    )

    c1, c2, c3 = st.columns(
        3,
        gap="medium",
    )

    with c1:

        st.metric(
            "Value",
            fmt(
                evidence_object.get(
                    "value"
                ),
                evidence_metric,
            ),
        )

    with c2:

        st.metric(
            "Status",
            str(
                evidence_object.get(
                    "status",
                    "N/A",
                )
            ),
        )

    with c3:

        st.metric(
            "Source Page",
            str(
                evidence_object.get(
                    "source_page",
                    "N/A",
                )
            ),
        )

    if evidence_object.get(
        "reported_label"
    ):

        st.markdown(
            "### Reported Label"
        )

        st.write(
            evidence_object[
                "reported_label"
            ]
        )

    if evidence_object.get(
        "evidence"
    ):

        st.markdown(
            "### Supporting Evidence"
        )

        st.markdown(
            f"""
<div class="evidence">
{evidence_object["evidence"]}
</div>
""",
            unsafe_allow_html=True,
        )

    if evidence_object.get(
        "notes"
    ):

        st.markdown(
            "### Notes"
        )

        st.caption(
            evidence_object[
                "notes"
            ]
        )


    st.divider()

    st.markdown(
        "### Data Coverage"
    )

    coverage_rows = []

    for company in available_companies:

        for year in YEARS:

            data = record(
                company,
                year,
            )

            available_metrics = sum(
                numeric_value(
                    data,
                    metric,
                )
                is not None
                for metric in METRICS
            )

            coverage_rows.append(
                {
                    "Company":
                        company,

                    "Fiscal Year":
                        year,

                    "Available Metrics":
                        available_metrics,

                    "Total Metrics":
                        len(METRICS),

                    "Coverage (%)":
                        round(
                            available_metrics
                            / len(METRICS)
                            * 100,
                            1,
                        ),
                }
            )

    coverage_df = pd.DataFrame(
        coverage_rows
    )

    st.dataframe(
        coverage_df,
        width="stretch",
        hide_index=True,
    )


    st.divider()

    st.markdown(
        "### Export"
    )

    if EXCEL_FILE.exists():

        with open(
            EXCEL_FILE,
            "rb",
        ) as excel_file:

            st.download_button(
                "📥 Download TrustRAG Excel Report",
                data=excel_file,
                file_name=(
                    "TrustRAG_Benchmarking_Report.xlsx"
                ),
                mime=(
                    "application/"
                    "vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch",
            )

    else:

        st.info(
            "Excel benchmarking report is not available."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#64748b;
        font-size:.78rem;
        padding:1rem;
    ">
        <strong>TrustRAG</strong>
        &nbsp;•&nbsp;
        Corporate Intelligence
        &nbsp;•&nbsp;
        Quantitative + Qualitative + RAG
        &nbsp;•&nbsp;
        FY2024–FY2025
    </div>
    """,
    unsafe_allow_html=True,
)