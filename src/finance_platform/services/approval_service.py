from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from finance_platform.errors.exceptions import (
    NotFoundError,
    BusinessRuleError,
    ApprovalChainError,
    ApprovalPermissionError,
)
from finance_platform.models.approval import ApprovalChain, ApprovalDecision, ApprovalStep
from finance_platform.models.base import ApprovalState
from finance_platform.state_machines.approval import ApprovalChainStateMachine


class ApprovalService:
    def __init__(self) -> None:
        self._chains: Dict[str, ApprovalChain] = {}

    def create_approval_chain(
        self,
        entity_type: str,
        entity_id: str,
        title: str,
        amount: float,
        initiated_by: str,
        steps: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ApprovalChain:
        chain = ApprovalChain(
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            amount=amount,
            initiated_by=initiated_by,
            state=ApprovalState.PENDING,
            tags=tags or [],
            metadata=metadata or {},
        )
        if steps:
            chain.steps = [ApprovalStep(**s) for s in steps]
        self._chains[chain.id] = chain
        return chain

    def get_approval_chain(self, chain_id: str) -> ApprovalChain:
        chain = self._chains.get(chain_id)
        if not chain or chain.is_deleted:
            raise NotFoundError(f"ApprovalChain {chain_id} not found", resource_type="ApprovalChain", resource_id=chain_id)
        return chain

    def find_chain_for_entity(self, entity_type: str, entity_id: str) -> Optional[ApprovalChain]:
        for chain in self._chains.values():
            if chain.entity_type == entity_type and chain.entity_id == entity_id and not chain.is_deleted:
                return chain
        return None

    def list_chains(
        self,
        entity_type: Optional[str] = None,
        state: Optional[ApprovalState] = None,
        initiated_by: Optional[str] = None,
    ) -> List[ApprovalChain]:
        results = [c for c in self._chains.values() if not c.is_deleted]
        if entity_type:
            results = [c for c in results if c.entity_type == entity_type]
        if state:
            results = [c for c in results if c.state == state]
        if initiated_by:
            results = [c for c in results if c.initiated_by == initiated_by]
        return results

    def add_step(self, chain_id: str, step_order: int, approver_id: str, **kwargs: Any) -> ApprovalStep:
        chain = self.get_approval_chain(chain_id)
        if chain.state != ApprovalState.PENDING:
            raise BusinessRuleError("Cannot add steps to a non-pending approval chain")
        step = ApprovalStep(step_order=step_order, approver_id=approver_id, **kwargs)
        chain.steps.append(step)
        chain.steps.sort(key=lambda s: s.step_order)
        chain.touch()
        return step

    def approve_step(self, chain_id: str, approver_id: str, comments: Optional[str] = None) -> ApprovalChain:
        chain = self.get_approval_chain(chain_id)
        step = chain.current_step_obj
        if not step:
            raise ApprovalChainError("No current step found in approval chain")
        if step.approver_id != approver_id:
            raise ApprovalPermissionError(f"User {approver_id} is not the assigned approver for this step")
        step.decision = ApprovalDecision(
            approver_id=approver_id,
            state=ApprovalState.APPROVED,
            comments=comments,
        )
        step.state = ApprovalState.APPROVED
        if chain.is_fully_approved:
            sm = ApprovalChainStateMachine(chain)
            sm.transition(ApprovalState.APPROVED, context={"resolved_by": approver_id})
        else:
            chain.advance_step()
        chain.touch()
        return chain

    def reject_step(self, chain_id: str, approver_id: str, comments: Optional[str] = None) -> ApprovalChain:
        chain = self.get_approval_chain(chain_id)
        step = chain.current_step_obj
        if not step:
            raise ApprovalChainError("No current step found in approval chain")
        if step.approver_id != approver_id:
            raise ApprovalPermissionError(f"User {approver_id} is not the assigned approver for this step")
        step.decision = ApprovalDecision(
            approver_id=approver_id,
            state=ApprovalState.REJECTED,
            comments=comments,
        )
        step.state = ApprovalState.REJECTED
        sm = ApprovalChainStateMachine(chain)
        sm.transition(ApprovalState.REJECTED, context={"resolved_by": approver_id})
        chain.touch()
        return chain

    def escalate_step(
        self,
        chain_id: str,
        approver_id: str,
        escalation_user_id: str,
        reason: Optional[str] = None,
    ) -> ApprovalChain:
        chain = self.get_approval_chain(chain_id)
        step = chain.current_step_obj
        if not step:
            raise ApprovalChainError("No current step found in approval chain")
        if step.approver_id != approver_id:
            raise ApprovalPermissionError(f"User {approver_id} is not the assigned approver")
        step.state = ApprovalState.ESCALATED
        step.escalation_user_id = escalation_user_id
        if reason:
            step.metadata["escalation_reason"] = reason
        chain.touch()
        return chain

    def delegate_step(
        self,
        chain_id: str,
        from_approver_id: str,
        to_approver_id: str,
        reason: Optional[str] = None,
    ) -> ApprovalChain:
        chain = self.get_approval_chain(chain_id)
        step = chain.current_step_obj
        if not step:
            raise ApprovalChainError("No current step found in approval chain")
        if step.approver_id != from_approver_id:
            raise ApprovalPermissionError(f"User {from_approver_id} is not the assigned approver")
        step.delegated_from = from_approver_id
        step.approver_id = to_approver_id
        if reason:
            step.metadata["delegation_reason"] = reason
        chain.touch()
        return chain

    def recall_chain(self, chain_id: str, user_id: str) -> ApprovalChain:
        chain = self.get_approval_chain(chain_id)
        if chain.initiated_by != user_id:
            raise ApprovalPermissionError("Only the initiator can recall an approval chain")
        sm = ApprovalChainStateMachine(chain)
        sm.transition(ApprovalState.CANCELLED, context={"resolved_by": user_id})
        chain.touch()
        return chain

    def get_pending_approvals(self, approver_id: str) -> List[ApprovalChain]:
        results: List[ApprovalChain] = []
        for chain in self._chains.values():
            if chain.is_deleted or chain.state != ApprovalState.PENDING:
                continue
            step = chain.current_step_obj
            if step and step.approver_id == approver_id:
                results.append(chain)
        return results

    def get_approval_history(self, entity_type: str, entity_id: str) -> List[ApprovalChain]:
        chain = self.find_chain_for_entity(entity_type, entity_id)
        if not chain:
            return []
        return [chain]
