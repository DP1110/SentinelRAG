import pytest
from app.api.auth import SEEDED_PERSONAS, IdentityContext
from app.agent.runner import AgentRunner


def test_agent_enforces_user_permissions(db_session):
    intern_info = SEEDED_PERSONAS["intern"]
    intern_id = IdentityContext(
        user_id=intern_info["user_id"],
        email=intern_info["email"],
        display_name=intern_info["display_name"],
        persona="intern",
        principals=intern_info["principals"],
    )

    runner = AgentRunner(db=db_session)
    # Intern asks agent to read restricted executive board document
    res = runner.run("get document gdrive_main_exec_001", intern_id)
    assert "Access denied" in res["final_answer"]


def test_agent_write_action_requires_confirmation(db_session):
    eng_info = SEEDED_PERSONAS["engineer"]
    eng_id = IdentityContext(
        user_id=eng_info["user_id"],
        email=eng_info["email"],
        display_name=eng_info["display_name"],
        persona="engineer",
        principals=eng_info["principals"],
    )

    runner = AgentRunner(db=db_session)
    # Without confirmation
    unconfirmed = runner.run("create ticket Fix memory leak in auth service", eng_id, confirmed_write=False)
    assert "Confirmation required" in unconfirmed["final_answer"]

    # With confirmation
    confirmed = runner.run("create ticket Fix memory leak in auth service", eng_id, confirmed_write=True)
    assert "Ticket created successfully" in confirmed["final_answer"]
