import json
from datetime import datetime

_crm_db = {}

# Definition of the CRM tool function schema
CRM_TOOL = {
    "type": "function",
    "function": {
        "name": "write_lead_to_crm",
        "description": "Write a qualified lead with score and email draft to the CRM system.",
        "parameters": {
            "type": "object",
            "properties": {
                "lead_id":       {"type": "string", "description": "Unique lead identifier"},
                "name":          {"type": "string", "description": "Lead full name"},
                "email":         {"type": "string", "description": "Lead email address"},
                "company":       {"type": "string", "description": "Company name"},
                "qualification": {"type": "string", "enum": ["HOT", "WARM", "COLD"]},
                "icp_score":     {"type": "integer", "description": "ICP fit score 0-100"},
                "email_draft":   {"type": "string", "description": "Personalised outreach email"},
                "bant_notes":    {"type": "string", "description": "BANT qualification notes"},
            },
            "required": ["lead_id", "name", "email", "company", "qualification", "icp_score"]
        }
    }
}
# Tool executor

def write_lead_to_crm(lead_id, name, email, company, qualification, icp_score, email_draft = "", bant_notes=""):
    """
    Simulates writing a lead to the CRM system. In a real implementation, this would involve
    API calls to the CRM software (e.g., Salesforce, HubSpot).
    """
    record = {
        "lead_id": lead_id,
        "name": name,
        "email": email,
        "company": company,
        "qualification": qualification,
        "icp_score": icp_score,
        "email_draft": email_draft,
        "bant_notes": bant_notes,
        "created_at": datetime.utcnow().isoformat()
    }
    _crm_db[lead_id] = record
    print(f"\n[CRM] ✓ Lead '{name}' written → qualification={qualification}, score={icp_score}")
    return {"status": "success", "record": record}

def get_all_leads():
    """Utility function to retrieve all leads from the mock CRM."""
    return list(_crm_db.values())

def dispatch_tool_call(name: str, arguments:str):
    """Dispatches the tool call to the appropriate function based on the tool name."""
    if name == "write_lead_to_crm":
        args = json.loads(arguments)
        result =  write_lead_to_crm(**args)
        return json.dumps(result)
    else:
        raise ValueError(f"Unknown tool: {name}")