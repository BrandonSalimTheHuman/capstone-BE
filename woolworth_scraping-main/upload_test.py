import csv
import json
from db_upload import upload_products  # Assuming your function is in db_upload.py


def test_upload_from_csv(csv_file_path: str):
    products = []

    print(f"Reading data from {csv_file_path}...")

    with open(csv_file_path, mode="r", encoding="utf-8") as f:
        # csv.DictReader automatically uses the first row as dictionary keys
        reader = csv.DictReader(f)

        for row in reader:
            # Clean up trailing/leading whitespaces from the CSV data
            cleaned_row = {key.strip(): val.strip() for key, val in row.items()}
            products.append(cleaned_row)

    print(f"Successfully converted CSV to list. Found {len(products)} items.")

    # Run your upload function with the mock data
    try:
        print("Starting test database upload...")
        upload_products(products, "IGA")
    except Exception as e:
        print(f"\n[ERROR] Upload failed: {e}")
        raise


if __name__ == "__main__":
    # Replace with the actual path to your CSV file
    CSV_PATH = "iga_test.csv"
    test_upload_from_csv(CSV_PATH)