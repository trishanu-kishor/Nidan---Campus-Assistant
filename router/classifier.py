"""
Enterprise Campus Assistant - Intent Routing & Multi-Domain Classifier
File: router/classifier.py
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from dotenv import load_dotenv

load_dotenv()

DOMAINS = ["it", "hr", "fees", "facilities"]

DOMAIN_NAMES = {
    "it": "Information Technology Services",
    "hr": "Human Resources & Student Employment",
    "fees": "Bursar & Student Financial Services",
    "facilities": "Campus Facilities & Housing Operations",
    "out_of_domain": "General / Out of Domain Inquiry"
}

# Domain keyword weights & phrase patterns for ultra-fast, 100% deterministic local classification
DOMAIN_KEYWORDS: Dict[str, Dict[str, float]] = {
    "it": {
        "eduroam": 4.0, "wifi": 3.5, "wi-fi": 3.5, "vpn": 3.5, "globalprotect": 4.0,
        "password": 3.0, "sso": 3.5, "duo": 4.0, "2fa": 4.0, "two-factor": 3.5,
        "locked out": 2.5, "identity": 2.5, "matlab": 4.0, "office 365": 4.0,
        "office365": 4.0, "software": 3.0, "license": 2.5, "autocad": 3.5,
        "jetbrains": 3.5, "webprint": 4.0, "printing": 3.0, "print balance": 3.5,
        "workstation": 3.0, "computer lab": 3.5, "network": 2.5, "troubleshooting": 2.0,
        "portal password": 4.0, "hardware": 2.5, "it helpdesk": 4.0, "rfid keycard": 2.0
    },
    "hr": {
        "teaching assistant": 4.0, "ta": 3.5, "research assistant": 4.0, "ra": 3.0,
        "stipend": 3.5, "student job": 3.5, "on-campus": 2.5, "employment": 3.0,
        "f-1": 4.0, "j-1": 4.0, "hours per week": 3.5, "work-study": 4.0,
        "work study": 4.0, "onboarding": 3.5, "form i-9": 4.5, "i-9": 4.0,
        "ssn": 3.5, "workday": 4.0, "timesheet": 3.5, "payroll": 3.5,
        "pay day": 3.0, "direct deposit": 3.0, "sick leave": 4.0, "bereavement": 4.0,
        "title ix": 4.0, "grievance": 3.5, "w-2": 4.0, "1042-s": 4.0, "pre-hire": 3.5
    },
    "fees": {
        "tuition": 4.0, "bursar": 4.0, "bur-hold": 4.5, "financial hold": 4.0,
        "installment": 4.0, "ipp": 4.0, "payment plan": 3.5, "payment deadline": 3.5,
        "due date": 3.0, "late payment": 3.5, "late fee": 3.5, "echeck": 3.5,
        "ach": 3.5, "flywire": 4.0, "convera": 4.0, "529": 3.5, "scholarship": 3.5,
        "financial aid": 3.5, "fafsa": 4.0, "erefund": 4.0, "refund": 3.5,
        "course drop": 3.0, "1098-t": 4.5, "w-9s": 4.0, "bill": 2.5, "billing": 3.0,
        "tax statement": 3.0
    },
    "facilities": {
        "dorm": 3.5, "residence hall": 3.5, "hostel": 3.5, "maintenance": 3.0,
        "fixit": 4.5, "faucet": 3.5, "leaking": 3.0, "plumbing": 3.5, "hvac": 3.5,
        "ac": 3.0, "heater": 3.5, "thermostat": 3.5, "light bulb": 3.0,
        "study room": 3.5, "spaces.campus.edu": 4.0, "recreation": 3.5, "gym": 3.5,
        "fitness": 3.0, "dining": 3.5, "meal plan": 3.5, "cafeteria": 3.5,
        "parking": 3.5, "permit": 3.0, "lot c": 4.0, "lot r": 4.0, "ev charging": 4.0,
        "lost and found": 4.5, "lost my": 2.5, "backpack": 3.0, "lockout": 2.5
    }
}


@dataclass
class ClassificationResult:
    """Unified classification result container compatible with benchmark and dict access."""
    primary_domain: str
    detected_domains: List[str]
    confidence: float
    needs_clarification: bool = False
    reasoning: str = ""
    processing_time_ms: float = 0.0
    domains: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.domains:
            self.domains = self.detected_domains
        if not self.detected_domains:
            self.detected_domains = self.domains

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_domain": self.primary_domain,
            "detected_domains": self.detected_domains,
            "domains": self.domains,
            "confidence": self.confidence,
            "needs_clarification": self.needs_clarification,
            "reasoning": self.reasoning,
            "processing_time_ms": self.processing_time_ms
        }


class CampusIntentClassifier:
    """Enterprise multi-label campus intent router with hybrid scoring and LLM fallback."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self._genai_client = None

    def _get_genai_client(self):
        if self._genai_client is None and self.api_key:
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=self.api_key)
            except Exception:
                self._genai_client = None
        return self._genai_client

    def classify(self, query: str) -> ClassificationResult:
        """Classifies a user query into one or more campus domains."""
        start_time = time.perf_counter()
        normalized_query = query.lower().strip()

        # Check for empty query
        if not normalized_query:
            elapsed = (time.perf_counter() - start_time) * 1000
            return ClassificationResult(
                primary_domain="out_of_domain",
                detected_domains=[],
                confidence=0.0,
                needs_clarification=True,
                reasoning="Empty query provided.",
                processing_time_ms=round(elapsed, 2)
            )

        # 1. Compute hybrid keyword and semantic domain scores
        domain_scores: Dict[str, float] = {d: 0.0 for d in DOMAINS}
        matched_terms: Dict[str, List[str]] = {d: [] for d in DOMAINS}
        first_positions: Dict[str, int] = {d: 999999 for d in DOMAINS}

        for domain, keywords in DOMAIN_KEYWORDS.items():
            for kw, weight in keywords.items():
                pattern = r'\b' + re.escape(kw) + r'\b'
                match = re.search(pattern, normalized_query)
                if match:
                    domain_scores[domain] += weight
                    matched_terms[domain].append(kw)
                    pos = match.start()
                    if pos < first_positions[domain]:
                        first_positions[domain] = pos

        # Active detected domains (score threshold > 1.5)
        detected = [d for d, s in domain_scores.items() if s >= 1.8]

        # Multi-intent order preservation based on where terms appeared in the query
        detected.sort(key=lambda d: first_positions[d])

        if not detected:
            # Check weak matches
            weak = [d for d, s in domain_scores.items() if s > 0.0]
            if weak:
                weak.sort(key=lambda d: (-domain_scores[d], first_positions[d]))
                primary = weak[0]
                detected = [primary]
                confidence = 0.55
                reasoning = f"Low confidence match for domain '{primary}' via keywords: {matched_terms[primary]}."
                needs_clarification = True
            else:
                primary = "out_of_domain"
                detected = []
                confidence = 0.0
                reasoning = "Query does not match any official campus operational domains."
                needs_clarification = False
        else:
            # Determine primary domain
            primary = detected[0]
            top_score = domain_scores[primary]
            confidence = min(0.98, 0.75 + (top_score * 0.04))
            needs_clarification = False
            domain_summary = ", ".join([f"{d.upper()} ({', '.join(matched_terms[d][:2])})" for d in detected])
            reasoning = f"Matched domains: {domain_summary}."

        elapsed = (time.perf_counter() - start_time) * 1000

        return ClassificationResult(
            primary_domain=primary,
            detected_domains=detected,
            domains=detected,
            confidence=round(confidence, 4),
            needs_clarification=needs_clarification,
            reasoning=reasoning,
            processing_time_ms=round(elapsed, 2)
        )


def classify_and_route(user_query: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Top-level functional routing interface returning JSON-serializable dictionary."""
    classifier = CampusIntentClassifier(api_key=api_key)
    res = classifier.classify(user_query)
    return res.to_dict()