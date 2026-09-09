import json
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).parent.parent / "data" / "crm_data.json"


def load_data() -> dict[str, Any]:
    """Load the mock CRM dataset."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data: dict[str, Any]) -> None:
    """Save changes to the mock CRM dataset."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def search_leads(query: str) -> list[dict[str, Any]]:
    """
    Ask tool:
    Search leads by name, company, email, interest, or status.
    """
    data = load_data()
    query = query.lower().strip()

    results = []

    for lead in data["leads"]:
        searchable_text = " ".join(
            [
                lead["id"],
                lead["name"],
                lead["company"],
                lead["email"],
                lead["interest"],
                lead["status"],
            ]
        ).lower()

        if query in searchable_text:
            results.append(lead)

    return results


def get_insights() -> dict[str, Any]:
    """
    Ask tool:
    Return computed CRM statistics.
    """
    data = load_data()

    leads = data["leads"]
    tasks = data["tasks"]

    status_counts = {}

    for lead in leads:
        status = lead["status"]
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "total_leads": len(leads),
        "lead_status_counts": status_counts,
        "total_tasks": len(tasks),
        "pending_tasks": sum(
            1 for task in tasks if task["status"] == "pending"
        ),
    }


def create_task(
    title: str,
    due: str,
    related_to: str | None = None,
) -> dict[str, Any]:
    """
    Run tool:
    Create a new CRM task.

    IMPORTANT:
    This function should only be called AFTER the user
    explicitly confirms the proposed action.
    """
    data = load_data()

    new_id = f"T{len(data['tasks']) + 1:03d}"

    new_task = {
        "id": new_id,
        "title": title,
        "due": due,
        "related_to": related_to,
        "status": "pending",
    }

    data["tasks"].append(new_task)
    save_data(data)

    return new_task