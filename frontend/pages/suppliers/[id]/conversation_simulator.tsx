import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import supabase from '../../../lib/supabaseClient';
import Link from 'next/link';

export default function ConversationSimulator() {
  const router = useRouter();
  const { id: supplierId } = router.query;
  const [conversation, setConversation] = useState([]);
  const [reply, setReply] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (supplierId) {
      fetchConversation();
    }
  }, [supplierId]);

  async function fetchConversation() {
    // Fetch conversation turns for this supplier
    setLoading(true);
    const { data, error } = await supabase
      .from('conversation_turns')
      .select('*')
      .eq('conv_id', supplierId)
      .order('sent_at', { ascending: true });
    if (!error) setConversation(data || []);
    setLoading(false);
  }

  async function handleReplySubmit(e: any) {
    e.preventDefault();
    setLoading(true);
    // Insert supplier reply as a new turn
    await supabase.from('conversation_turns').insert({
      conv_id: supplierId,
      role: 'SUPPLIER',
      content: reply,
      sent_at: new Date().toISOString(),
    });
    setReply('');
    // Call agentic DAG API
    await fetch('/api/run_agentic_dag', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ supplier_id: supplierId, conv_id: supplierId, input_event: { type: 'SUPPLIER_REPLY', content: reply } })
    });
    await fetchConversation();
    setLoading(false);
  }

  return (
    <div style={{ maxWidth: 600, margin: '0 auto' }}>
      <h2>Conversation Simulator for Supplier {supplierId}</h2>
      <Link href="/supplier_signin">
        <button style={{ marginBottom: 16 }}>Sign in as a supplier</button>
      </Link>
      <div style={{ border: '1px solid #ccc', padding: 16, borderRadius: 8 }}>
        {loading ? <p>Loading...</p> : (
          <ul>
            {conversation.map((turn: any, idx: number) => (
              <li key={idx} style={{ marginBottom: 12 }}>
                <strong>{turn.role}:</strong> {turn.content}
              </li>
            ))}
          </ul>
        )}
      </div>
      <form onSubmit={handleReplySubmit} style={{ marginTop: 24 }}>
        <textarea
          value={reply}
          onChange={e => setReply(e.target.value)}
          rows={3}
          style={{ width: '100%', marginBottom: 8 }}
          placeholder="Type your reply as supplier..."
        />
        <button type="submit" disabled={loading || !reply}>
          Send Reply
        </button>
      </form>
    </div>
  );
}
