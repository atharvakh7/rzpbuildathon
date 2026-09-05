"""
Abstract base class for payment providers.
Allows seamless switching between live Razorpay and SimulationProvider.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class PaymentProvider(ABC):
    @abstractmethod
    async def retry_payment(self, case_id: int, amount: float, payment_method: str, customer_info: Dict[str, Any], probability: float) -> Dict[str, Any]:
        """Attempt to retry a failed payment."""
        pass

    @abstractmethod
    async def create_payment_link(self, case_id: int, amount: float, customer_info: Dict[str, Any], probability: float) -> Dict[str, Any]:
        """Generate a dynamic payment link."""
        pass

    @abstractmethod
    async def send_recovery_message(self, customer_info: Dict[str, Any], message: str, channel: str) -> Dict[str, Any]:
        """Send recovery notification / reminder."""
        pass

    @abstractmethod
    async def record_payment(self, case_id: int, amount: float) -> Dict[str, Any]:
        """Record a successful payment settlement."""
        pass
