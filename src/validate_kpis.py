import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

TARGET_FISCAL_YEAR = "FY2025"

INPUT_FILE = Path(f"data/kpis_{TARGET_FISCAL_YEAR}.json")
OUTPUT_FILE = Path(f"data/validated_kpis_{TARGET_FISCAL_YEAR}.json")


# ============================================================
# HELPERS
# ============================================================

def get_metric(company, metric_name):
    """Safely retrieve a KPI from a company record."""
    metric = company.get(metric_name, {})

    if metric.get("status") != "reported":
        return None

    return metric.get("value")


def calculate_percentage(numerator, denominator):
    """Calculate percentage safely."""
    if numerator is None or denominator in (None, 0):
        return None

    return round((numerator / denominator) * 100, 2)


def calculate_revenue_per_employee(revenue, employees):
    """
    Revenue is in INR crore.
    Employees are absolute headcount.

    Result = INR crore per employee.
    """
    if revenue is None or employees in (None, 0):
        return None

    return round(revenue / employees, 4)


def add_derived_metric(name, value, unit, formula, notes=None):
    """Create a standard derived KPI object."""

    return {
        "status": "derived",
        "value": value,
        "unit": unit,
        "reported_label": None,
        "fiscal_year": "FY2024",
        "source_page": None,
        "evidence": None,
        "notes": notes,
        "formula": formula,
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_company(company):

    company_name = company["company"]

    print()
    print("-" * 70)
    print(f"VALIDATING: {company_name}")
    print("-" * 70)

    validation_flags = []

    # --------------------------------------------------------
    # Core KPI checks
    # --------------------------------------------------------

    core_metrics = [
        "revenue",
        "revenue_growth",
        "operating_margin",
        "pat",
        "eps",
        "roe",
        "employees",
    ]

    for metric_name in core_metrics:

        metric = company.get(metric_name, {})

        if metric.get("status") == "reported":

            if metric.get("value") is None:
                validation_flags.append(
                    f"{metric_name}: reported but value is missing"
                )

            if metric.get("source_page") is None:
                validation_flags.append(
                    f"{metric_name}: reported but source page is missing"
                )

            if not metric.get("evidence"):
                validation_flags.append(
                    f"{metric_name}: reported but evidence is missing"
                )

    # --------------------------------------------------------
    # Unit checks
    # --------------------------------------------------------

    expected_units = {
        "revenue": "INR crore",
        "pat": "INR crore",
        "eps": "INR",
        "employees": "employees",
    }

    for metric_name, expected_unit in expected_units.items():

        metric = company.get(metric_name, {})

        if metric.get("status") == "reported":

            actual_unit = metric.get("unit")

            if actual_unit != expected_unit:

                validation_flags.append(
                    f"{metric_name}: expected unit '{expected_unit}', "
                    f"found '{actual_unit}'"
                )

    # --------------------------------------------------------
    # Revenue sanity check
    # --------------------------------------------------------

    revenue = get_metric(company, "revenue")

    if revenue is not None and revenue <= 0:

        validation_flags.append(
            "revenue: non-positive value"
        )

    # --------------------------------------------------------
    # Employee sanity check
    # --------------------------------------------------------

    employees = get_metric(company, "employees")

    if employees is not None and employees <= 0:

        validation_flags.append(
            "employees: non-positive value"
        )

    # --------------------------------------------------------
    # Margin sanity checks
    # --------------------------------------------------------

    for metric_name in [
        "revenue_growth",
        "operating_margin",
        "roe",
        "attrition",
    ]:

        metric = company.get(metric_name, {})

        if metric.get("status") == "reported":

            value = metric.get("value")

            if value is not None and (
                value < -100 or value > 100
            ):

                validation_flags.append(
                    f"{metric_name}: suspicious percentage {value}%"
                )

    # ========================================================
    # DERIVED METRICS
    # ========================================================

    pat = get_metric(company, "pat")

    # --------------------------------------------------------
    # PAT Margin
    # --------------------------------------------------------

    pat_margin = calculate_percentage(
        pat,
        revenue
    )

    company["pat_margin"] = add_derived_metric(
        name="pat_margin",
        value=pat_margin,
        unit="%",
        formula="PAT / Revenue × 100",
        notes="Calculated deterministically from reported PAT and revenue."
    )

    # --------------------------------------------------------
    # Revenue per Employee
    # --------------------------------------------------------

    revenue_per_employee = calculate_revenue_per_employee(
        revenue,
        employees
    )

    company["revenue_per_employee"] = add_derived_metric(
        name="revenue_per_employee",
        value=revenue_per_employee,
        unit="INR crore per employee",
        formula="Revenue / Employee Headcount",
        notes=(
            "Calculated deterministically. "
            "Revenue is reported in INR crore."
        )
    )

    # --------------------------------------------------------
    # Free Cash Flow Margin
    # --------------------------------------------------------

    fcf = get_metric(company, "free_cash_flow")

    fcf_margin = calculate_percentage(
        fcf,
        revenue
    )

    company["fcf_margin"] = add_derived_metric(
        name="fcf_margin",
        value=fcf_margin,
        unit="%",
        formula="Free Cash Flow / Revenue × 100",
        notes=(
            "Calculated only when reported Free Cash Flow "
            "is available."
        )
    )

    # --------------------------------------------------------
    # Employee Growth
    #
    # We do NOT calculate this yet because the current
    # KPI extraction schema only stores FY2024 headcount.
    # --------------------------------------------------------

    company["employee_growth"] = {
        "status": "not_available",
        "value": None,
        "unit": "%",
        "reported_label": None,
        "fiscal_year": "FY2024",
        "source_page": None,
        "evidence": None,
        "notes": (
            "FY2023 headcount is not currently stored in "
            "the KPI extraction output."
        ),
        "formula": (
            "(FY2024 Employees - FY2023 Employees) "
            "/ FY2023 Employees × 100"
        ),
    }

    # ========================================================
    # COMPARABILITY FLAGS
    # ========================================================

    comparability = {}

    # Revenue
    comparability["revenue"] = {
        "level": "high",
        "reason": (
            "Consolidated revenue from operations/revenue "
            "reported for FY2024."
        ),
    }

    # Revenue Growth
    comparability["revenue_growth"] = {
        "level": "high",
        "reason": (
            "Reported FY2024 year-on-year revenue growth."
        ),
    }

    # Operating Margin
    comparability["operating_margin"] = {
        "level": "medium",
        "reason": (
            "Companies use related but not necessarily "
            "identical operating-margin definitions."
        ),
    }

    # PAT
    comparability["pat"] = {
        "level": "medium",
        "reason": (
            "Profit definitions may differ, e.g. total "
            "profit versus profit attributable to owners."
        ),
    }

    # EPS
    comparability["eps"] = {
        "level": "medium",
        "reason": (
            "Reported EPS is comparable at a high level, "
            "but accounting/share-base definitions should "
            "be retained from each company."
        ),
    }

    # ROE
    comparability["roe"] = {
        "level": "medium",
        "reason": (
            "TCS did not report a supported FY2024 ROE in "
            "the extracted evidence; HCLTech uses return "
            "on net worth terminology."
        ),
    }

    # Employees
    comparability["employees"] = {
        "level": "medium",
        "reason": (
            "Headcount scope and reporting definitions "
            "can differ by company."
        ),
    }

    # Attrition
    comparability["attrition"] = {
        "level": "low",
        "reason": (
            "TCS reports LTM IT-services attrition while "
            "Infosys reports turnover for permanent employees; "
            "HCLTech value was not found."
        ),
    }

    # Cash
    comparability["cash_liquid_assets"] = {
        "level": "low",
        "reason": (
            "Reported definitions differ: for example, "
            "cash and investments versus invested funds."
        ),
    }

    # FCF
    comparability["free_cash_flow"] = {
        "level": "low",
        "reason": (
            "FY2024 INR FCF was not explicitly extracted "
            "for the three companies."
        ),
    }

    # Capex
    comparability["capex"] = {
        "level": "low",
        "reason": (
            "Capex was not consistently available as a "
            "comparable FY2024 aggregate."
        ),
    }

    company["comparability"] = comparability

    # ========================================================
    # VALIDATION SUMMARY
    # ========================================================

    company["validation"] = {
        "status": (
            "passed_with_flags"
            if validation_flags
            else "passed"
        ),
        "flags": validation_flags,
    }

    # --------------------------------------------------------
    # Print summary
    # --------------------------------------------------------

    print(
        f"Revenue: {revenue}"
    )

    print(
        f"PAT: {pat}"
    )

    print(
        f"PAT Margin: {pat_margin}%"
    )

    print(
        f"Revenue / Employee: "
        f"{revenue_per_employee}"
    )

    print(
        f"Validation flags: "
        f"{len(validation_flags)}"
    )

    for flag in validation_flags:

        print(
            f"  ⚠ {flag}"
        )

    return company


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("TRUSTRAG KPI VALIDATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Load extracted KPIs
    # --------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        companies = json.load(f)

    print(
        f"Loaded {len(companies)} company records."
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validated_results = []

    for company in companies:

        # Handle failed Gemini extraction records
        if "error" in company:

            print(
                f"\nSkipping {company.get('company')} "
                f"because extraction failed."
            )

            validated_results.append(company)

            continue

        validated_company = validate_company(
            company
        )

        validated_results.append(
            validated_company
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

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
            validated_results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()