"""
Razorpay Payment Provider integration.
Uses razorpay client in test mode if credentials exist,
otherwise gracefully proxies/falls back to SimulationProvider.
"""

from typing import Any, Dict
from app.config import settings
from app.providers.base import PaymentProvider
from app.providers.simulation_provider import SimulationProvider


class RazorpayProvider(PaymentProvider):
    def __init__(self):
        self._simulator = SimulationProvider()
        self._client = None
        if settings.razorpay_available:
            try:
                import razorpay
                self._client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            except Exception:
                self._client = None

    async def retry_payment(self, case_id: int, amount: float, payment_method: str, customer_info: Dict[str, Any], probability: float) -> Dict[str, Any]:
        if not self._client:
            return await self._simulator.retry_payment(case_id, amount, payment_method, customer_info, probability)

        try:
            # In live Razorpay test mode, create order or simulated recurring charge
            order_data = {
                "amount": int(amount * 100),  # paise
                "currency": "INR",
                "receipt": f"rcpt_retry_{case_id}",
                "notes": {"case_id": str(case_id), "type": "smart_retry"}
            }
            order = self._client.order.create(data=order_data)
            return {
                "success": True,
                "transaction_id": order.get("id"),
                "amount_recovered": float(amount),
                "provider": "razorpay_test"
            }
        except Exception:
            return await self._simulator.retry_payment(case_id, amount, payment_method, customer_info, probability)

    async def create_payment_link(self, case_id: int, amount: float, customer_info: Dict[str, Any], probability: float) -> Dict[str, Any]:
        if not self._client:
            return await self._simulator.create_payment_link(case_id, amount, customer_info, probability)

        try:
            link_payload = {
                "amount": int(amount * 100),
                "currency": "INR",
                "accept_partial": False,
                "description": f"RecoverAI Recovery Link for Case #{case_id}",
                "customer": {
                    "name": customer_info.get("name", "Customer"),
                    "contact": customer_info.get("phone", "+919999999999"),
                    "email": customer_info.get("email", "customer@example.com")
                },
                "notify": {"sms": True, "email": True},
                "reminder_enable": True,
                "notes": {"case_id": str(case_id)}
            }
            link = self._client.payment_link.create(link_payload)
            return {
                "success": True,
                "payment_link_id": link.get("id"),
                "payment_url": link.get("short_url"),
                "amount_recovered": float(amount),
                "provider": "razorpay_test"
            }
        except Exception:
            return await self._simulator.create_payment_link(case_id, amount, customer_info, probability)

    async def send_recovery_message(self, customer_info: Dict[str, Any], message: str, channel: str) -> Dict[str, Any]:
        return await self._simulator.send_recovery_message(customer_info, message, channel)

    async def record_payment(self, case_id: int, amount: float) -> Dict[str, Any]:
        return await self._simulator.record_payment(case_id, amount)


def get_payment_provider() -> PaymentProvider:
    """Factory to obtain configured payment provider."""
    if settings.razorpay_available:
        return RazorpayProvider()
    return SimulationProvider()
