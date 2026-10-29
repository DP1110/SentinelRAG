from typing import List, Set, Optional, Dict
from fastapi import Header, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, Group, GroupMember
from app.core.identity import IdentityContext, SEEDED_PERSONAS


def resolve_principals_for_user(user: User, db: Session) -> List[str]:
    principals = {
        f"user:{user.id}",
        f"user:{user.email}",
        "public",
    }
    if "@" in user.email:
        domain = user.email.split("@")[1]
        principals.add(f"domain:{domain}")

    memberships = db.query(GroupMember).filter(GroupMember.user_id == user.id).all()
    for m in memberships:
        if m.group:
            principals.add(f"group:{m.group.name}")

    return sorted(list(principals))


def get_current_identity(
    x_persona: Optional[str] = Header(None, alias="X-Persona"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> IdentityContext:
    # 1. Check for seeded persona header (convenient for UI, CLI, Red-Team harness)
    if x_persona:
        persona_key = x_persona.lower().strip()
        if persona_key in SEEDED_PERSONAS:
            info = SEEDED_PERSONAS[persona_key]
            effective_user_id = x_user_id if isinstance(x_user_id, str) and x_user_id else info["user_id"]
            effective_principals = list(info["principals"])
            if isinstance(x_user_id, str) and x_user_id:
                effective_principals = [f"user:{x_user_id}"] + [p for p in effective_principals if not p.startswith("user:")]
            return IdentityContext(
                user_id=effective_user_id,
                email=f"{effective_user_id}@example.com" if (isinstance(x_user_id, str) and x_user_id) else info["email"],
                display_name=info["display_name"],
                persona=persona_key,
                principals=effective_principals,
            )

    # 2. Check for Bearer token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1].strip()
        # If token matches persona name
        if token.lower() in SEEDED_PERSONAS:
            info = SEEDED_PERSONAS[token.lower()]
            return IdentityContext(
                user_id=info["user_id"],
                email=info["email"],
                display_name=info["display_name"],
                persona=token.lower(),
                principals=info["principals"],
            )
        # Check DB by user ID or email
        user = db.query(User).filter((User.id == token) | (User.email == token)).first()
        if user:
            principals = resolve_principals_for_user(user, db)
            return IdentityContext(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
                persona="custom",
                principals=principals,
            )

    # 3. Reject unauthenticated queries (Fail-closed authentication - FR-3)
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide 'X-Persona' or 'Authorization: Bearer <token>' header.",
    )
