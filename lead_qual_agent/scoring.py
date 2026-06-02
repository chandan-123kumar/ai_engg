import time, json
from openai import OpenAI
from state import LeadState

client = OpenAI()

SYSTEM_PROMPT = """You are a B2B sales qualification expert using the BANT framework.
Score this lead on ICP (Ideal Customer Profile) fit from 0-100 and qualify them.

Scoring guide:
- 80-100 → HOT  (strong fit, likely budget, decision maker)
- 50-79  → WARM (partial fit, needs nurturing)
- 0-49   → COLD (poor fit or no budget signals)

Respond ONLY in this JSON format:
{
  "icp_score": <integer 0-100>,
  "qualification": "<HOT|WARM|COLD>",
  "bant_notes": "<2-3 sentence BANT analysis>"
}"""


def run(state: LeadState) -> LeadState:
    # TODO: Add weighted scoring model (company size: 30%, industry: 30%, budget signals: 40%)
    # TODO: Store scoring decisions for training feedback loop
    # TODO: Implement human-in-the-loop: flag edge cases for manual review
    
    t0 = time.time()
    print(f"\n[Scoring] Scoring lead '{state.name}' from {state.company}...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": (
                f"Lead: {state.name} ({state.email})\n"
                f"Company: {state.company}\n"
                f"Industry: {state.industry} | Size: {state.company_size}\n"
                f"Tech stack: {', '.join(state.tech_stack)}\n"
                f"Their message: {state.message}"
            )}
        ]
    )


    try:
        data = json.loads(response.choices[0].message.content)
        state.icp_score = data.get("icp_score", 0)
        state.qualification = data.get("qualification", "COLD")
        state.bant_notes = data.get("bant_notes", "")
        print(f"[Scoring] ✓ ICP Score: {state.icp_score}, Qualification: {state.qualification}")
    except Exception as e:
        error_msg = f"Scoring parsing error: {str(e)}"
        state.errors.append(error_msg)
        print(f"[Scoring] ✗ {error_msg}")
    state.latency_ms['scoring'] = int((time.time() - t0) * 1000)
    return state    