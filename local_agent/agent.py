from .api_client import ApiClient
from .composer import compose_answer
from .models import AgentAnswer, RoutingDecision
from .router import decide_route


class Agent:
    """Ties the three steps together: route -> call the real API -> compose.
    This is the local stand-in for what SKILL.md tells any autonomous agent
    to do on its own; nothing here runs server-side or gets deployed.
    """

    def __init__(self, api_client: ApiClient | None = None, model: str | None = None):
        self.api_client = api_client or ApiClient()
        self.model = model

    def ask(self, user_prompt: str) -> AgentAnswer:
        decision = decide_route(user_prompt, model=self.model)
        api_response = self._call(decision)
        return compose_answer(user_prompt, decision.endpoint, api_response, model=self.model)

    def _call(self, decision: RoutingDecision) -> dict:
        if decision.endpoint == "is_action_allowed":
            return self.api_client.is_action_allowed(decision.query_or_action, context=decision.context)
        if decision.endpoint == "search":
            params = {"document_type": decision.document_type} if decision.document_type else {}
            return self.api_client.search(decision.query_or_action, **params)
        if decision.endpoint == "sections":
            return self.api_client.get_section(decision.query_or_action)
        if decision.endpoint == "sections_related":
            return self.api_client.get_related(decision.query_or_action)
        if decision.endpoint == "penalties":
            return self.api_client.penalties(query=decision.query_or_action)
        if decision.endpoint == "permits":
            return self.api_client.permits(query=decision.query_or_action)
        raise ValueError(f"unknown endpoint: {decision.endpoint}")  # pragma: no cover - Literal-exhaustive
