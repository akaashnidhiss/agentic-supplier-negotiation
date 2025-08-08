// frontend/pages/api/run_agentic_dag.ts
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  // Proxy to FastAPI backend
  const backendUrl = 'http://localhost:8000/run_agentic_dag'; // Update if your backend runs elsewhere
  const response = await fetch(backendUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req.body),
  });
  const data = await response.json();
  res.status(response.status).json(data);
}