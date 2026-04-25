from __future__ import annotations

from typing import Any, Dict, List, Optional

from finance_platform.notifications.models import TemplateVariable


class TemplateEngine:
    def __init__(self) -> None:
        self._templates: Dict[str, Dict[str, str]] = {
            "approval_requested": {
                "title": "Approval Requested",
                "body": "Expense {expense_id} requires your approval.",
            },
            "approval_result": {
                "title": "Expense {result}",
                "body": "Your expense {expense_id} has been {result} by {reviewer_name}.",
            },
            "month_end_reminder": {
                "title": "Month-End Reminder",
                "body": "You have {pending_count} pending expenses that need attention before month-end close.",
            },
            "discrepancy_alert": {
                "title": "Discrepancy Detected",
                "body": "A discrepancy was found in expense {expense_id}: {discrepancy_detail}.",
            },
            "high_priority_debt": {
                "title": "High Priority Debt Alert",
                "body": "A high priority debt of {debt_amount} with {counterparty} requires immediate attention.",
            },
            "group_leader_reminder": {
                "title": "Amortization Group Reminder",
                "body": "You have pending items in amortization group {group_id} that require your review.",
            },
            "void_approval": {
                "title": "Void Approval Required",
                "body": "Expense {expense_id} has been marked for void and requires your approval.",
            },
        }

    def register_template(self, name: str, title: str, body: str) -> None:
        self._templates[name] = {"title": title, "body": body}

    def render(self, template_name: str, variables: Dict[str, str]) -> Dict[str, str]:
        template = self._templates.get(template_name)
        if template is None:
            return {"title": "Notification", "body": ""}
        title = template["title"]
        body = template["body"]
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            title = title.replace(placeholder, value)
            body = body.replace(placeholder, value)
        return {"title": title, "body": body}

    def list_templates(self) -> List[str]:
        return list(self._templates.keys())

    def get_template_variables(self, template_name: str) -> List[str]:
        import re

        template = self._templates.get(template_name)
        if template is None:
            return []
        text = template["title"] + " " + template["body"]
        return re.findall(r"\{(\w+)\}", text)
