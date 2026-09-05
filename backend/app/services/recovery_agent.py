"""
Recovery Agent — Core Intelligence Engine for RecoverAI.
Implements the continuous agentic loop:
DETECT → DIAGNOSE → EVALUATE INTERVENTIONS → SELECT BEST (ERV) →
POLICY CHECK → EXECUTE → OBSERVE RESULT → RECOVER / RE-EVALUATE / ESCALATE / STOP
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.mistral_client import mistral_agent_service
from app.models.models import (
    AgentDecision, Customer, RecoveryAction, RecoveryCase, RecoveryLedger
)
from app.policies.policy_engine import check_policy, log_policy_check
from app.services.action_executor import action_executor
from app.services.root_cause_engine import diagnose
from app.services.value_calculator import (
    calculate_baseline_probability,
    calculate_expected_recovery_value,
    calculate_incremental_recovery,
    calculate_recovery_probability,
    get_available_actions,
    get_intervention_cost,
)


class RecoveryAgent:
    async def analyze_case(self, db: AsyncSession, case_id: int) -> Dict[str, Any]:
        """
        Diagnoses root cause, evaluates candidate interventions with ERV,
        checks policy eligibility, and generates structured reasoning.
        """
        query = (
            select(RecoveryCase)
            .options(
                selectinload(RecoveryCase.customer),
                selectinload(RecoveryCase.payment_event),
                selectinload(RecoveryCase.checkout_event),
                selectinload(RecoveryCase.invoice),
                selectinload(RecoveryCase.actions),
            )
            .where(RecoveryCase.id == case_id)
        )
        result = await db.execute(query)
        case = result.scalar_one_or_none()
        if not case:
            raise ValueError(f"Recovery case {case_id} not found.")

        customer = case.customer
        total_attempts = case.attempt_count or 0

        # Extract features
        tot_hist = (customer.previous_payments or 0) + (customer.previous_failures or 0)
        success_rate = (customer.previous_payments or 0) / tot_hist if tot_hist > 0 else 0.5
        ltv = float(customer.ltv or 0)

        decline_code = case.payment_event.decline_code if case.payment_event else None
        failure_reason = case.payment_event.failure_reason if case.payment_event else None
        abandonment_reason = case.checkout_event.abandonment_reason if case.checkout_event else None
        page_reached = case.checkout_event.page_reached if case.checkout_event else None
        days_overdue = case.invoice.days_overdue if case.invoice else 0
        dispute_flag = (case.invoice.dispute_flag if case.invoice else False) or customer.dispute_status
        hardship_flag = customer.hardship_status

        # 1. DIAGNOSE (if not already diagnosed)
        if not case.root_cause:
            diag = await diagnose(
                recovery_type=case.recovery_type,
                decline_code=decline_code,
                failure_reason=failure_reason,
                abandonment_reason=abandonment_reason,
                page_reached=page_reached,
                days_overdue=days_overdue,
                dispute_flag=dispute_flag,
                hardship_flag=hardship_flag,
                customer_success_rate=success_rate,
                customer_previous_payments=customer.previous_payments or 0,
                amount=float(case.amount_at_risk),
                payment_method=case.payment_event.payment_method if case.payment_event else None,
                ltv=ltv,
                previous_failures=customer.previous_failures or 0,
            )
            case.root_cause = diag["root_cause"]
            case.confidence = diag["confidence"]
            case.evidence = diag.get("evidence", [])
            case.status = "DIAGNOSED" if case.status == "PENDING" else case.status
            await db.flush()

        # 2. EVALUATE CANDIDATE INTERVENTIONS
        candidate_actions = get_available_actions(case.recovery_type)
        amount = float(case.amount_at_risk)

        baseline_prob = calculate_baseline_probability(
            customer_success_rate=success_rate,
            failure_reason=case.root_cause or failure_reason,
            recovery_type=case.recovery_type,
            has_dispute=dispute_flag,
            has_opt_out=customer.opt_out,
        )

        interventions: List[Dict[str, Any]] = []
        for act in candidate_actions:
            prob = calculate_recovery_probability(
                action_type=act,
                customer_success_rate=success_rate,
                failure_reason=case.root_cause or failure_reason,
                days_overdue=days_overdue,
                customer_ltv=ltv,
                recovery_type=case.recovery_type,
                attempt_number=total_attempts + 1,
                has_dispute=dispute_flag,
                has_opt_out=customer.opt_out,
                has_hardship=hardship_flag,
            )
            cost = get_intervention_cost(act)
            erv = calculate_expected_recovery_value(amount, prob, cost)
            incr = calculate_incremental_recovery(prob, baseline_prob)

            policy_eval = await check_policy(db, case, act, expected_recovery_value=erv)
            await log_policy_check(db, case.id, act, policy_eval["result"], policy_eval["reason"])

            interventions.append({
                "action": act,
                "recovery_probability": prob,
                "intervention_cost": cost,
                "expected_recovery_value": erv,
                "incremental_recovery": incr,
                "baseline_probability": baseline_prob,
                "policy_status": policy_eval["result"],
                "policy_reason": policy_eval["reason"],
            })

        # 3. SELECT BEST ACTION — Highest ERV among ALLOWED actions
        allowed_interventions = [i for i in interventions if i["policy_status"] == "ALLOWED"]
        if allowed_interventions:
            # Sort by ERV descending
            allowed_interventions.sort(key=lambda x: x["expected_recovery_value"], reverse=True)
            best = allowed_interventions[0]
            recommended_action = best["action"]
            case.recovery_probability = best["recovery_probability"]
        else:
            # Check if any requires approval
            approval_items = [i for i in interventions if i["policy_status"] == "REQUIRES_APPROVAL"]
            if approval_items:
                approval_items.sort(key=lambda x: x["expected_recovery_value"], reverse=True)
                recommended_action = approval_items[0]["action"]
                case.recovery_probability = approval_items[0]["recovery_probability"]
            else:
                recommended_action = "STOP"
                case.recovery_probability = 0.0

        # Calculate risk score (0-100)
        risk_score = round(min(100, (1 - (case.recovery_probability or 0.5)) * 60 + (min(amount, 100000) / 100000) * 40), 1)
        case.risk_score = risk_score
        await db.flush()

        # 4. EXPLAINABILITY
        selected_erv = next((i["expected_recovery_value"] for i in interventions if i["action"] == recommended_action), 0.0)
        explanation_data = await mistral_agent_service.explain_decision(
            customer_name=customer.name,
            amount=amount,
            root_cause=case.root_cause,
            selected_action=recommended_action,
            erv=selected_erv,
            alternatives=interventions,
        )

        agent_explanation = f"{explanation_data.get('why')} {explanation_data.get('why_this_action')}"

        # Persist AgentDecision
        decision = AgentDecision(
            case_id=case.id,
            reasoning=agent_explanation,
            interventions_evaluated=interventions,
            selected_action=recommended_action,
            why_selected=explanation_data.get("why_this_action"),
            why_not_alternatives=explanation_data.get("why_not_alternatives", {}),
        )
        db.add(decision)
        await db.flush()

        return {
            "case_id": case.id,
            "root_cause": case.root_cause,
            "confidence": case.confidence or 0.85,
            "evidence": case.evidence or [],
            "interventions": interventions,
            "recommended_action": recommended_action,
            "agent_explanation": agent_explanation,
            "why_not_alternatives": explanation_data.get("why_not_alternatives", {}),
        }

    async def run_agent_on_case(
        self,
        db: AsyncSession,
        case_id: int,
        forced_action: Optional[str] = None,
        language: str = "english"
    ) -> Dict[str, Any]:
        """
        Full autonomous single-step execution:
        Analyze → Validate Policy → Execute → Observe → Return outcome.
        If the action fails, the caller/agent can trigger next step re-evaluation.
        """
        analysis = await self.analyze_case(db, case_id)

        chosen_action = forced_action or analysis["recommended_action"]
        chosen_interv = next((i for i in analysis["interventions"] if i["action"] == chosen_action), None)
        if not chosen_interv:
            raise ValueError(f"Action {chosen_action} is not valid for case {case_id}")

        query = (
            select(RecoveryCase)
            .options(selectinload(RecoveryCase.customer))
            .where(RecoveryCase.id == case_id)
        )
        case = (await db.execute(query)).scalar_one()

        # Policy validation
        policy_eval = await check_policy(
            db, case, chosen_action, expected_recovery_value=chosen_interv["expected_recovery_value"]
        )

        # Execution
        result = await action_executor.execute_action(
            db=db,
            case=case,
            action_type=chosen_action,
            probability=chosen_interv["recovery_probability"],
            cost=chosen_interv["intervention_cost"],
            erv=chosen_interv["expected_recovery_value"],
            incremental=chosen_interv["incremental_recovery"],
            baseline_prob=chosen_interv["baseline_probability"],
            policy_result=policy_eval,
            language=language,
            explanation=analysis["agent_explanation"]
        )

        return result


recovery_agent = RecoveryAgent()
