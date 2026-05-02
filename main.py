import os
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from groq import Groq
import stripe

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

app = FastAPI(
    docs_url="/fastapi/docs",
    redoc_url="/fastapi/redoc",
    openapi_url="/fastapi/openapi.json",
)
router = APIRouter(prefix="/fastapi")

client = Groq(api_key=os.environ["GROQ_API_KEY"])

TONE_INSTRUCTIONS = {
    "polite": (
        "Write in a polite, respectful, and courteous tone. "
        "Be warm and considerate throughout."
    ),
    "formal": (
        "Write in a strictly formal, professional tone. "
        "Use formal language, avoid contractions, and maintain a business-letter style."
    ),
    "apologetic": (
        "Write in a deeply apologetic tone. "
        "Express genuine remorse, take full responsibility, and show sincere regret for the actions that led to the ban."
    ),
    "confident": (
        "Write in a confident, assertive tone. "
        "Clearly state your case, highlight your positive history, and make a strong case for reinstatement without being aggressive."
    ),
}


class AppealRequest(BaseModel):
    ban_reason: str
    account_age: float
    tone: Literal["polite", "formal", "apologetic", "confident"] = "polite"


class AppealResponse(BaseModel):
    appeal_text: str
    tone: str


@router.post("/generate-appeal", response_model=AppealResponse)
def generate_appeal(body: AppealRequest) -> AppealResponse:
    tone_instruction = TONE_INSTRUCTIONS[body.tone]

    prompt = (
        f"Write a ban appeal letter for a user.\n\n"
        f"Ban reason: {body.ban_reason}\n"
        f"Account age: {int(body.account_age)} days\n\n"
        f"Tone instruction: {tone_instruction}\n\n"
        f"The letter should be 2-3 paragraphs. It should:\n"
        f"1. Acknowledge the ban reason respectfully\n"
        f"2. Emphasize the user's loyalty given their account age\n"
        f"3. Ask for a second chance\n\n"
        f"Respond with only the appeal letter text, no subject line or extra commentary."
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
        )
        appeal_text = response.choices[0].message.content or ""
        return AppealResponse(appeal_text=appeal_text, tone=body.tone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate appeal: {str(e)}")


@router.get("/", response_class=HTMLResponse)
def index():
    return Path("index.html").read_text()


class PaymentResponse(BaseModel):
    client_secret: str
    amount: int
    currency: str


@router.post("/create-payment", response_model=PaymentResponse)
def create_payment() -> PaymentResponse:
    try:
        intent = stripe.PaymentIntent.create(
            amount=500,
            currency="usd",
            payment_method_types=["card"],
        )
        return PaymentResponse(
            client_secret=intent.client_secret,
            amount=intent.amount,
            currency=intent.currency,
        )
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")


app.include_router(router)
