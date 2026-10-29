from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.core.identity import IdentityContext
from app.agent.tools import (
    tool_search_knowledge,
    tool_get_document,
    tool_summarize_document,
    tool_create_ticket,
)
from app.core.config import settings


class AgentRunner:
    """
    Executes tool-calling agent tasks under user identity context.
    Enforces step limit and permission boundaries.
    """

    def __init__(self, db: Session, max_steps: int = settings.MAX_AGENT_STEPS):
        self.db = db
        self.max_steps = max_steps

    def run(
        self,
        instruction: str,
        identity: IdentityContext,
        confirmed_write: bool = False,
    ) -> Dict[str, Any]:
        steps_executed = 0
        trace = []

        instruction_lower = instruction.lower()

        # Step 1: Detect intended tool
        if "ticket" in instruction_lower or "issue" in instruction_lower:
            steps_executed += 1
            result = tool_create_ticket(
                title=instruction[:50],
                description=instruction,
                confirmed=confirmed_write,
                identity=identity,
            )
            trace.append({"step": 1, "tool": "create_ticket", "output": result})
            final_answer = result

        elif "get" in instruction_lower or "read" in instruction_lower or "fetch" in instruction_lower:
            steps_executed += 1
            # Extract doc_id from instruction if present
            words = instruction.split()
            target_doc = words[-1] if words else "unknown"
            result = tool_get_document(target_doc, identity, self.db)
            trace.append({"step": 1, "tool": "get_document", "output": result})
            final_answer = result

        elif "summarize" in instruction_lower:
            steps_executed += 1
            words = instruction.split()
            target_doc = words[-1] if words else "unknown"
            result = tool_summarize_document(target_doc, identity, self.db)
            trace.append({"step": 1, "tool": "summarize_document", "output": result})
            final_answer = result

        else:
            steps_executed += 1
            result = tool_search_knowledge(instruction, identity, self.db)
            trace.append({"step": 1, "tool": "search_knowledge", "output": result})
            final_answer = result

        return {
            "instruction": instruction,
            "steps_count": steps_executed,
            "final_answer": final_answer,
            "trace": trace,
            "identity_used": identity.user_id,
        }
