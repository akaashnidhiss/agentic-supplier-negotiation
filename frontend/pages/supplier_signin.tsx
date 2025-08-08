import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import supabase from '../lib/supabaseClient';

export default function SupplierSignin() {
  const router = useRouter();
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

  function handleSelectSupplier(supplierId: string) {
    router.push(`/suppliers/${supplierId}/conversation_simulator`);
  }

  return (
    <div style={{ maxWidth: 500, margin: '0 auto' }}>
      <h2>Sign in as a Supplier</h2>
      {loading ? <p>Loading suppliers...</p> : (
        <ul>
          {suppliers.map((supplier: any) => (
            <li key={supplier.id} style={{ marginBottom: 16 }}>
              <button onClick={() => handleSelectSupplier(supplier.id)}>
                {supplier.name}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
