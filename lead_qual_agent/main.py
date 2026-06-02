from dotenv import load_dotenv
import os

# Load environment variables FIRST, before any other imports
load_dotenv()

import uuid
from state import LeadState
from orchestractor import run
print(f"Loaded environment variables. Starting lead qualification agent... #{os.getenv('OPENAI_API_KEY')[:5]}...")

TEST_LEADS = [
    {
        "name":    "Priya Sharma",
        "email":   "priya@finedge.io",
        "company": "FinEdge",
        "message": "We're a 200-person fintech company looking to automate our sales ops. "
                   "We currently use Salesforce and are evaluating AI tools for lead scoring. "
                   "Our CTO wants something production-ready within Q3."
    },
    {
        "name":    "Tom Baker",
        "email":   "tom@bakerconsulting.net",
        "company": "Baker Consulting",
        "message": "Just exploring options, no real timeline. Small team, 3 people."
    },
]


def main():
    # TODO: Load leads from database or external API instead of hardcoded list
    # TODO: Add batch processing with rate limiting
    # TODO: Add metrics/telemetry collection (success rate, avg latency, etc.)
    
    for lead_data in TEST_LEADS:
        lead = LeadState(
            lead_id=str(uuid.uuid4()),
            **lead_data
        )
        result = run(lead)
        
        # TODO: Persist results to database (PostgreSQL, MongoDB, etc.)
        # TODO: Send qualified leads to analytics/BI system
        # TODO: Handle errors gracefully and retry failed leads
        
        print(f"\n── Final state: {result.name} ──────────────")
        print(f"  Qualification : {result.qualification}")
        print(f"  ICP Score     : {result.icp_score}/100")
        print(f"  Industry      : {result.industry} | Size: {result.company_size}")
        print(f"  BANT Notes    : {result.bant_notes}")
        if result.email_draft:
            print(f"  Email Draft   :\n{result.email_draft}")
        print(f"  Latency       : {result.latency_ms}")
        if result.errors:
            print(f"  Errors        : {result.errors}")      



if __name__ == "__main__":
    main()
