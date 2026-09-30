import json
from pathlib import Path


TARGET_FISCAL_YEAR = "FY2025"

INPUT_FILE = Path(
    f"data/validated_kpis_{TARGET_FISCAL_YEAR}.json"
)

OUTPUT_FILE = Path(
    f"data/calculated_kpis_{TARGET_FISCAL_YEAR}.json"
)


def get_value(kpi):
    """
    Return the numeric KPI value only when the KPI
    has a valid reported/derived value.
    """
    if not isinstance(kpi, dict):
        return None

    status = kpi.get("status")
    value = kpi.get("value")

    if status in {"reported", "derived"} and value is not None:
        return value

    return None


def calculate_standardized_fcf(operating_cash_flow, capex):
    """
    Standardized FCF = Operating Cash Flow - |Capital Expenditure|

    Returns None when either input is unavailable.
    """
    if operating_cash_flow is None or capex is None:
        return None

    return round(operating_cash_flow - abs(capex), 2)


def calculate_metrics(company_data):
    """
    Calculate deterministic financial metrics for one company.
    """

    revenue = get_value(company_data.get("revenue"))
    pat = get_value(company_data.get("pat"))
    employees = get_value(company_data.get("employees"))

    operating_cash_flow = get_value(
        company_data.get("operating_cash_flow")
    )

    capex = get_value(
        company_data.get("capex")
    )

    # ---------------------------------------------------------
    # 1. PAT Margin
    # ---------------------------------------------------------

    if revenue is not None and pat is not None and revenue != 0:
        pat_margin = round((pat / revenue) * 100, 2)

        company_data["pat_margin"] = {
            "value": pat_margin,
            "unit": "%",
            "status": "derived",
            "formula": "PAT / Revenue × 100",
            "inputs": {
                "pat": pat,
                "revenue": revenue,
            },
        }
    else:
        company_data["pat_margin"] = {
            "value": None,
            "unit": "%",
            "status": "not_calculated",
            "formula": "PAT / Revenue × 100",
            "inputs": {},
        }

    # ---------------------------------------------------------
    # 2. Revenue per Employee
    # ---------------------------------------------------------

    if revenue is not None and employees is not None and employees != 0:
        revenue_per_employee = round(
            revenue / employees,
            4
        )

        company_data["revenue_per_employee"] = {
            "value": revenue_per_employee,
            "unit": "INR crore per employee",
            "status": "derived",
            "formula": "Revenue / Employee Headcount",
            "inputs": {
                "revenue": revenue,
                "employees": employees,
            },
        }
    else:
        company_data["revenue_per_employee"] = {
            "value": None,
            "unit": "INR crore per employee",
            "status": "not_calculated",
            "formula": "Revenue / Employee Headcount",
            "inputs": {},
        }

    # ---------------------------------------------------------
    # 3. Standardized Free Cash Flow
    # ---------------------------------------------------------

    standardized_fcf = calculate_standardized_fcf(
        operating_cash_flow,
        capex
    )

    if standardized_fcf is not None:

        company_data["standardized_fcf"] = {
            "value": standardized_fcf,
            "unit": "INR crore",
            "status": "derived",
            "formula": "Operating Cash Flow - |Capital Expenditure|",
            "inputs": {
                "operating_cash_flow": operating_cash_flow,
                "capex": capex,
            },
        }

    else:

        company_data["standardized_fcf"] = {
            "value": None,
            "unit": "INR crore",
            "status": "not_calculated",
            "formula": "Operating Cash Flow - |Capital Expenditure|",
            "inputs": {
                "operating_cash_flow": operating_cash_flow,
                "capex": capex,
            },
            "reason": (
                "Standardized FCF was not calculated because "
                "Operating Cash Flow or Capital Expenditure "
                "was unavailable."
            ),
        }

    return company_data


def main():

    print("=" * 70)
    print("CALCULATING DETERMINISTIC METRICS")
    print("=" * 70)

    # ---------------------------------------------------------
    # Load validated KPI data
    # ---------------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ---------------------------------------------------------
    # Calculate metrics company by company
    # ---------------------------------------------------------

    calculated_data = []

    for company_data in data:

        company = company_data.get("company", "Unknown")

        print()
        print("-" * 70)
        print(f"COMPANY: {company}")
        print("-" * 70)

        calculated_company = calculate_metrics(
            company_data
    )

        calculated_data.append(calculated_company)

        pat_margin = calculated_company["pat_margin"]
        revenue_per_employee = calculated_company[
            "revenue_per_employee"
        ]
        standardized_fcf = calculated_company[
            "standardized_fcf"
        ]

        print(
            f"PAT Margin: "
            f"{pat_margin['value']}%"
            if pat_margin["value"] is not None
            else "PAT Margin: Not calculated"
        )

        print(
            f"Revenue / Employee: "
            f"{revenue_per_employee['value']}"
            if revenue_per_employee["value"] is not None
            else "Revenue / Employee: Not calculated"
        )

        print(
            f"Operating Cash Flow: "
            f"{operating_cash_flow}"
        ) if False else None

        print(
            f"Standardized FCF: "
            f"{standardized_fcf['value']} Cr"
            if standardized_fcf["value"] is not None
            else "Standardized FCF: Not calculated"
        )

        if standardized_fcf["status"] == "derived":
            print(
                "FCF Formula: "
                "Operating Cash Flow - |Capital Expenditure|"
            )
        else:
            print(
                "FCF Status: "
                "Not calculated — required inputs unavailable"
            )

    # ---------------------------------------------------------
    # Save output
    # ---------------------------------------------------------

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
            calculated_data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 70)
    print("CALCULATION COMPLETE")
    print("=" * 70)
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()