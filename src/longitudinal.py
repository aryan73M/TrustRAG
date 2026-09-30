import json
from pathlib import Path
from collections import defaultdict


INPUT_FILE = Path("data/kpis_long.json")
OUTPUT_FILE = Path("data/trends_long.json")


def fiscal_year_number(fiscal_year):
    """
    Convert FY2024 -> 2024 for sorting.
    """
    try:
        return int(
            fiscal_year.replace("FY", "")
        )
    except (ValueError, AttributeError):
        return None


def calculate_yoy(current_value, previous_value):
    """
    YoY Growth = ((Current - Previous) / Previous) * 100
    """
    if current_value is None or previous_value is None:
        return None

    if previous_value == 0:
        return None

    return round(
        ((current_value - previous_value) / previous_value) * 100,
        2
    )


def calculate_cagr(start_value, end_value, years):
    """
    CAGR = (Ending / Beginning)^(1 / years) - 1

    Returns percentage.
    """

    if (
        start_value is None
        or end_value is None
        or years <= 0
        or start_value <= 0
        or end_value <= 0
    ):
        return None

    return round(
        ((end_value / start_value) ** (1 / years) - 1) * 100,
        2
    )


def main():

    print("=" * 70)
    print("LONGITUDINAL ANALYSIS")
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

        records = json.load(f)

    # ---------------------------------------------------------
    # Group records by company + metric
    # ---------------------------------------------------------

    grouped = defaultdict(list)

    for record in records:

        company = record.get("company")
        metric = record.get("metric")

        if company is None or metric is None:
            continue

        grouped[
            (company, metric)
        ].append(record)

    trend_records = []

    # ---------------------------------------------------------
    # Calculate YoY
    # ---------------------------------------------------------

    for (company, metric), metric_records in grouped.items():

        metric_records.sort(
            key=lambda x: (
                fiscal_year_number(
                    x.get("fiscal_year")
                )
                or 0
            )
        )

        previous_value = None
        previous_year = None

        for record in metric_records:

            current_value = record.get("value")
            current_year = record.get("fiscal_year")

            yoy = None

            if (
                current_value is not None
                and previous_value is not None
            ):

                yoy = calculate_yoy(
                    current_value,
                    previous_value
                )

            trend_record = {
                "company": company,
                "metric": metric,
                "fiscal_year": current_year,
                "value": current_value,
                "unit": record.get("unit"),
                "yoy_growth": yoy,
                "source_page": record.get("source_page"),
                "evidence": record.get("evidence"),
                "status": record.get("status"),
            }

            trend_records.append(
                trend_record
            )

            if current_value is not None:
                previous_value = current_value
                previous_year = current_year

    # ---------------------------------------------------------
    # Calculate CAGR
    # ---------------------------------------------------------

    cagr_records = []

    for (company, metric), metric_records in grouped.items():

        valid_records = [
            r for r in metric_records
            if r.get("value") is not None
            and fiscal_year_number(
                r.get("fiscal_year")
            ) is not None
        ]

        valid_records.sort(
            key=lambda x: fiscal_year_number(
                x.get("fiscal_year")
            )
        )

        if len(valid_records) < 2:
            continue

        first = valid_records[0]
        last = valid_records[-1]

        first_year = fiscal_year_number(
            first.get("fiscal_year")
        )

        last_year = fiscal_year_number(
            last.get("fiscal_year")
        )

        years = last_year - first_year

        if years <= 0:
            continue

        cagr = calculate_cagr(
            first.get("value"),
            last.get("value"),
            years
        )

        if cagr is not None:

            cagr_records.append({
                "company": company,
                "metric": metric,
                "start_year": first.get("fiscal_year"),
                "end_year": last.get("fiscal_year"),
                "start_value": first.get("value"),
                "end_value": last.get("value"),
                "years": years,
                "cagr": cagr,
                "unit": first.get("unit"),
            })

    # ---------------------------------------------------------
    # Save output
    # ---------------------------------------------------------

    output = {
        "trend_records": trend_records,
        "cagr_records": cagr_records,
    }

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
    print("LONGITUDINAL ANALYSIS COMPLETE")
    print("=" * 70)

    print(
        f"Trend records: {len(trend_records)}"
    )

    print(
        f"CAGR records: {len(cagr_records)}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()