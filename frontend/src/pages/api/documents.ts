import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    const response = await fetch('http://localhost:8000/documents');
    const data = await response.json();
    res.status(200).json(data);
  } else if (req.method === 'POST') {
    const document = req.body;
    const response = await fetch('http://localhost:8000/documents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(document),
    });
    const data = await response.json();
    res.status(201).json(data);
  } else {
    res.status(405).end();
  }
}
