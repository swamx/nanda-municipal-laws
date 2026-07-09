import json

from .claude_cli import ask_structured
from .models import AgentAnswer
from .skill_context import load_skill_md

_ANSWER_SCHEMA = AgentAnswer.model_json_schema()

_SYSTEM_PROMPT_TEMPLATE = """You are an autonomous agent composing a final answer for a user \
from the Municipal Law Skill's response below, following SKILL.md's own "Composing your final \
answer" and "Rules" sections exactly:
- Never state a fact or number that isn't literally present in the API response's text/reasoning.
- Always cite section_number and url for anything you quote or paraphrase, in `sources`.
- If citations/results are empty, say so plainly rather than answering from general knowledge.
- Never repeat an `allowed` value as a settled legal conclusion without reflecting what \
`reasoning` actually says (e.g. an absence-of-restriction inference is weaker than an explicit \
statement - see SKILL.md's confidence rubric).

Keep `answer` concise - 2 to 4 sentences covering the verdict, the key caveat, and the citation. \
Put any additional supporting detail in `reasoning` instead of padding out `answer`. This is a \
CLI chat tool, not a legal memo.

--- SKILL.md ---
{skill_md}
"""


def compose_answer(
    user_prompt: str,
    endpoint: str,
    api_response: dict,
    *,
    model: str | None = None,
) -> AgentAnswer:
    """Asks Claude Code (via the CLI) to synthesize the final
    {answer, sources, reasoning} shape from a raw Municipal Law Skill API
    response, per SKILL.md's own contract - this project's server never
    does this itself; composing the natural-language answer is always the
    calling agent's job, which is exactly what this function simulates.
    """
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(skill_md=load_skill_md())
    prompt = (
        f"User's question: {user_prompt!r}\n\n"
        f"Endpoint called: {endpoint}\n\n"
        f"Raw API response:\n{json.dumps(api_response, indent=2)}"
    )
    raw = ask_structured(
        prompt,
        system_prompt=system_prompt,
        json_schema=_ANSWER_SCHEMA,
        model=model,
    )
    return AgentAnswer.model_validate(raw)
