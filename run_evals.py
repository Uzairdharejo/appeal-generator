import json
import os
import urllib.request
import urllib.error
from groq import Groq

APPEAL_URL = "http://localhost:8000/fastapi/generate-appeal"
ACCOUNT_AGE_DAYS = 730  # 2 years

BAN_REASONS = [
    "Spam",
    "Impersonation",
    "Fake Account",
    "Copyright",
    "Hate Speech",
    "Nudity",
    "Violence",
    "Bullying",
    "Misinformation",
    "Hacked Account",
]

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def generate_appeal(ban_reason: str, account_age: int) -> str:
    payload = json.dumps({"ban_reason": ban_reason, "account_age": account_age}).encode()
    req = urllib.request.Request(
        APPEAL_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["appeal_text"]


def score_appeal(appeal_text: str) -> dict:
    prompt = f"""Score the following ban appeal letter on three criteria. 
Return ONLY a valid JSON object with integer scores from 1 to 5, like:
{{"tone": 4, "length": 3, "persuasiveness": 5}}

Scoring guide:
- tone: 1=rude/inappropriate, 3=neutral, 5=perfectly respectful and professional
- length: 1=too short or too long, 3=acceptable, 5=ideal length for an appeal
- persuasiveness: 1=unconvincing, 3=somewhat convincing, 5=highly convincing

Appeal letter:
{appeal_text}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=64,
    )
    raw = response.choices[0].message.content or ""
    # Extract JSON from response
    start = raw.find("{")
    end = raw.rfind("}") + 1
    scores = json.loads(raw[start:end])
    return {
        "tone": int(scores["tone"]),
        "length": int(scores["length"]),
        "persuasiveness": int(scores["persuasiveness"]),
        "average": round((scores["tone"] + scores["length"] + scores["persuasiveness"]) / 3, 2),
    }


results = []

for reason in BAN_REASONS:
    print(f"Processing: {reason}")
    try:
        appeal_text = generate_appeal(reason, ACCOUNT_AGE_DAYS)
        print(f"  Appeal generated ({len(appeal_text)} chars)")
    except Exception as e:
        print(f"  ERROR generating appeal: {e}")
        results.append({"ban_reason": reason, "account_age": ACCOUNT_AGE_DAYS, "error": str(e)})
        continue

    try:
        scores = score_appeal(appeal_text)
        print(f"  Scores → tone: {scores['tone']}, length: {scores['length']}, persuasiveness: {scores['persuasiveness']}, avg: {scores['average']}")
    except Exception as e:
        print(f"  ERROR scoring appeal: {e}")
        scores = {"error": str(e)}

    results.append({
        "ban_reason": reason,
        "account_age": ACCOUNT_AGE_DAYS,
        "appeal_text": appeal_text,
        "scores": scores,
    })

with open("evals.json", "w") as f:
    json.dump(results, f, indent=2)

# Compute overall averages
scored = [r for r in results if "scores" in r and "average" in r["scores"]]
if scored:
    avg_tone = round(sum(r["scores"]["tone"] for r in scored) / len(scored), 2)
    avg_length = round(sum(r["scores"]["length"] for r in scored) / len(scored), 2)
    avg_persuasiveness = round(sum(r["scores"]["persuasiveness"] for r in scored) / len(scored), 2)
    avg_overall = round(sum(r["scores"]["average"] for r in scored) / len(scored), 2)

    print(f"\n{'='*40}")
    print(f"RESULTS ({len(scored)}/{len(results)} appeals scored)")
    print(f"{'='*40}")
    print(f"  Tone:             {avg_tone} / 5")
    print(f"  Length:           {avg_length} / 5")
    print(f"  Persuasiveness:   {avg_persuasiveness} / 5")
    print(f"  Overall average:  {avg_overall} / 5")
    print(f"{'='*40}")

print(f"\nSaved to evals.json")
