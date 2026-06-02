from openai import OpenAI
import time, json
from state import LeadState
from enrichment import run as enrichment_run
from scoring import run as scoring_run
from outreach import run as outreach_run
from tools.crm_mock import CRM_TOOL, dispatch_tool_call


client = OpenAI()





def run(lead: LeadState) -> LeadState:
    """
    Orchestrator function that takes in a lead state, processes it through various stages,
    and returns the updated lead state.
    """
    t0 = time.time()
    print(f"\n[Orchestrator] Starting processing for lead '{lead.name}' from {lead.company}...")
    
    # TODO: Add pre-flight validation (check required fields, data quality)
    # TODO: Implement caching to skip already-processed leads
    
    lead = enrichment_run(lead)
    # TODO: Add fallback enrichment from external data sources (LinkedIn, Crunchbase) if LLM fails
    
    lead = scoring_run(lead)
    # TODO: Add conditional logic: if COLD lead, decide whether to skip outreach
    # TODO: Implement A/B testing different scoring models
    
    lead = outreach_run(lead)
    # TODO: Store email drafts for human review before sending (compliance check)
    # TODO: Add A/B testing for email templates and CTAs  

    print(f"\n[Orchestrator] Deciding next action via tool call...")
    messages = [
        {
            "role": "system",
            "content": (
                "You are a lead qualification orchestrator. "
                "Given a fully enriched and scored lead, call write_lead_to_crm "
                "with all the available data. Always call the tool — never just respond with text."
            )
        },
        {
            "role": "user",
            "content": (
                f"Lead data:\n"
                f"- lead_id: {lead.lead_id}\n"
                f"- name: {lead.name}\n"
                f"- email: {lead.email}\n"
                f"- company: {lead.company}\n"
                f"- qualification: {lead.qualification}\n"
                f"- icp_score: {lead.icp_score}\n"
                f"- bant_notes: {lead.bant_notes}\n"
                f"- email_draft: {lead.email_draft}\n"
                "Please write this lead to the CRM now."
            )
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        tools=[CRM_TOOL],
        tool_choice="required",   # force tool use — no free-text escape
        messages=messages
    )

    # ── Step 3: Execute tool call ────────────────────────────────────────────
    tool_call = response.choices[0].message.tool_calls[0]
    result = dispatch_tool_call(tool_call.function.name, tool_call.function.arguments)
    print(f"[Orchestrator] Tool result: {result[:120]}...")

    lead.latency_ms["total"] = round((time.time() - t0) * 1000)
    print(f"\n[Orchestrator] ✓ Done in {lead.latency_ms['total']}ms")
    return lead