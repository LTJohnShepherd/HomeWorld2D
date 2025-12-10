Comment & Docstring Style Guide

Purpose
- Make code comments concise, factual, and helpful to a reader who already understands Python.
- Prefer docstrings for modules, classes, and public functions. Use triple-quoted strings (PEP 257 style).
- Use inline `#` comments sparingly to explain non-obvious implementation details or reasoning.

Tone & Content
- Use the imperative mood for docstrings describing actions (e.g., "Return the entry for id").
- Keep sentences short. One idea per sentence.
- Avoid commenting obvious code (e.g., `i += 1  # increment`).
- Prefer describing why something is done when not obvious, not what the code does.

Docstrings
- Top-level module: brief description of purpose and any high-level contracts.
- Class docstring: describe the responsibilities and public attributes.
- Public function/method: describe behavior, parameters, return values, and side effects briefly.

Inline comments
- Use `#` to explain: edge cases, rationale, units for numeric constants, or cross-file contracts.
- Keep to one short comment per line; place above the code block when longer explanation needed.

Examples
- Good:
    # Use a kite-shaped overlay to match the visual reference image.
    draw_dalton(...)

- Bad:
    x = x + 1  # add one

Process for automated edits
- Convert long, ambiguous comments into short clarifying docstrings.
- Remove redundant or obvious comments.
- Add docstrings to modules/classes that lack them.
- Preserve comments that indicate TODOs or important caveats.

Naming
- Use `COMMENT_STYLE.md` in `docs/` as the canonical source.

If you prefer adjustments to tone or stricter rules (length limits, Sphinx-style parameter docs), tell me and I'll adapt the guide and subsequent edits.