import React, { useEffect, useState } from 'react';
import Link from 'next/link';

const Dashboard = () => {
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [newSupplier, setNewSupplier] = useState({ name: '', contact_email: '', status: 'OPEN' });
  const [documents, setDocuments] = useState<any[]>([]);
  const [newDocument, setNewDocument] = useState({ supplier_id: '', doc_type: '', version: '', date: '', summary: '', file_url: '' });
  const [conversations, setConversations] = useState<any[]>([]);
  const [newConversation, setNewConversation] = useState({ supplier_id: '', state: 'OPEN', messages: [], last_updated: '' });
  const [evaluations, setEvaluations] = useState<any[]>([]);
  const [newEvaluation, setNewEvaluation] = useState({ conv_id: '', turn_id: '', judge_prompt_version: '', scores_json: {}, comments: '', created_at: '' });

  useEffect(() => {
    fetch('/api/suppliers').then(res => res.json()).then(data => setSuppliers(Array.isArray(data) ? data : []));
    fetch('/api/documents').then(res => res.json()).then(data => setDocuments(Array.isArray(data) ? data : []));
    fetch('/api/conversations').then(res => res.json()).then(data => setConversations(Array.isArray(data) ? data : []));
    fetch('/api/evaluations').then(res => res.json()).then(data => setEvaluations(Array.isArray(data) ? data : []));
  }, []);

  // Supplier creation
  const handleSupplierCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/suppliers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSupplier),
    });
    setNewSupplier({ name: '', contact_email: '', status: 'OPEN' });
    fetch('/api/suppliers').then(res => res.json()).then(setSuppliers);
  };

  // Document creation
  const handleDocumentCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/documents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newDocument),
    });
    setNewDocument({ supplier_id: '', doc_type: '', version: '', date: '', summary: '', file_url: '' });
    fetch('/api/documents').then(res => res.json()).then(setDocuments);
  };

  // Conversation creation
  const handleConversationCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newConversation),
    });
    setNewConversation({ supplier_id: '', state: 'OPEN', messages: [], last_updated: '' });
    fetch('/api/conversations').then(res => res.json()).then(setConversations);
  };

  // Evaluation creation
  const handleEvaluationCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch('/api/evaluations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newEvaluation),
    });
    setNewEvaluation({ conv_id: '', turn_id: '', judge_prompt_version: '', scores_json: {}, comments: '', created_at: '' });
    fetch('/api/evaluations').then(res => res.json()).then(setEvaluations);
  };

  return (
    <main style={{ maxWidth: 1000, margin: '0 auto', padding: 24 }}>
      <h1>Supplier Dashboard</h1>
      <section style={{ marginBottom: 32 }}>
        <h2>Suppliers</h2>
        <form onSubmit={handleSupplierCreate} style={{ marginBottom: 16 }}>
          <input placeholder="Name" value={newSupplier.name} onChange={e => setNewSupplier({ ...newSupplier, name: e.target.value })} required />
          <input placeholder="Contact Email" value={newSupplier.contact_email} onChange={e => setNewSupplier({ ...newSupplier, contact_email: e.target.value })} required />
          <button type="submit">Add Supplier</button>
        </form>
        <table border={1} cellPadding={8} style={{ width: '100%' }}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Contact Email</th>
              <th>Status</th>
              <th>Last Contact</th>
              <th>Evaluation Avg</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(suppliers) && suppliers.map(supplier => (
              <tr key={supplier.id}>
                <td>{supplier.name}</td>
                <td>{supplier.contact_email}</td>
                <td>{supplier.status}</td>
                <td>{supplier.last_contact}</td>
                <td>{supplier.evaluation_average}</td>
                <td>
                  <Link href={`/suppliers/${supplier.id}`}>View</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section style={{ marginBottom: 32 }}>
        <h2>Documents</h2>
        <form onSubmit={handleDocumentCreate} style={{ marginBottom: 16 }}>
          <input placeholder="Supplier ID" value={newDocument.supplier_id} onChange={e => setNewDocument({ ...newDocument, supplier_id: e.target.value })} />
          <input placeholder="Doc Type" value={newDocument.doc_type} onChange={e => setNewDocument({ ...newDocument, doc_type: e.target.value })} />
          <input placeholder="Version" value={newDocument.version} onChange={e => setNewDocument({ ...newDocument, version: e.target.value })} />
          <input placeholder="Date" value={newDocument.date} onChange={e => setNewDocument({ ...newDocument, date: e.target.value })} />
          <input placeholder="Summary" value={newDocument.summary} onChange={e => setNewDocument({ ...newDocument, summary: e.target.value })} />
          <input placeholder="File URL" value={newDocument.file_url} onChange={e => setNewDocument({ ...newDocument, file_url: e.target.value })} />
          <button type="submit">Add Document</button>
        </form>
        <table border={1} cellPadding={8} style={{ width: '100%' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Supplier ID</th>
              <th>Type</th>
              <th>Version</th>
              <th>Date</th>
              <th>Summary</th>
              <th>File URL</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(documents) && documents.map(doc => (
              <tr key={doc.id}>
                <td>{doc.id}</td>
                <td>{doc.supplier_id}</td>
                <td>{doc.doc_type}</td>
                <td>{doc.version}</td>
                <td>{doc.date}</td>
                <td>{doc.summary}</td>
                <td>{doc.file_url}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section style={{ marginBottom: 32 }}>
        <h2>Conversations</h2>
        <form onSubmit={handleConversationCreate} style={{ marginBottom: 16 }}>
          <input placeholder="Supplier ID" value={newConversation.supplier_id} onChange={e => setNewConversation({ ...newConversation, supplier_id: e.target.value })} />
          <input placeholder="State" value={newConversation.state} onChange={e => setNewConversation({ ...newConversation, state: e.target.value })} />
          <input placeholder="Last Updated" value={newConversation.last_updated} onChange={e => setNewConversation({ ...newConversation, last_updated: e.target.value })} />
          <button type="submit">Add Conversation</button>
        </form>
        <table border={1} cellPadding={8} style={{ width: '100%' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Supplier ID</th>
              <th>State</th>
              <th>Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(conversations) && conversations.map(conv => (
              <tr key={conv.id}>
                <td>{conv.id}</td>
                <td>{conv.supplier_id}</td>
                <td>{conv.state}</td>
                <td>{conv.last_updated}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section>
        <h2>Evaluations</h2>
        <form onSubmit={handleEvaluationCreate} style={{ marginBottom: 16 }}>
          <input placeholder="Conversation ID" value={newEvaluation.conv_id} onChange={e => setNewEvaluation({ ...newEvaluation, conv_id: e.target.value })} />
          <input placeholder="Turn ID" value={newEvaluation.turn_id} onChange={e => setNewEvaluation({ ...newEvaluation, turn_id: e.target.value })} />
          <input placeholder="Prompt Version" value={newEvaluation.judge_prompt_version} onChange={e => setNewEvaluation({ ...newEvaluation, judge_prompt_version: e.target.value })} />
          <input placeholder="Comments" value={newEvaluation.comments} onChange={e => setNewEvaluation({ ...newEvaluation, comments: e.target.value })} />
          <input placeholder="Created At" value={newEvaluation.created_at} onChange={e => setNewEvaluation({ ...newEvaluation, created_at: e.target.value })} />
          <button type="submit">Add Evaluation</button>
        </form>
        <table border={1} cellPadding={8} style={{ width: '100%' }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Conversation ID</th>
              <th>Turn ID</th>
              <th>Prompt Version</th>
              <th>Comments</th>
              <th>Created At</th>
            </tr>
          </thead>
          <tbody>
            {Array.isArray(evaluations) && evaluations.map(evalItem => (
              <tr key={evalItem.id}>
                <td>{evalItem.id}</td>
                <td>{evalItem.conv_id}</td>
                <td>{evalItem.turn_id}</td>
                <td>{evalItem.judge_prompt_version}</td>
                <td>{evalItem.comments}</td>
                <td>{evalItem.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
};

export default Dashboard;
