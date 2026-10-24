import json


def write_json_report(page_data, filename="report.json"):
    # 1. Convert page_data.values() to a list sorted by URL
    pages = sorted(page_data.values(), key=lambda p: p["url"])

    # 2. Write the sorted list to a JSON file formatted with 2-space indentation
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(pages, f, indent=2)
