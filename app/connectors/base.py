from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConnectorItem:
    def __init__(
        self,
        id: str,
        title: str,
        content: str,
        source_id: str,
        url: Optional[str] = None,
        path: Optional[str] = None,
        version: str = "1.0",
        sensitivity: str = "internal",
        modified_at: Optional[datetime] = None,
        acls: Optional[List[Dict[str, str]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.title = title
        self.content = content
        self.source_id = source_id
        self.url = url or f"https://source.local/{source_id}"
        self.path = path or f"/{title}"
        self.version = version
        self.sensitivity = sensitivity
        self.modified_at = modified_at or datetime.utcnow()
        self.acls = acls or []
        self.metadata = metadata or {}

    def get_allowed_principals(self) -> List[str]:
        principals = set()
        for acl in self.acls:
            p_type = acl.get("type", "user")
            p_id = acl.get("id", "")
            if p_type == "anyone" or p_id == "anyone" or p_type == "public":
                principals.add("public")
            elif p_type == "domain":
                principals.add(f"domain:{p_id}")
            elif p_type == "group":
                principals.add(f"group:{p_id}")
            elif p_type == "user":
                principals.add(f"user:{p_id}")
            else:
                principals.add(f"{p_type}:{p_id}")
        return sorted(list(principals))


class BaseConnector(ABC):
    def __init__(self, connector_id: str, name: str, config: Dict[str, Any]):
        self.connector_id = connector_id
        self.name = name
        self.config = config

    @abstractmethod
    def list_items(self) -> List[ConnectorItem]:
        """List all discoverable items from the source."""
        pass

    @abstractmethod
    def fetch_content(self, source_id: str) -> str:
        """Fetch raw content for an item."""
        pass

    @abstractmethod
    def fetch_acl(self, source_id: str) -> List[Dict[str, str]]:
        """Fetch current ACL list for an item."""
        pass

    @abstractmethod
    def detect_changes(self, since: datetime) -> List[Dict[str, Any]]:
        """Detect changes, deletions, and ACL modifications since a given timestamp."""
        pass
