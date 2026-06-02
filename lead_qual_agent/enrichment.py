import time
from openai import OpenAI
from state import LeadState
import json

client = OpenAI()

SYSTEM_PROMPT = """You are a B2B lead enrichment specialist.
Given a company name and a lead's message, infer:
- company_size: one of "1-10", "11-50", "51-200", "201-1000", "1000+"
- industry: e.g. "FinTech", "HealthTech", "E-commerce", "SaaS", "Manufacturing"
- tech_stack: list of likely technologies (max 5 items, infer from context clues)

Respond ONLY in this exact JSON format, no extra text:
{
  "company_size": "...",
  "industry": "...",
  "tech_stack": ["...", "..."]
}""" 

def run(state: LeadState) -> LeadState:
    # TODO: Cache enrichment results by company to avoid duplicate API calls
    # TODO: Add external data sources (LinkedIn Company API, Crunchbase, etc.)
    # TODO: Validate enrichment data against known-good patterns
    # TODO: Implement retry logic with exponential backoff for API failures
    
    start_time = time.time()
    print(f"\n[Enrichment] Enriching lead '{state.name}' from {state.company}...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Company: {state.company}\nMessage: {state.message}"}
        ]
    )

    try:
        data = json.loads(response.choices[0].message.content)
        state.company_size = data.get("company_size", "Unknown")
        state.industry = data.get("industry", "Unknown")
        state.tech_stack = data.get("tech_stack", [])
        print(f"[Enrichment] ✓ {state.industry}, {state.company_size} employees, stack: {state.tech_stack}")
    except Exception as e:
        error_msg = f"Enrichment parsing error: {str(e)}"
        state.errors.append(error_msg)
        print(f"[Enrichment] ✗ {error_msg}")
    return state    
