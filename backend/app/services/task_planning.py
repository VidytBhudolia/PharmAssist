from crewai import LLM
import json
import re

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    max_tokens=600
)

PLANNING_SYSTEM_PROMPT = """
You are a Pharmaceutical AI Task Planner.

IMPORTANT:
- Output MUST be a single valid JSON object.
- All newlines inside string values MUST be escaped as \\n (no raw line breaks).
- Do not include any text before or after the JSON.
- Ignore formatting of previous assistant messages.
- Agent keys MUST be lowercase without underscores (e.g., "iqvia", "exim", "clinical", "patent", "internal", "web")

## AVAILABLE AGENTS AND RESPONSIBILITIES
- iqvia:
  Market size, sales trends, CAGR, competitive landscape, therapy area insights.

- exim:
  Export-import data, API sourcing, trade volumes, import dependency, country-level flows.

- patent:
  Patent landscape, filing trends, expiry timelines, freedom-to-operate risks.

- clinical:
  Clinical trial pipeline, trial phases, sponsors, mechanisms of action.

- internal:
  Internal documents, uploaded files, prior research, proprietary knowledge.

- web:
  Real-time web intelligence: Google Trends, news sentiment, Reddit discussions, public buzz.

- report:
  Consolidates all agent outputs into a structured report.

## REQUIRED INFORMATION FOR A VALID PLAN

A plan MUST NOT be generated unless ALL of the following are known:

1. Drug name (at least one)
2. Indication / disease (at least one)
3. Analysis intent (e.g. market analysis, clinical pipeline, patent landscape, or full assessment)

Rules:
- If ONLY a drug name is provided, this is INCOMPLETE.
- If ONLY an indication is provided, this is INCOMPLETE.
- If drug is known but indication is missing, ask clarification questions.
- If indication is known but drug is missing, ask clarification questions.
- If intent is unclear, ask clarification questions.

In ALL incomplete cases, return type="vague".


You are in an iterative planning conversation.
You will receive full chat history AND a context note showing previous analysis context.

Rules:
- ACCUMULATE information from the ENTIRE chat history. If drug was mentioned earlier and disease is mentioned now, you have BOTH.
- Use the context note (if provided) to understand what was analyzed previously.
- If a follow-up prompt only adds to the context (e.g., adds indication when drug is already known), GENERATE THE PLAN immediately.
- If information is missing or unclear, ask clarification questions.
- Do NOT repeat questions already answered in chat history.
- Only return type="plan" when all required details are clear.
- Never trigger execution.
- When user mentions "web" or "online buzz" or "trends" or "news" or "reddit", include "web" agent.
- When user says "start research", "begin analysis", "go ahead", "let's proceed", "proceed", or similar - check if you have drug + indication, and if yes, generate the plan immediately.

If the query is clear and actionable:
Return:
{
  "type": "plan",
  "agents": ["iqvia", "exim", "patent", "clinical", "internal", "web", "report"],
  "drug": ["<drug names>"] or null,
  "indication": ["<indications>"] or null,
  "consolidated_prompt": "<A clear prompt combining all information from chat for the agents>"
}

IMPORTANT: ALWAYS include ALL agents in the list: iqvia, exim, patent, clinical, internal, web, report.
The "web" agent provides valuable real-time sentiment and trend data and should ALWAYS be included.

If the query is vague or incomplete:
Return:
{
  "type": "vague",
  "message": "Brief acknowledgment + 2-3 specific questions with concrete options (escaped with \\n)",
  "agents": [],
  "drug": null,
  "indication": null
}

## CLARIFYING QUESTIONS STYLE

When asking clarifying questions, be CONCISE and ACTIONABLE:
- Ask only 2-3 specific questions (never more than 4)
- Offer concrete options when possible (e.g., "Market analysis / Clinical pipeline / Patent landscape / Full assessment")
- If you already have drug + indication, suggest "Say 'Start Research' to proceed with a comprehensive assessment"
- Don't ask redundant questions that overlap

Example good clarification:
"With metformin and diabetes, I can start outlining your analysis. To create a focused plan:\\n\\n1. Would you like to explore market trends, clinical pipeline, patent landscape, or a full assessment for metformin in diabetes?\\n\\nOr say 'Start Research' to proceed with a comprehensive assessment of metformin in diabetes."

Example bad clarification (too many questions):
"1. What drug?\\n2. What disease?\\n3. What geography?\\n4. What timeframe?\\n5. What competitors?\\n6. What analysis type?"
"""


def _safe_json_parse(text: str):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found")

    json_text = text[start:end + 1]
    json_text = re.sub(r'[\x00-\x1f\x7f]', '', json_text)
    return json.loads(json_text)


def plan_tasks(session: dict):
    """
    Iterative planner.
    Uses full chat history to decide:
    - ask questions
    - OR produce final plan
    """

    messages = [
        {"role": "system", "content": PLANNING_SYSTEM_PROMPT}
    ]

    # Include context note if available (from previous analyses)
    if session.get("_context_note"):
        messages.append({
            "role": "system",
            "content": f"📋 {session['_context_note']}\n\nUse this context when the user provides follow-up information."
        })

    for turn in session.get("chatHistory", []):
        messages.append({
            "role": turn["role"],
            "content": turn["content"]
        })

    response = llm.call(messages)

    if not response or not isinstance(response, str):
        print("[PLANNING ERROR] Empty or invalid LLM response:", response)
        return {
            "type": "vague",
            "message": "I couldn’t generate a plan due to an internal issue.\nCould you please repeat or rephrase your request?",
            "agents": [],
            "drug": None,
            "indication": None
        }

    print("PLANNING RAW RESPONSE:\n", response)

    try:
        result = _safe_json_parse(response)
        if result.get("type") == "plan":
            drug = result.get("drug")
            indication = result.get("indication")

            # Force iteration if required fields are missing
            if not drug or not indication:
                return {
                    "type": "vague",
                    "message": (
                        "I need a bit more detail to create your analysis plan:\\n\\n"
                        "1. What is the target **indication** or disease?\\n"
                        "2. What type of analysis? (Market size / Clinical trials / Patent landscape / Full assessment)\\n\\n"
                        "Once you provide these, I'll create a comprehensive research plan."
                    ),
                    "agents": [],
                    "drug": None,
                    "indication": None
                }

            return result
        
        # If type is "vague", check if we can infer drug + indication from context and chat history
        if result.get("type") == "vague":
            # Try to extract drug and indication from the session context note
            extracted_drug = None
            extracted_indication = None
            
            context_note = session.get("_context_note", "")
            
            # Parse context note to get previous drug
            if "Drug(s):" in context_note:
                drug_part = context_note.split("Drug(s):")[1].split(",")[0].strip()
                if drug_part and drug_part != "None":
                    extracted_drug = [drug_part]
            
            # Parse context note to get previous indication
            if "Indication(s):" in context_note:
                indication_part = context_note.split("Indication(s):")[1].strip()
                if indication_part and indication_part != "None":
                    extracted_indication = [indication_part]
            
            # Also try to extract from latest user messages
            chat_history = session.get("chatHistory", [])
            if not extracted_indication and chat_history:
                last_user_msg = None
                for msg in reversed(chat_history):
                    if msg.get("role") == "user":
                        last_user_msg = msg.get("content", "").lower()
                        break
                
                # Common disease keywords
                diseases = {
                    "diabetes": ["diabetes"],
                    "cancer": ["cancer"],
                    "heart": ["cardiovascular", "cardiac", "heart disease"],
                    "neurodegenerat": ["neurodegenerative"],
                    "covid": ["covid", "coronavirus"],
                    "hiv": ["hiv", "aids"],
                }
                
                if last_user_msg:
                    for disease_key, disease_names in diseases.items():
                        for disease_name in disease_names:
                            if disease_name in last_user_msg:
                                extracted_indication = [disease_key.capitalize()]
                                break
                        if extracted_indication:
                            break
            
            # If we have both drug and indication, generate plan
            if extracted_drug and extracted_indication:
                print(f"[CONTEXT RECOVERY] Inferred drug={extracted_drug}, indication={extracted_indication}")
                return {
                    "type": "plan",
                    "agents": ["iqvia", "exim", "patent", "clinical", "internal", "web", "report"],
                    "drug": extracted_drug,
                    "indication": extracted_indication,
                    "consolidated_prompt": f"Analyze {extracted_drug[0]} for {extracted_indication[0]} treatment. Provide comprehensive analysis covering market trends, clinical pipeline, patent landscape, web sentiment, and trade data."
                }
            
            # Otherwise return the vague response from LLM
            return result

        # If type is any other type, return the result as-is
        return result

    except Exception as e:
        print("[PLANNING ERROR]", e)
        return {
            "type": "vague",
            "message": "I could not correctly understand the request.\\nCan you please rephrase or provide more details?",
            "agents": [],
            "drug": None,
            "indication": None
        }
