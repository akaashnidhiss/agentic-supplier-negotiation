# Vendor Negotiation Agent (Demo)

**Quickstart**

```bash
pip install -r requirements.txt
cp .env.example .env  # set GEMINI_API_KEY and optionally SENDGRID_API_KEY
python main.py
```

- DEMO mode writes emails to `results/outbox/*.json` and reads demo replies from `demo/simulated_replies.json`.
- Replace `demo/sample_specs.zip` with your own to try different SKUs.
- LLM: defaults to Google Gemini Flash via the free-tier Developer API.
