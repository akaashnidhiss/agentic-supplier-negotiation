"""
mem0 Adapter Functions
"""
from typing import Any, Dict, List
from datetime import datetime

class Mem0Adapter:
    def __init__(self, supabase_client):
        self.supabase_client = supabase_client

    def read_short_term(self, run_id: str) -> Dict[str, Any]:
        """
        Read short-term scratchpad for a run.
        """
        # Placeholder logic
        return {"plan": "Sample plan", "tool_outputs": "Sample outputs"}

    def write_short_term(self, run_id: str, data: Dict[str, Any]):
        """
        Write to short-term scratchpad.
        """
        # Placeholder logic
        pass

    def read_episodic(self, conv_id: str) -> List[Dict[str, Any]]:
        """
        Read episodic memory (conversation turns) from Supabase.
        """
        response = self.supabase_client.table('conversation_turns').select('*').eq('conv_id', conv_id).order('sent_at').execute()
        return response.data if response.data else []

    def write_episodic(self, conv_id: str, turn: Dict[str, Any], supplier_id: str = None):
        """
        Write a turn to episodic memory (Supabase conversation_turns table).
        Ensures the conversation exists in supplier_conversations.
        """
        # Check if conversation exists
        response = self.supabase_client.table('supplier_conversations').select('id').eq('id', conv_id).execute()
        if not response.data:
            # Create new conversation if not exists
            if supplier_id is None:
                raise ValueError("supplier_id required to create new conversation")
            conv_resp = self.supabase_client.table('supplier_conversations').insert({
                'id': conv_id,
                'supplier_id': supplier_id,
                'state': 'OPEN',
                'conversation_turns': [],
                'last_updated': datetime.utcnow().isoformat()
            }).execute()
        self.supabase_client.table('conversation_turns').insert({
            'conv_id': conv_id,
            'role': turn.get('role'),
            'content': turn.get('content'),
            'sent_at': turn.get('sent_at') or datetime.utcnow().isoformat(),
            'meta': turn.get('meta')
        }).execute()

    def read_semantic(self, supplier_id: str) -> List[Dict[str, Any]]:
        """
        Read semantic store (vector search results).
        """
        # Placeholder logic
        return [{"doc_id": "123", "summary": "Contract details"}]

    def write_semantic(self, supplier_id: str, embedding: Any):
        """
        Write new embedding to semantic store.
        """
        # Placeholder logic
        pass
