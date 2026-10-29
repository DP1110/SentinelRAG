from typing import List, Dict
from pydantic import BaseModel


class IdentityContext(BaseModel):
    user_id: str
    email: str
    display_name: str
    persona: str
    principals: List[str]


# Built-in Seeded Enterprise Personas
SEEDED_PERSONAS: Dict[str, Dict] = {
    "intern": {
        "user_id": "intern_alice",
        "email": "alice.intern@example.com",
        "display_name": "Alice (Engineering Intern)",
        "groups": ["interns"],
        "principals": [
            "user:intern_alice",
            "user:alice.intern@example.com",
            "group:interns",
            "domain:example.com",
            "public",
        ],
    },
    "engineer": {
        "user_id": "bob_eng",
        "email": "bob.engineer@example.com",
        "display_name": "Bob (Software Engineer)",
        "groups": ["engineering", "employees"],
        "principals": [
            "user:bob_eng",
            "user:bob.engineer@example.com",
            "group:engineering",
            "group:employees",
            "domain:example.com",
            "public",
        ],
    },
    "hr_manager": {
        "user_id": "carol_hr",
        "email": "carol.hr@example.com",
        "display_name": "Carol (HR Director)",
        "groups": ["hr", "employees"],
        "principals": [
            "user:carol_hr",
            "user:carol.hr@example.com",
            "group:hr",
            "group:employees",
            "domain:example.com",
            "public",
        ],
    },
    "finance_analyst": {
        "user_id": "dave_fin",
        "email": "dave.finance@example.com",
        "display_name": "Dave (Financial Analyst)",
        "groups": ["finance", "employees"],
        "principals": [
            "user:dave_fin",
            "user:dave.finance@example.com",
            "group:finance",
            "group:employees",
            "domain:example.com",
            "public",
        ],
    },
    "executive": {
        "user_id": "eve_exec",
        "email": "eve.exec@example.com",
        "display_name": "Eve (Chief Executive Officer)",
        "groups": ["executives", "engineering", "hr", "finance", "employees"],
        "principals": [
            "user:eve_exec",
            "user:eve.exec@example.com",
            "group:executives",
            "group:engineering",
            "group:hr",
            "group:finance",
            "group:employees",
            "domain:example.com",
            "public",
        ],
    },
}
