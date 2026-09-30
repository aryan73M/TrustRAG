# Core KPI definitions for TrustRAG
# These are the metrics the quantitative benchmarking
# engine will attempt to extract from each annual report.

KPI_DEFINITIONS = [
    {
        "name": "revenue",
        "label": "Revenue from Operations",
        "type": "reported",
        "unit": "INR crore",
        "description": (
            "Revenue from operations for the financial year."
        ),
    },
    {
        "name": "revenue_growth",
        "label": "Revenue Growth",
        "type": "derived_or_reported",
        "unit": "%",
        "description": (
            "Year-on-year growth in revenue from operations."
        ),
    },
    {
        "name": "operating_margin",
        "label": "Operating / EBIT Margin",
        "type": "reported_or_derived",
        "unit": "%",
        "description": (
            "Operating or EBIT margin as reported by the company. "
            "Preserve the company's definition."
        ),
    },
    {
        "name": "pat",
        "label": "Profit After Tax",
        "type": "reported",
        "unit": "INR crore",
        "description": (
            "Profit attributable to owners / profit after tax, "
            "using the company's reported definition."
        ),
    },
    {
        "name": "pat_margin",
        "label": "PAT Margin",
        "type": "derived",
        "unit": "%",
        "description": (
            "Profit after tax divided by revenue from operations."
        ),
    },
    {
        "name": "eps",
        "label": "Diluted EPS",
        "type": "reported",
        "unit": "INR",
        "description": (
            "Diluted earnings per share for the financial year."
        ),
    },
    {
        "name": "roe",
        "label": "Return on Equity",
        "type": "reported",
        "unit": "%",
        "description": (
            "Return on equity / return on net worth as reported."
        ),
    },
    {
        "name": "free_cash_flow",
        "label": "Free Cash Flow",
        "type": "reported_or_derived",
        "unit": "INR crore",
        "description": (
            "Free cash flow if explicitly reported. "
            "Do not invent it if the report does not provide it."
        ),
        
    },

    {
        "name": "operating_cash_flow",
        "label": "Operating Cash Flow",
        "description": "Cash generated from operating activities",
        "type": "reported",
        "unit": "INR crore",
    },
    {
        "name": "capex",
        "label": "Capital Expenditure",
        "type": "reported_or_derived",
        "unit": "INR crore",
        "description": (
            "Capital expenditure / additions to property, plant "
            "and equipment, using the company's disclosed definition."
        ),
    },
    {
        "name": "cash_liquid_assets",
        "label": "Cash & Liquid Investments",
        "type": "reported",
        "unit": "INR crore",
        "description": (
            "Cash, cash equivalents and liquid investments, "
            "where clearly disclosed."
        ),
    },
    {
        "name": "employees",
        "label": "Employee Headcount",
        "type": "reported",
        "unit": "employees",
        "description": (
            "Total employee headcount at the end of the financial year."
        ),
    },
    {
        "name": "attrition",
        "label": "Employee Attrition",
        "type": "reported",
        "unit": "%",
        "description": (
            "Employee attrition rate for the financial year."
        ),
    },
    {
        "name": "revenue_per_employee",
        "label": "Revenue per Employee",
        "type": "derived",
        "unit": "INR crore per employee",
        "description": (
            "Revenue from operations divided by employee headcount."
        ),
    },
    {
        "name": "employee_growth",
        "label": "Employee Growth",
        "type": "derived",
        "unit": "%",
        "description": (
            "Year-on-year growth in employee headcount."
        ),
    },
    {
        "name": "fcf_margin",
        "label": "Free Cash Flow Margin",
        "type": "derived",
        "unit": "%",
        "description": (
            "Free cash flow divided by revenue from operations."
        ),
    },
]


def get_kpi(name):
    """Return the definition for a KPI."""
    for kpi in KPI_DEFINITIONS:
        if kpi["name"] == name:
            return kpi

    raise ValueError(f"Unknown KPI: {name}")


def get_all_kpis():
    """Return all KPI definitions."""
    return KPI_DEFINITIONS