"""
Campus Assistant - Multi-Domain Orchestration & Grounded Knowledge Synthesis
File: router/orchestrator.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv
from router.classifier import CampusIntentClassifier, DOMAINS, DOMAIN_NAMES

load_dotenv()

# Resolve workspace root and skill map
ROOT_DIR = Path(__file__).resolve().parent.parent
DOMAIN_SKILL_MAP: Dict[str, Path] = {
    "it": ROOT_DIR / "domain_skills" / "it_skill.md",
    "fees": ROOT_DIR / "domain_skills" / "fees_skill.md",
    "hr": ROOT_DIR / "domain_skills" / "hr_skill.md",
    "facilities": ROOT_DIR / "domain_skills" / "facilities_skill.md"
}

ESCALATION_CONTACTS: Dict[str, Dict[str, str]] = {
    "it": {
        "desk": "Central Library, Ground Floor, Room 102",
        "hours": "Mon–Fri: 08:00 AM – 08:00 PM | Sat–Sun: 10:00 AM – 04:00 PM",
        "email": "helpdesk@campus.edu",
        "phone": "+1 (555) 019-4821",
        "portal": "https://servicedesk.campus.edu"
    },
    "fees": {
        "desk": "Student Services Center, 1st Floor, Counter 3–6",
        "hours": "Mon–Fri: 09:00 AM – 04:30 PM",
        "email": "bursar@campus.edu",
        "phone": "+1 (555) 019-4823",
        "portal": "https://bursar.campus.edu"
    },
    "hr": {
        "desk": "Administration Building, 2nd Floor, Suite 210",
        "hours": "Mon–Fri: 08:30 AM – 05:00 PM",
        "email": "hr-services@campus.edu",
        "phone": "+1 (555) 019-4822",
        "portal": "https://workday.campus.edu"
    },
    "facilities": {
        "desk": "Physical Plant Building, 1st Floor",
        "hours": "24/7 Emergency Dispatch Available",
        "email": "facilities-ops@campus.edu",
        "phone": "+1 (555) 019-4824",
        "portal": "https://facilities.campus.edu/fixit"
    }
}


def _extract_grounded_local_answer(skill_text: str, domain: str, user_query: str) -> str:
    """Intelligently extracts the most relevant sections and facts directly from domain skill markdown."""
    query_words = set(re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', user_query.lower()))

    # Split markdown by sections (## or ###)
    raw_sections = re.split(r'\n(?=#{2,3}\s+)', skill_text)
    scored_sections = []

    for section in raw_sections:
        clean_section = section.strip()
        if not clean_section or clean_section.startswith("# Domain Skill:"):
            continue

        sec_words = set(re.findall(r'\b[a-zA-Z0-9_\-]{3,}\b', clean_section.lower()))
        overlap = len(query_words.intersection(sec_words))
        
        # Boost for title matches
        first_line = clean_section.split('\n')[0].lower()
        for qw in query_words:
            if qw in first_line:
                overlap += 3

        scored_sections.append((overlap, clean_section))

    scored_sections.sort(key=lambda x: x[0], reverse=True)

    # Take top relevant sections
    top_sections = [s for score, s in scored_sections if score > 0]
    if not top_sections and scored_sections:
        top_sections = [scored_sections[0][1]]

    extracted_content = "\n\n".join(top_sections[:2])

    # Extract section heading for citation
    citation_match = re.search(r'#{2,3}\s+(.+)', extracted_content)
    citation_title = citation_match.group(1).strip() if citation_match else f"{domain.upper()} Knowledge Base"

    contacts = ESCALATION_CONTACTS.get(domain, {})
    contact_info = (
        f"\n\n**📞 Official {domain.upper()} Contact & Escalation:**\n"
        f"- **Email:** `{contacts.get('email', 'N/A')}` | **Phone:** `{contacts.get('phone', 'N/A')}`\n"
        f"- **Location / Portal:** [{contacts.get('portal', 'Campus Portal')}]({contacts.get('portal', '#')}) ({contacts.get('desk', 'Campus Desk')})"
    )

    return (
        f"📍 **Source Citation:** *`domain_skills/{domain}_skill.md`* — **{citation_title}**\n\n"
        f"{extracted_content}"
        f"{contact_info}"
    )


def execute_domain_skill(domain: str, user_query: str, api_key: Optional[str] = None) -> str:
    """Executes a specialized domain skill agent using Gemini or Grounded Extraction."""
    clean_domain = domain.lower().strip()
    file_path = DOMAIN_SKILL_MAP.get(clean_domain)

    if not file_path or not file_path.exists():
        return f"⚠️ Grounded knowledge base for '{domain}' not found."

    with open(file_path, "r", encoding="utf-8") as f:
        knowledge_base = f.read()

    resolved_api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    if resolved_api_key:
        try:
            from google import genai
            client = genai.Client(api_key=resolved_api_key)
            prompt = f"""
            You are the official Campus Specialist for the {DOMAIN_NAMES.get(clean_domain, clean_domain)} department.
            Provide an authoritative, clear, and helpful answer to the user query using ONLY the verified Knowledge Base below.
            
            Strict Guidelines:
            1. Explicitly cite the exact section numbers and headings from the knowledge base (e.g. "According to Section 1.1 Eduroam Wi-Fi Setup...").
            2. Include relevant URLs, portals, phone numbers, and physical office locations mentioned.
            3. If steps are required, list them as clear bullet points.
            
            Knowledge Base:
            {knowledge_base}
            
            User Query: "{user_query}"
            """
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if response.text:
                return response.text.strip()
        except Exception:
            # Gracefully fallback to deterministic local extractor
            pass

    return _extract_grounded_local_answer(knowledge_base, clean_domain, user_query)


def process_campus_query(user_query: str, api_key: Optional[str] = None) -> str:
    """Full orchestration pipeline: Intent Classification -> Multi-Domain Dispatch -> Grounded Synthesis."""
    classifier = CampusIntentClassifier(api_key=api_key)
    routing = classifier.classify(user_query)

    domains = routing.detected_domains
    confidence = routing.confidence
    needs_clarification = routing.needs_clarification

    # 1. Out of Domain or Ambiguous Filter
    if routing.primary_domain == "out_of_domain" or confidence < 0.35:
        return (
            "ℹ️ **Out-of-Domain Notice:**\n"
            "This query does not appear to relate to official campus services (IT, Fees, HR, or Facilities).\n\n"
            "If this is an urgent university matter, please reach out directly to the General Campus Helpdesk at "
            "`helpdesk@campus.edu` or visit the Student Services Center."
        )

    # 2. Clarification Needed
    if needs_clarification or (0.35 <= confidence < 0.60):
        suggested = ", ".join([f"**{DOMAIN_NAMES.get(d, d.upper())}**" for d in (domains or DOMAINS)])
        return (
            f"🤔 **Clarification Needed:**\n"
            f"Your inquiry appears ambiguous. Could you please clarify if your question relates to {suggested}?\n\n"
            f"*Tip: You can rephrase your request with more details.*"
        )

    # 3. Multi-Domain / Single-Domain Dispatch & Synthesis
    results = []
    for domain in domains:
        if domain in DOMAIN_SKILL_MAP:
            domain_title = DOMAIN_NAMES.get(domain, domain.upper())
            res = execute_domain_skill(domain, user_query, api_key=api_key)
            results.append(f"### 🏢 {domain_title} ({domain.upper()})\n{res}")

    if not results:
        return "I could not retrieve information for this request. Please contact campus support."

    return "\n\n---\n\n".join(results)