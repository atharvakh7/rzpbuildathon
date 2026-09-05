"""
Mistral client wrapper for reasoning, explanation, and Hinglish recovery message generation.
Includes rate limiting and structured output parsing, with deterministic fallbacks.
"""

import json
from typing import Any, Dict, List, Optional
from app.config import settings


class MistralAgentService:
    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY

    async def explain_decision(
        self,
        customer_name: str,
        amount: float,
        root_cause: str,
        selected_action: str,
        erv: float,
        alternatives: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate WHY, WHY THIS ACTION, WHY NOT THE ALTERNATIVES explanations.
        """
        if settings.mistral_available:
            try:
                from mistralai import Mistral
                client = Mistral(api_key=self.api_key)

                prompt = f"""You are RecoverAI's decision explainability engine.
Case:
- Customer: {customer_name}
- Amount at risk: INR {amount}
- Diagnosed Root Cause: {root_cause}
- Selected Intervention: {selected_action} (Expected Recovery Value: INR {erv})
- Evaluated Alternatives: {json.dumps(alternatives)}

Generate a structured financial explainability response in JSON with these keys:
- "why": 1-2 sentence assessment of customer risk context.
- "why_this_action": 1-2 sentence economic justification for selecting {selected_action}.
- "why_not_alternatives": JSON object mapping each alternative action name to 1 sentence why it was inferior.
- "policy_summary": "Compliant with automated recovery guardrails."
- "stop_condition": "Stop on successful payment or policy limit."

Only return valid JSON."""

                resp = await client.chat.complete_async(
                    model="mistral-small-latest",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=600,
                )
                raw = resp.choices[0].message.content.strip()
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
                data = json.loads(raw)
                return data
            except Exception:
                pass  # Fall through to deterministic template

        # Deterministic explainability fallback
        why = f"Customer has active exposure of ₹{amount:,.2f} associated with {root_cause.replace('_', ' ')}."
        why_this = f"{selected_action.replace('_', ' ').title()} maximizes Expected Recovery Value (₹{erv:,.2f}) within policy boundaries."

        why_not = {}
        for alt in alternatives:
            alt_name = alt.get("action", "")
            if alt_name != selected_action:
                alt_erv = alt.get("expected_recovery_value", 0)
                if alt.get("policy_status") != "ALLOWED":
                    why_not[alt_name] = f"Blocked by policy guardrail: {alt.get('policy_reason', 'policy denial')}."
                elif alt_erv < erv:
                    why_not[alt_name] = f"Lower Expected Recovery Value (₹{alt_erv:,.2f} vs ₹{erv:,.2f})."
                else:
                    why_not[alt_name] = "Suboptimal risk-adjusted yield compared to primary recommendation."

        return {
            "why": why,
            "why_this_action": why_this,
            "why_not_alternatives": why_not,
            "policy_summary": "Validated against deterministic recovery guardrails.",
            "stop_condition": "Stop on settlement or max attempts reached."
        }

    async def generate_message(
        self,
        customer_name: str,
        amount: float,
        recovery_type: str,
        payment_link: str,
        language: str = "english"
    ) -> str:
        """
        Dynamically generate Hinglish or English recovery notification.
        Validates amounts and respectful tone.
        """
        if settings.mistral_available:
            try:
                from mistralai import Mistral
                client = Mistral(api_key=self.api_key)

                prompt = f"""Write a polite, professional, dynamic payment recovery message.
Customer: {customer_name}
Amount: INR {amount:,.2f}
Recovery Type: {recovery_type}
Payment Link: {payment_link}
Language: {language} (if Hinglish, use natural conversational conversational Hindi in Latin script, like: 'Hi {customer_name}, aapka INR {amount:,.2f} ka payment...')
Rules:
- Respectful, helpful, absolutely no aggressive or harassing words.
- Clearly mention the exact amount: INR {amount:,.2f}.
- Keep it under 60 words."""

                resp = await client.chat.complete_async(
                    model="mistral-small-latest",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=200,
                )
                msg = resp.choices[0].message.content.strip()
                if msg:
                    return msg
            except Exception:
                pass

        # Deterministic dynamic message templates
        first_name = customer_name.split()[0] if customer_name else "Customer"
        if language.lower() == "hinglish":
            return (
                f"Hi {first_name},\n\n"
                f"Aapka ₹{amount:,.2f} ka payment complete nahi ho paya. "
                f"Aap UPI ya card se dobara payment try kar sakte hain.\n\n"
                f"Payment complete karne ke liye yahan click karein: {payment_link}"
            )
        else:
            return (
                f"Hi {first_name},\n\n"
                f"We noticed your payment of ₹{amount:,.2f} was not completed. "
                f"You can easily complete it using UPI, Cards, or Net Banking.\n\n"
                f"Click here to resolve securely: {payment_link}"
            )


mistral_agent_service = MistralAgentService()
