import { useState, useEffect } from 'react';
import Link from 'next/link';
import supabase from '../lib/supabaseClient';

export default function Dashboard() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSuppliers();
  }, []);

  async function fetchSuppliers() {
    const { data, error } = await supabase.from('suppliers_table').select('*');
    if (!error) setSuppliers(data || []);
    setLoading(false);
  }

  return (
    <div style={{ maxWidth: 700, margin: '0 auto' }}>
      <h1>Supplier Dashboard</h1>
      <Link href="/supplier_signin">
        <button style={{ marginBottom: 24 }}>Sign in as a supplier</button>
      </Link>
      {loading ? <p>Loading suppliers...</p> : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left' }}>Name</th>
              <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left' }}>Status</th>
              <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left' }}>Last Contact</th>
              <th style={{ borderBottom: '1px solid #ccc', textAlign: 'left' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((supplier: any) => (
              <tr key={supplier.id}>
                <td>{supplier.name}</td>
                <td>{supplier.status}</td>
                <td>{supplier.last_contact || '-'}</td>
                <td>
                  <Link href={`/suppliers/${supplier.id}/conversation_simulator`}>
                    <button>Open Conversation</button>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
