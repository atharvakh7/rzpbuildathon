"""
Simulation Provider for offline / demo environments.
Computes dynamic outcomes based on statistical recovery probabilities,
NOT hardcoded per-customer results!
"""

import random
import uuid
from typing import Any, Dict
from app.providers.base import PaymentProvider


class SimulationProvider(PaymentProvider):
    async def retry_payment(self, case_id: int, amount: float, payment_method: str, customer_info: Dict[str, Any], probability: float) -> Dict[str, Any]:
        """
        Dynamically simulate retry outcome using statistical recovery probability.
        """
        # Hard stops
        if customer_info.get("opt_out") or customer_info.get("dispute_status"):
            return {
                "success": False,
                "transaction_id": f"sim_tx_{uuid.uuid4().hex[:10]}",
                "error": "Customer opted out or dispute active",
                "amount_recovered": 0.0,
            }

        # Dynamic outcome evaluation
        draw = random.random()
        success = draw <= probability

        return {
            "success": success,
            "transaction_id": f"sim_tx_{uuid.uuid4().hex[:10]}",
            "amount_recovered": float(amount) if success else 0.0,
            "probability_evaluated": probability,
            "random_draw": round(draw, 4),
            "error": None if success else "Simulated issuer decline on retry",
        }

    async def create_payment_link(self, case_id: int, amount: float, customer_info: Dict[str, Any], probability: float) -> Dict[str, Any]:
        draw = random.random()
        success = draw <= probability
        link_id = f"plink_sim_{uuid.uuid4().hex[:8]}"

        return {
            "success": success,
            "payment_link_id": link_id,
            "payment_url": f"https://pay.recoverai.demo/{link_id}",
            "amount_recovered": float(amount) if success else 0.0,
            "probability_evaluated": probability,
            "random_draw": round(draw, 4),
            "error": None if success else "Customer did not complete payment link",
        }

    async def send_recovery_message(self, customer_info: Dict[str, Any], message: str, channel: str) -> Dict[str, Any]:
        return {
            "success": True,
            "message_id": f"msg_sim_{uuid.uuid4().hex[:8]}",
            "recipient": customer_info.get("phone") or customer_info.get("email"),
            "channel": channel,
            "delivered": True,
        }

    async def record_payment(self, case_id: int, amount: float) -> Dict[str, Any]:
        return {
            "success": True,
            "settlement_id": f"settle_{uuid.uuid4().hex[:8]}",
            "amount": float(amount),
        }
