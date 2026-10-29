from typing import List, Dict, Any, Optional
from datetime import datetime
from app.connectors.base import BaseConnector, ConnectorItem


class GitHubConnector(BaseConnector):
    """GitHub connector supporting repositories, markdown documentation, and team permissions."""

    def __init__(self, connector_id: str, name: str, config: Dict[str, Any]):
        super().__init__(connector_id, name, config)
        self._items: Dict[str, ConnectorItem] = {}

    def seed_item(self, item: ConnectorItem):
        self._items[item.source_id] = item

    def list_items(self) -> List[ConnectorItem]:
        return list(self._items.values())

    def fetch_content(self, source_id: str) -> str:
        if source_id in self._items:
            return self._items[source_id].content
        raise KeyError(f"Item {source_id} not found in GitHub connector.")

    def fetch_acl(self, source_id: str) -> List[Dict[str, str]]:
        if source_id in self._items:
            return self._items[source_id].acls
        return []

    def detect_changes(self, since: datetime) -> List[Dict[str, Any]]:
        changes = []
        for s_id, item in self._items.items():
            if item.modified_at and item.modified_at > since:
                changes.append({
                    "event_type": "update",
                    "source_id": s_id,
                    "title": item.title,
                    "modified_at": item.modified_at,
                })
        return changes
