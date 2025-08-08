import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    // Fetch suppliers from backend
    const response = await fetch('http://localhost:8000/suppliers');
    const data = await response.json();
    res.status(200).json(data);
  } else if (req.method === 'POST') {
    // Create supplier in backend
    const supplier = req.body;
    const response = await fetch('http://localhost:8000/suppliers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(supplier),
    });
    const data = await response.json();
    res.status(201).json(data);
  } else {
    res.status(405).end();
  }
}
