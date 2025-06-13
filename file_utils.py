import csv
import os

APPLICATIONS_CSV = "applications.csv"

def save_application_to_csv(application_data):
    file_exists = os.path.isfile(APPLICATIONS_CSV)
    with open(APPLICATIONS_CSV, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email", "phone", "education", "experience", "status"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(application_data)

def load_applications_from_csv():
    if not os.path.isfile(APPLICATIONS_CSV):
        return []
    with open(APPLICATIONS_CSV, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)
