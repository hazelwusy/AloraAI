import json
from collections import Counter
from pathlib import Path


GROUPS = {
    "Gynecology": Path("output/gynecology/fhir"),
    "Chronic pain": Path("output/chronic_pain/fhir"),
    "Psychiatry": Path("output/psychiatry/fhir"),
}


def get_patient_name(resource: dict) -> str:
    names = resource.get("name", [])

    if not names:
        return "Unknown patient"

    name = names[0]
    given = " ".join(name.get("given", []))
    family = name.get("family", "")

    return f"{given} {family}".strip()


for group_name, folder in GROUPS.items():
    print(f"\n{'=' * 60}")
    print(group_name)
    print("=" * 60)

    files = sorted(folder.glob("*.json"))

    print(f"FHIR files found: {len(files)}")

    for index, file_path in enumerate(files, start=1):
        with file_path.open("r", encoding="utf-8") as file:
            bundle = json.load(file)

        resources = [
            entry.get("resource", {})
            for entry in bundle.get("entry", [])
        ]

        patient = next(
            (
                resource
                for resource in resources
                if resource.get("resourceType") == "Patient"
            ),
            {},
        )

        resource_counts = Counter(
            resource.get("resourceType", "Unknown")
            for resource in resources
        )

        print(f"\nPatient {index}: {get_patient_name(patient)}")
        print(f"Gender: {patient.get('gender', 'Unknown')}")
        print(f"Birth date: {patient.get('birthDate', 'Unknown')}")
        print(f"File: {file_path.name}")

        important_types = [
            "Condition",
            "Encounter",
            "MedicationRequest",
            "Observation",
            "Procedure",
            "CarePlan",
        ]

        for resource_type in important_types:
            print(
                f"  {resource_type}: "
                f"{resource_counts.get(resource_type, 0)}"
            )