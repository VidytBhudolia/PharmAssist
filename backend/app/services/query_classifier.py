from crewai import LLM
import json

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    max_tokens=200
)

CLASSIFIER_SYSTEM_PROMPT = """
You are a pharmaceutical AI query classifier.

Your job is to classify the user input into exactly ONE of the following:

1. greeting
   - Any form of greeting, small talk, casual conversation.
   - Examples: "hi", "hello", "good morning", "how are you", "what's up"

2. irrelevant
   - Completely outside medical / pharmaceutical / healthcare domain.
   - Examples: sports, movies, music, food, weather, coding, politics, etc.

3. actionable
   - ANY medical, pharmaceutical, healthcare, biology, disease, drug, clinical, market, patent, or guideline related query.
   - Even vague medical terms like "cancer", "heart disease", "diabetes" are actionable.

Return STRICT JSON only:

For greeting:
{
  "type": "greeting",
  "message": "Warm friendly response",
  "drug": null,
  "indication": null
}

For irrelevant:
{
  "type": "irrelevant",
  "message": "Polite refusal stating pharmaceutical scope",
  "drug": null,
  "indication": null
}

For actionable:
{
  "type": "actionable",
  "message": "",
  "drug": "<drug name or null if not mentioned>",
  "indication": "<disease/indication or null if not mentioned>"
}

Rules:
- Always return valid JSON.
- No markdown.
- No explanations.
- No extra text.
- Only the JSON object.
"""

def classify_query(user_prompt: str) -> dict:
    messages = [
        {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    response = llm.call(messages)
    try:
        return json.loads(response)
    except Exception:
        # Safe fallback (never break pipeline)
        return {
            "type": "actionable",
            "message": "",
            "drug": None,
            "indication": None
        }
