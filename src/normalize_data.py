import json
from pathlib import Path


INPUT_FILE = Path("data/calculated_kpis.json")
OUTPUT_FILE = Path("data/kpis_long.json")


# KPI fields that should be converted into long format
KPI_FIELDS = [
    "revenue",
    "revenue_growth",
    "operating_margin",
    "pat",
    "pat_margin",
    "eps",
    "roe",
    "free_cash_flow",
    "standardized_fcf",
    "capex",
    "operating_cash_flow",
    "cash_liquid_assets",
    "employees",
    "attrition",
    "revenue_per_employee",
    "employee_growth",
    "fcf_margin",
]


def normalize_company(company_data):

    company = company_data.get("company")

    normalized_records = []

    # Most of the current dataset is FY2024
    fiscal_year = "FY2024"

    for metric in KPI_FIELDS:

        kpi = company_data.get(metric)

        if not isinstance(kpi, dict):
            continue

        record = {
            "company": company,
            "fiscal_year": fiscal_year,
            "metric": metric,
            "value": kpi.get("value"),
            "unit": kpi.get("unit"),
            "reported_label": kpi.get("reported_label"),
            "source_page": kpi.get("source_page"),
            "evidence": kpi.get("evidence"),
            "status": kpi.get("status"),
            "notes": kpi.get("notes"),
            "comparability": kpi.get("comparability"),
            "formula": kpi.get("formula"),
            "inputs": kpi.get("inputs"),
        }

        normalized_records.append(record)

    return normalized_records


def main():

    print("=" * 70)
    print("NORMALIZING KPI DATA")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    all_records = []

    for company_data in data:

        company = company_data.get(
            "company",
            "Unknown"
        )

        print(f"Processing: {company}")

        records = normalize_company(
            company_data
        )

        all_records.extend(records)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_records,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 70)
    print("NORMALIZATION COMPLETE")
    print("=" * 70)
    print(f"Records created: {len(all_records)}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()