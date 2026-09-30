import json
from pathlib import Path


DATA_DIR = Path("data")

FILES = [
    DATA_DIR / "calculated_kpis.json",
    DATA_DIR / "calculated_kpis_FY2025.json",
]

OUTPUT_FILE = DATA_DIR / "multiyear_kpis.json"


def load_json(path):
    
    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def get_fiscal_year_from_filename(file_path):

    filename = file_path.name.upper()

    if "FY2025" in filename:
        return "FY2025"

    if filename == "CALCULATED_KPIS.JSON":
        return "FY2024"

    return None


def main():

    combined = []

    for file_path in FILES:

        if not file_path.exists():

            print(
                f"WARNING: Missing file: {file_path}"
            )

            continue

        print(
            f"Loading: {file_path}"
        )

        data = load_json(file_path)

        fiscal_year = get_fiscal_year_from_filename(
            file_path
        )

        if fiscal_year is None:

            print(
                f"WARNING: Could not determine fiscal year "
                f"from {file_path.name}"
            )

            continue

        for company_data in data:

            company = company_data.get("company")

            if not company:

                print(
                    f"WARNING: Missing company "
                    f"in {file_path.name}"
                )

                continue

            metrics = {
                key: value
                for key, value in company_data.items()
                if key != "company"
            }

            record = {
                "company": company,
                "fiscal_year": fiscal_year,
                "metrics": metrics
            }

            combined.append(record)

    # Sort by company and fiscal year
    combined.sort(
        key=lambda x: (
            x["company"],
            int(
                x["fiscal_year"].replace(
                    "FY",
                    ""
                )
            )
        )
    )

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
            combined,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 70)
    print("MULTI-YEAR DATASET CREATED")
    print("=" * 70)

    print(
        f"Total company-year records: "
        f"{len(combined)}"
    )

    print(
        f"Saved to: {OUTPUT_FILE}"
    )

    print()
    print("COMPANY-YEAR COVERAGE")

    for record in combined:

        print(
            f"{record['company']:10} | "
            f"{record['fiscal_year']}"
        )


if __name__ == "__main__":
    main()