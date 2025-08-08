import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

const SupplierPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const [supplier, setSupplier] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [conversations, setConversations] = useState<any[]>([]);

  useEffect(() => {
    if (id) {
      fetch(`/api/suppliers?id=${id}`)
        .then(res => res.json())
        .then(data => setSupplier(data[0]));
      fetch(`/api/documents?supplier_id=${id}`)
        .then(res => res.json())
        .then(setDocuments);
      fetch(`/api/conversations?supplier_id=${id}`)
        .then(res => res.json())
        .then(setConversations);
    }
  }, [id]);

  if (!supplier) return <div>Loading...</div>;

  return (
    <main style={{ maxWidth: 800, margin: '0 auto', padding: 24 }}>
      <div style={{ textAlign: 'center', marginBottom: 24 }}>
        {/* Placeholder for supplier logo */}
        <div style={{ width: 120, height: 120, margin: '0 auto', background: '#eee', borderRadius: '50%' }}>
          <span style={{ fontSize: 48, lineHeight: '120px' }}>🏢</span>
        </div>
        <h2>{supplier.name}</h2>
      </div>
      <section style={{ marginBottom: 24 }}>
        <h3>Supplier Summary</h3>
        <div style={{ background: '#f9f9f9', padding: 16, borderRadius: 8 }}>{supplier.summary || 'No summary yet.'}</div>
      </section>
      <section style={{ marginBottom: 24 }}>
        <h3>Documents</h3>
        <ul>
          {documents.map(doc => (
            <li key={doc.id}>{doc.doc_type} - {doc.version} ({doc.date})</li>
          ))}
        </ul>
      </section>
      <section>
        <h3>Conversation Trace</h3>
        <ul>
          {conversations.map(conv => (
            <li key={conv.id}>
              <div><strong>State:</strong> {conv.state}</div>
              <div><strong>Last Updated:</strong> {conv.last_updated}</div>
              <div><strong>Messages:</strong>
                <ul>
                  {conv.messages.map((msg: any, idx: number) => (
                    <li key={idx}><strong>{msg.role}:</strong> {msg.content}</li>
                  ))}
                </ul>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
};

export default SupplierPage;
