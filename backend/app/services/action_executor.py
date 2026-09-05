"""
Action Executor service.
Executes chosen recovery interventions via configured PaymentProvider,
enforces audit logging, writes to RecoveryAction and RecoveryLedger,
and mutates DB state.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.mistral_client import mistral_agent_service
from app.models.models import Customer, RecoveryAction, RecoveryCase, RecoveryLedger
from app.providers.razorpay_provider import get_payment_provider


class ActionExecutor:
    def __init__(self):
        self.provider = get_payment_provider()

    async def execute_action(
        self,
        db: AsyncSession,
        case: RecoveryCase,
        action_type: str,
        probability: float,
        cost: float,
        erv: float,
        incremental: float,
        baseline_prob: float,
        policy_result: Dict[str, Any],
        language: str = "english",
        explanation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute the selected intervention, track attempts, update state, and append audit ledger.
        """
        customer = case.customer
        amount = float(case.amount_at_risk)
        customer_info = {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "email": customer.email,
            "opt_out": customer.opt_out,
            "dispute_status": customer.dispute_status,
        }

        execution_result = "FAILURE"
        amount_recovered = 0.0
        msg_content = None
        stop_reason = None

        if not policy_result.get("allowed", False):
            execution_result = "DENIED"
            stop_reason = policy_result.get("reason", "Denied by policy guardrail")
        elif action_type == "STOP":
            execution_result = "STOPPED"
            stop_reason = "Deliberate agent stop decision."
        elif action_type == "HUMAN_ESCALATION":
            execution_result = "ESCALATED"
            case.status = "ESCALATED"
            stop_reason = "Escalated for human operator review."
        elif action_type in ("SMART_RETRY", "ALTERNATE_PAYMENT_METHOD"):
            res = await self.provider.retry_payment(
                case_id=case.id,
                amount=amount,
                payment_method="UPI" if action_type == "ALTERNATE_PAYMENT_METHOD" else "credit_card",
                customer_info=customer_info,
                probability=probability
            )
            if res.get("success"):
                execution_result = "SUCCESS"
                amount_recovered = amount
            else:
                execution_result = "FAILURE"

        elif action_type in ("PAYMENT_LINK", "REMINDER", "HINGLISH_MESSAGE", "PAYMENT_PLAN", "PROMISE_TO_PAY"):
            # Provider link + dynamic recovery messaging
            link_res = await self.provider.create_payment_link(
                case_id=case.id,
                amount=amount,
                customer_info=customer_info,
                probability=probability
            )
            url = link_res.get("payment_url", f"https://pay.recoverai.demo/case/{case.id}")
            lang_to_use = "hinglish" if action_type == "HINGLISH_MESSAGE" else language
            msg_content = await mistral_agent_service.generate_message(
                customer_name=customer.name,
                amount=amount,
                recovery_type=case.recovery_type,
                payment_link=url,
                language=lang_to_use
            )
            await self.provider.send_recovery_message(
                customer_info=customer_info,
                message=msg_content,
                channel="whatsapp" if lang_to_use == "hinglish" else "sms"
            )

            if link_res.get("success"):
                execution_result = "SUCCESS"
                amount_recovered = amount
            else:
                execution_result = "FAILURE"

        # Update case metrics & attempts
        case.attempt_count = (case.attempt_count or 0) + 1

        if execution_result == "SUCCESS":
            case.status = "RECOVERED"
            case.amount_recovered = Decimal(str(amount_recovered))
            stop_reason = "Full settlement recovered."
        elif execution_result == "ESCALATED":
            case.status = "ESCALATED"
        elif execution_result == "DENIED":
            # If denied by policy, check if max retries or opt out
            if "opt" in (stop_reason or "").lower() or "dispute" in (stop_reason or "").lower():
                case.status = "STOPPED"
                case.stop_reason = stop_reason
            else:
                case.status = "ESCALATED"
        elif execution_result == "STOPPED":
            case.status = "STOPPED"
            case.stop_reason = stop_reason
        else:
            # Action failed — status stays DIAGNOSED / IN_PROGRESS for re-evaluation
            case.status = "IN_PROGRESS"

        # Record Action in database
        action_record = RecoveryAction(
            case_id=case.id,
            action_type=action_type,
            recovery_probability=probability,
            intervention_cost=Decimal(str(cost)),
            expected_recovery_value=Decimal(str(erv)),
            incremental_recovery=incremental,
            baseline_probability=baseline_prob,
            policy_status=policy_result.get("result", "ALLOWED"),
            policy_reason=policy_result.get("reason"),
            execution_result=execution_result,
            amount_recovered=Decimal(str(amount_recovered)),
            attempt_number=case.attempt_count,
            message_content=msg_content,
            message_language=language if action_type == "HINGLISH_MESSAGE" else "english",
        )
        db.add(action_record)
        await db.flush()

        # Record immutable Recovery Ledger entry
        ledger_entry = RecoveryLedger(
            case_id=case.id,
            customer_id=customer.id,
            recovery_type=case.recovery_type,
            amount_at_risk=case.amount_at_risk,
            root_cause=case.root_cause,
            confidence=case.confidence,
            recommended_action=action_type,
            selected_action=action_type,
            recovery_probability=probability,
            expected_recovery_value=Decimal(str(erv)),
            policy_result=policy_result.get("result", "ALLOWED"),
            policy_reason=policy_result.get("reason"),
            execution_result=execution_result,
            amount_recovered=Decimal(str(amount_recovered)),
            status=case.status,
            stop_reason=stop_reason,
            agent_explanation=explanation,
        )
        db.add(ledger_entry)
        await db.flush()

        return {
            "case_id": case.id,
            "action_type": action_type,
            "policy_result": policy_result.get("result", "ALLOWED"),
            "policy_reason": policy_result.get("reason"),
            "execution_result": execution_result,
            "amount_recovered": amount_recovered,
            "case_status": case.status,
            "stop_reason": stop_reason,
            "message_content": msg_content,
            "agent_explanation": explanation,
        }


action_executor = ActionExecutor()
