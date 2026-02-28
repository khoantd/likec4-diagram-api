"""AI service for generating LikeC4 DSL from natural language descriptions."""

from __future__ import annotations

LIKEC4_SYSTEM_PROMPT = """You are an expert in LikeC4 (architecture-as-code DSL). Your task is to generate valid LikeC4 source code from a user's natural language description of a system or architecture.

## LikeC4 DSL rules

1. **Model block** – Define elements and relations inside `model { ... }`.

2. **Element kinds** (use lowercase): `actor`, `system`, `container`, `component`. Syntax:
   - `id = kind 'Display Title' 'optional short summary' { ... }`
   - Or nested: `parentId = system 'Parent' { childId = container 'Child' { } }`
   - Ids are camelCase or lowercase with no spaces (e.g. `webApp`, `api`, `database`).

3. **Relations** (inside model or inside element body):
   - `source -> target 'label'` or `-> target 'label'` when inside the source element body.
   - Optional relation kind: `source -[relationshipKind]-> target 'label'`.

4. **Strings**: Use single quotes for titles/descriptions: `'Title'`, `'Multi line\ndescription'`.

5. **Views block** – Define views in `views { ... }`:
   - `view viewId { title 'Title' include * }` – include all elements.
   - `view viewId of elementId { include * }` – view focused on an element and its children.
   - Prefer at least one default view that includes `*`.

6. **Output**: Respond with ONLY the LikeC4 code, no markdown code fence, no explanation before or after. If the user asks for explanation, add a single short comment at the top of the file starting with `// ` with one line explanation; otherwise no comments.
"""

_EXTEND_SYSTEM_ADDENDUM = """
## Extending an existing model

When an existing LikeC4 DSL is provided:
- Understand the current model before making changes.
- Preserve all existing element IDs, hierarchy, and relations unless the user explicitly asks to change them.
- Add new elements, relations, or views using the same naming conventions already used in the DSL.
- Return the COMPLETE updated DSL—not just the additions.
"""


def _extract_dsl_from_content(content: str) -> tuple[str, str | None]:
    """Extract LikeC4 DSL from model response; optionally return explanation if present."""
    text = content.strip()
    explanation: str | None = None
    # If model wrapped in ```likec4 or ```, unwrap
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    # First line as explanation if it's a comment
    if text.startswith("//"):
        first_line, _, rest = text.partition("\n")
        explanation = first_line[2:].strip()
        text = rest.strip()
    return text, explanation if explanation else None


def generate_likec4_dsl(
    prompt: str,
    hint: str | None,
    *,
    api_key: str,
    model: str,
    base_url: str | None = None,
    current_dsl: str | None = None,
    view_id: str | None = None,
) -> tuple[str, str | None]:
    """
    Call OpenAI-compatible API to generate LikeC4 DSL from a natural language prompt.

    When *current_dsl* is provided the model is instructed to extend the existing
    architecture rather than generate from scratch.

    Returns (likec4_dsl, explanation).
    Raises ValueError if the API call fails or returns empty content.
    """
    try:
        from openai import OpenAI
    except ImportError as e:
        raise ValueError(
            "AI support requires the 'openai' package. Install with: pip install likec4-diagram-api[ai]"
        ) from e

    client_kw: dict = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url
    client = OpenAI(**client_kw)

    system_prompt = LIKEC4_SYSTEM_PROMPT + (_EXTEND_SYSTEM_ADDENDUM if current_dsl else "")

    user_content = prompt
    if hint:
        user_content = f"{prompt}\n\nHint: {hint}"
    if current_dsl:
        dsl_block = f"\n\nExisting LikeC4 model:\n```\n{current_dsl}\n```"
        if view_id:
            dsl_block += f"\n\nCurrently active view: {view_id}"
        user_content = user_content + dsl_block

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=4096,
    )
    choice = response.choices[0] if response.choices else None
    if not choice or not choice.message or not choice.message.content:
        raise ValueError("AI returned no content")
    content = choice.message.content.strip()
    if not content:
        raise ValueError("AI returned empty content")
    return _extract_dsl_from_content(content)
