"""OpenAI-compatible LLM client.

Provider-agnostic: works against any OpenAI-compatible chat-completions endpoint
(OpenRouter by default, but also OpenAI, Together, local vLLM, etc.). The
base URL, model and API key are all driven by config + environment so nothing
is hard-coded to a single vendor.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - import guard
    raise ImportError(
        "The 'openai' package is required. Install with: pip install openai"
    ) from exc


class LLMError(RuntimeError):
    """Raised when the LLM cannot return a usable response after retries."""


@dataclass
class LLMConfig:
    base_url: str = "https://openrouter.ai/api/v1"
    model: str = "anthropic/claude-3.5-sonnet"
    api_key_env: str = "OPENROUTER_API_KEY"
    temperature: float = 0.8
    max_tokens: int = 4096
    max_retries: int = 4
    request_timeout: float = 120.0
    extra_headers: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, gen: Dict[str, Any]) -> "LLMConfig":
        return cls(
            base_url=gen.get("base_url", cls.base_url),
            model=gen.get("model", cls.model),
            api_key_env=gen.get("api_key_env", cls.api_key_env),
            temperature=float(gen.get("temperature", cls.temperature)),
            max_tokens=int(gen.get("max_tokens", cls.max_tokens)),
            max_retries=int(gen.get("max_retries", cls.max_retries)),
            request_timeout=float(gen.get("request_timeout", cls.request_timeout)),
            extra_headers=dict(gen.get("extra_headers", {}) or {}),
        )


class LLMClient:
    """Thin wrapper around an OpenAI-compatible chat endpoint with JSON helpers."""

    def __init__(self, config: LLMConfig):
        self.config = config
        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            raise LLMError(
                f"No API key found. Set the {config.api_key_env} environment "
                f"variable (endpoint: {config.base_url})."
            )
        self._client = OpenAI(
            base_url=config.base_url,
            api_key=api_key,
            timeout=config.request_timeout,
        )

    # -- raw completion ----------------------------------------------------

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Return the assistant message text, retrying on transient failures."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        last_err: Optional[Exception] = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                resp = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=(
                        self.config.temperature if temperature is None else temperature
                    ),
                    max_tokens=max_tokens or self.config.max_tokens,
                    extra_headers=self.config.extra_headers or None,
                )
                content = resp.choices[0].message.content
                if content:
                    return content
                last_err = LLMError("Empty completion content.")
            except Exception as exc:  # noqa: BLE001 - retry on any API error
                last_err = exc
            sleep = min(2 ** attempt, 30)
            time.sleep(sleep)
        raise LLMError(
            f"LLM request failed after {self.config.max_retries} attempts: {last_err}"
        )

    # -- structured helpers -------------------------------------------------

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """Complete and parse a single JSON object/array from the response."""
        text = self.complete(
            system, user, temperature=temperature, max_tokens=max_tokens
        )
        return extract_json(text)

    def complete_jsonl(
        self,
        system: str,
        user: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> List[Any]:
        """Complete and parse a list of JSON objects (a JSON array or JSONL)."""
        text = self.complete(
            system, user, temperature=temperature, max_tokens=max_tokens
        )
        return extract_json_list(text)


# ---------------------------------------------------------------------------
# Parsing helpers (robust to code fences and minor LLM formatting noise).
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```(?:json|jsonl)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_OPEN_FENCE_RE = re.compile(r"^\s*```(?:json|jsonl)?\s*", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    # Handle an *unterminated* opening fence (e.g. truncated ```json output).
    return _OPEN_FENCE_RE.sub("", text).strip()


def _salvage_json_objects(text: str) -> List[Any]:
    """Recover as many complete top-level JSON objects as possible.

    Tolerant of a truncated trailing object (e.g. when the model hit its
    max_tokens limit mid-array): every fully-formed object before the cut is
    still returned.
    """
    decoder = json.JSONDecoder()
    objs: List[Any] = []
    i, n = 0, len(text)
    while i < n:
        brace = text.find("{", i)
        if brace == -1:
            break
        try:
            obj, end = decoder.raw_decode(text, brace)
            objs.append(obj)
            i = end
        except json.JSONDecodeError:
            i = brace + 1
    return objs


def extract_json(text: str) -> Any:
    """Extract the first JSON object or array from arbitrary LLM text."""
    cleaned = _strip_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fall back to locating the outermost bracketed region.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = cleaned.find(open_ch)
        end = cleaned.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                continue
    # Last resort: repair a response truncated at max_tokens by closing open
    # strings/brackets at the last structurally-valid boundary.
    repaired = _repair_truncated_json(cleaned)
    if repaired is not None:
        return repaired
    raise LLMError(f"Could not parse JSON from response:\n{text[:500]}")


def _close_json(frag: str) -> Optional[str]:
    """Append the closers needed to balance a JSON fragment, or None if the
    fragment ends inside a string (so this cut point is unusable)."""
    stack: List[str] = []
    in_str = False
    esc = False
    for ch in frag:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in "}]":
            if not stack:
                return None
            stack.pop()
    if in_str:
        return None
    f = frag.rstrip()
    while f.endswith(","):
        f = f[:-1].rstrip()
    return f + "".join(reversed(stack))


def _repair_truncated_json(text: str) -> Any:
    """Recover the largest valid JSON prefix of a truncated object/array.

    Tries candidate cut points (after each '}' ']' '"' and before each ',')
    from longest to shortest, closing open structures at each, and returns the
    first that parses.
    """
    start = next((i for i, c in enumerate(text) if c in "{["), -1)
    if start == -1:
        return None
    s = text[start:]
    cuts = {len(s)}
    for i, ch in enumerate(s):
        if ch in '}]"':
            cuts.add(i + 1)
        elif ch == ",":
            cuts.add(i)
    for cut in sorted(cuts, reverse=True):
        closed = _close_json(s[:cut])
        if closed is None:
            continue
        try:
            return json.loads(closed)
        except json.JSONDecodeError:
            continue
    return None


def extract_json_list(text: str) -> List[Any]:
    """Extract a list of JSON objects, accepting either a JSON array or JSONL."""
    cleaned = _strip_fences(text)
    # Try a single JSON array first.
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Some models wrap the array in a key; take the first list value.
            for v in data.values():
                if isinstance(v, list):
                    return v
            return [data]
    except json.JSONDecodeError:
        pass
    # Fall back to line-by-line JSONL parsing.
    rows: List[Any] = []
    for line in cleaned.splitlines():
        line = line.strip().rstrip(",")
        if not line or line in "[]":
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if rows:
        return rows
    # Last resort: salvage complete objects from a truncated/malformed array.
    salvaged = _salvage_json_objects(cleaned)
    if salvaged:
        return salvaged
    raise LLMError(f"Could not parse JSON list from response:\n{text[:500]}")
