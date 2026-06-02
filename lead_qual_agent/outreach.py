import time
from openai import OpenAI
from state import LeadState

client = OpenAI()

def run(state: LeadState) -> LeadState:
    # TODO: Add multi-language email generation
    # TODO: Implement email personalization with custom templates
    # TODO: Add spam/compliance checker before drafting
    # TODO: Track email open rates and click-through rates for feedback
    
    """
    Main orchestration function that processes a lead through enrichment, scoring, and next steps recommendation.
    """
    prompt = f"""Write a short, personalised B2B outreach email.

Lead: {state.name}, {state.company} ({state.industry}, {state.company_size} employees)
Their message: {state.message}
ICP score: {state.icp_score}/100 — {state.qualification} lead
BANT notes: {state.bant_notes}

Rules:
- Max 120 words
- Reference something specific about their company or message
- Clear single CTA (15-min call)
- No fluff, no "I hope this email finds you well"
- Sign off as "Alex, Head of Partnerships"
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.7,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    state.email_draft = response.choices[0].message.content
    print(f"\n[Outreach] Drafted email for {state.name} at {state.company}:\n{state.email_draft}")
    state.latency_ms['outreach'] = int(time.time() * 1000)
    return state