import anthropic
import os
from sqlalchemy.orm import Session
from models.ambulance import Ambulance
from models.hospital import Hospital
from models.incident import Incident


def get_system_snapshot(db: Session) -> str:
    """Build a text summary of current system state to give Claude context."""
    ambulances = db.query(Ambulance).filter(Ambulance.is_active == True).all()
    hospitals = db.query(Hospital).all()
    incidents = db.query(Incident).filter(Incident.status == "active").all()

    snapshot = []

    snapshot.append("=== CURRENT SYSTEM STATE ===\n")

    snapshot.append("AMBULANCES:")
    for a in ambulances:
        snapshot.append(f"  - {a.name}: status={a.status}, equipment={a.equipment}, location=({a.latitude}, {a.longitude})")

    snapshot.append("\nHOSPITALS:")
    for h in hospitals:
        load = round((1 - h.available_beds / h.total_beds) * 100)
        snapshot.append(f"  - {h.name}: trauma_level={h.trauma_level}, available_beds={h.available_beds}/{h.total_beds} ({load}% full), location=({h.latitude}, {h.longitude})")

    snapshot.append("\nACTIVE INCIDENTS:")
    for i in incidents:
        snapshot.append(f"  - Incident #{i.id}: type={i.type}, severity={i.severity}, status={i.status}, location=({i.latitude}, {i.longitude}), description={i.description}")

    snapshot.append("\n=== END SYSTEM STATE ===")
    return "\n".join(snapshot)


def ask_ai_assistant(question: str, db: Session) -> str:
    """Send dispatcher question + system context to Claude and return answer."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    system_snapshot = get_system_snapshot(db)

    system_prompt = """You are an AI operations assistant for ResQOps, an emergency response operating system.

You have access to real-time data about ambulances, hospitals, and active incidents.
Your job is to help dispatchers make fast, informed decisions.

Rules:
- Be concise and direct — dispatchers are under pressure
- Always base answers on the actual system data provided
- If recommending an action, explain why briefly
- Flag any critical risks you notice
- Use plain language, no jargon
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"{system_snapshot}\n\nDispatcher question: {question}"
            }
        ]
    )

    return message.content[0].text