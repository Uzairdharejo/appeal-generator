# Appeal Generator

An AI-powered ban appeal generator built with FastAPI, Groq (Llama 3.3), and Stripe.

Users fill out a short form with their ban reason, account age, and preferred tone — the app charges a small fee via Stripe, then generates a personalised appeal letter using Llama 3.3 70B.

---

## Features

- AI-generated ban appeal letters (Groq / `llama-3.3-70b-versatile`)
- Four tone options: Polite, Formal, Apologetic, Confident
- Stripe payment integration ($5 USD per appeal)
- Clean web UI served directly from the API
- Eval script to batch-score appeal quality

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Uvicorn |
| AI | Groq API — `llama-3.3-70b-versatile` |
| Payments | Stripe Payment Intents |
| Evals | Groq API — `llama-3.1-8b-instant` |
| Container | Docker + Docker Compose |

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/fastapi/` | Web UI |
| `POST` | `/fastapi/create-payment` | Create a Stripe PaymentIntent ($5 USD) |
| `POST` | `/fastapi/generate-appeal` | Generate an AI appeal letter |
| `GET` | `/fastapi/docs` | Interactive Swagger docs |
| `GET` | `/fastapi/redoc` | ReDoc API docs |

### `POST /fastapi/generate-appeal`

**Request body:**
```json
{
  "ban_reason": "Cheating in a ranked match",
  "account_age": 365,
  "tone": "apologetic"
}
```

**Tone options:** `polite` | `formal` | `apologetic` | `confident`

**Response:**
```json
{
  "appeal_text": "Dear Support Team, ...",
  "tone": "apologetic"
}
```

### `POST /fastapi/create-payment`

No request body required. Returns a Stripe `client_secret` for frontend confirmation.

```json
{
  "client_secret": "pi_xxx_secret_xxx",
  "amount": 500,
  "currency": "usd"
}
```

---

## Running Locally

### With Docker (recommended)

```bash
# Clone the repo
git clone https://github.com/Uzairdharejo/appeal-generator.git
cd appeal-generator

# Set environment variables
export GROQ_API_KEY=your_groq_api_key
export STRIPE_SECRET_KEY=your_stripe_secret_key

# Build and run
docker-compose up --build
```

The app will be available at `http://localhost:8000/fastapi/`

### Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_groq_api_key
export STRIPE_SECRET_KEY=your_stripe_secret_key

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key — get one at [console.groq.com](https://console.groq.com) |
| `STRIPE_SECRET_KEY` | Your Stripe secret key — get one at [dashboard.stripe.com](https://dashboard.stripe.com) |

---

## Running Evals

The eval script generates appeal letters for 10 common ban scenarios and scores them using a second Groq model:

```bash
python run_evals.py
```

Results are saved to `evals.json` with a score (1–10) and reasoning for each appeal.

---

## Project Structure

```
appeal-generator/
├── main.py              # FastAPI app — all endpoints
├── index.html           # Frontend UI
├── run_evals.py         # Batch eval script
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container definition
├── docker-compose.yml   # Multi-container orchestration
└── .dockerignore        # Docker build exclusions
```
