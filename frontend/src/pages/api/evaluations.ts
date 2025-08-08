import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    const response = await fetch('http://localhost:8000/evaluations');
    const data = await response.json();
    res.status(200).json(data);
  } else if (req.method === 'POST') {
    const evaluation = req.body;
    const response = await fetch('http://localhost:8000/evaluations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(evaluation),
    });
    const data = await response.json();
    res.status(201).json(data);
  } else {
    res.status(405).end();
  }
}
