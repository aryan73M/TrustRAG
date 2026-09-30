import json
from pathlib import Path


INPUT_FILE = Path("data/multiyear_kpis.json")
OUTPUT_FILE = Path("data/quantitative_analysis.json")


# Metrics for which numerical trend analysis makes sense
NUMERIC_METRICS = [
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
    "pat_margin",
    "revenue_per_employee",
    "employee_growth",
    "fcf_margin",
    "standardized_fcf",
]

RATE_METRICS = {
    "revenue_growth",
    "operating_margin",
    "roe",
    "attrition",
    "pat_margin",
    "fcf_margin",
}   

def numeric_value(metric):

    if not isinstance(metric, dict):
        return None

    value = metric.get("value")

    if value is None:
        return None

    if metric.get("status") not in [
        "reported",
        "derived",
        "reported_or_derived",
        "reported_or_derived"
    ]:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fiscal_year_number(year):

    if not year:
        return None

    try:
        return int(
            year.replace("FY", "")
        )
    except (ValueError, AttributeError):
        return None


def calculate_yoy(previous, current):

    if previous is None or current is None:
        return None

    if previous == 0:
        return None

    return ((current - previous) / abs(previous)) * 100


def calculate_change(previous, current):

    if previous is None or current is None:
        return None

    return current - previous


def calculate_cagr(start_value, end_value, years):

    if (
        start_value is None
        or end_value is None
        or years <= 0
        or start_value <= 0
        or end_value < 0
    ):
        return None

    return (
        (end_value / start_value) ** (1 / years) - 1
    ) * 100


def load_data():

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def build_company_history(records):

    companies = {}

    for record in records:

        company = record["company"]
        fiscal_year = record["fiscal_year"]

        if company not in companies:
            companies[company] = {}

        companies[company][fiscal_year] = record["metrics"]

    return companies


def build_yoy_analysis(companies):

    yoy_analysis = {}

    for company, years_data in companies.items():

        years = sorted(
            years_data.keys(),
            key=fiscal_year_number
        )

        yoy_analysis[company] = {}

        for i in range(1, len(years)):

            previous_year = years[i - 1]
            current_year = years[i]

            previous_metrics = years_data[previous_year]
            current_metrics = years_data[current_year]

            comparison_key = (
                f"{previous_year}_to_{current_year}"
            )

            yoy_analysis[company][comparison_key] = {}

            for metric_name in NUMERIC_METRICS:

                previous_value = numeric_value(
                    previous_metrics.get(metric_name)
                )

                current_value = numeric_value(
                    current_metrics.get(metric_name)
                )

                if metric_name in RATE_METRICS:

                    yoy_analysis[company][comparison_key][
                        metric_name
                    ] = {
                        "previous_year": previous_year,
                        "current_year": current_year,
                        "previous_value": previous_value,
                        "current_value": current_value,
                        "percentage_point_change": calculate_change(
                            previous_value,
                            current_value
                        ),
                        "percentage_change": None,
                    }

                else:

                    yoy_analysis[company][comparison_key][
                        metric_name
                    ] = {
                        "previous_year": previous_year,
                        "current_year": current_year,
                        "previous_value": previous_value,
                        "current_value": current_value,
                        "absolute_change": calculate_change(
                            previous_value,
                            current_value
                        ),
                        "percentage_change": calculate_yoy(
                            previous_value,
                            current_value
                        ),
                    }

    return yoy_analysis


def build_cagr_analysis(companies):

    cagr_analysis = {}

    for company, years_data in companies.items():

        years = sorted(
            years_data.keys(),
            key=fiscal_year_number
        )

        if len(years) < 2:
            continue

        start_year = years[0]
        end_year = years[-1]

        start_metrics = years_data[start_year]
        end_metrics = years_data[end_year]

        number_of_years = (
            fiscal_year_number(end_year)
            - fiscal_year_number(start_year)
        )

        cagr_analysis[company] = {
            "start_year": start_year,
            "end_year": end_year,
            "years": number_of_years,
            "metrics": {},
        }

        for metric_name in NUMERIC_METRICS:

            start_value = numeric_value(
                start_metrics.get(metric_name)
            )

            end_value = numeric_value(
                end_metrics.get(metric_name)
            )

            if metric_name in RATE_METRICS:

                cagr_analysis[company]["metrics"][
                    metric_name
                ] = {
                    "start_value": start_value,
                    "end_value": end_value,
                    "cagr_percent": None,
                    "change_percentage_points": calculate_change(
                        start_value,
                        end_value
                    ),
                }

            else:

                cagr_analysis[company]["metrics"][
                    metric_name
                ] = {
                    "start_value": start_value,
                    "end_value": end_value,
                    "cagr_percent": calculate_cagr(
                        start_value,
                        end_value,
                        number_of_years
                    ),
                }

    return cagr_analysis


def build_cross_company_analysis(companies):

    all_years = set()

    for company_data in companies.values():
        all_years.update(company_data.keys())

    all_years = sorted(
        all_years,
        key=fiscal_year_number
    )

    result = {}

    for year in all_years:

        result[year] = {}

        for metric_name in NUMERIC_METRICS:

            result[year][metric_name] = {}

            for company, company_data in companies.items():

                metrics = company_data.get(year)

                if metrics is None:
                    value = None
                else:
                    value = numeric_value(
                        metrics.get(metric_name)
                    )

                result[year][metric_name][company] = value

    return result


def main():

    if not INPUT_FILE.exists():

        print(
            f"ERROR: Input file not found: {INPUT_FILE}"
        )

        return

    print("=" * 70)
    print("TRUSTRAG QUANTITATIVE ANALYSIS ENGINE")
    print("=" * 70)

    records = load_data()

    print(
        f"Loaded {len(records)} company-year records."
    )

    companies = build_company_history(records)

    print()
    print("COMPANIES AND YEARS")

    for company, years_data in companies.items():

        print(
            f"{company}: "
            f"{', '.join(sorted(years_data.keys(), key=fiscal_year_number))}"
        )

    print()
    print("Calculating YoY analysis...")

    yoy_analysis = build_yoy_analysis(companies)

    print("Calculating CAGR analysis...")

    cagr_analysis = build_cagr_analysis(companies)

    print("Calculating cross-company analysis...")

    cross_company_analysis = (
        build_cross_company_analysis(companies)
    )

    output = {
        "companies": companies,
        "yoy_analysis": yoy_analysis,
        "cagr_analysis": cagr_analysis,
        "cross_company_analysis": cross_company_analysis,
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

    print()
    print("=" * 70)
    print("QUANTITATIVE ANALYSIS COMPLETE")
    print("=" * 70)

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()