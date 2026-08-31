import re
import time
from typing import List, Tuple

try:
    from .llm import call_llm
    from .models import DebateResponse, Turn
    from .prompts import build_against_prompt, build_for_prompt, build_judge_prompt
except ImportError:
    from llm import call_llm
    from models import DebateResponse, Turn
    from prompts import build_against_prompt, build_for_prompt, build_judge_prompt


def _call_llm_with_retry(prompt: str, retries: int = 1, max_output_tokens: int = 800) -> str:
    """Call LLM with up to `retries` additional retry on failure."""
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            return call_llm(prompt, max_output_tokens=max_output_tokens)
        except Exception as e:
            last_err = e
    if last_err:
        raise last_err
    raise RuntimeError("Unknown error during LLM invocation.")


def parse_judge_output(output: str) -> Tuple[str, str]:
    """Parse judge response into (winner, reasoning).
    
    Robustly handles markdown asterisks, whitespace variations, and case.
    Defaults winner to 'UNDECIDED' if parsing fails completely.
    """
    if not output or not output.strip():
        return "UNDECIDED", "No evaluation received from judge."

    cleaned_output = output.strip()
    winner = "UNDECIDED"
    reasoning = cleaned_output

    # 1. Primary Regex: WINNER: <FOR or AGAINST> with possible markdown (e.g. **WINNER:** **FOR**)
    winner_match = re.search(
        r"(?:WINNER|VICTOR|DECISION)\s*[:\-]?\s*[\*\_]*\s*(FOR|AGAINST)\b",
        cleaned_output,
        re.IGNORECASE,
    )
    if winner_match:
        winner = winner_match.group(1).upper()
    else:
        # Fallback: Check if output starts with or clearly declares FOR or AGAINST
        first_lines = "\n".join(cleaned_output.splitlines()[:3])
        if re.search(r"\bFOR\b", first_lines, re.IGNORECASE) and not re.search(r"\bAGAINST\b", first_lines, re.IGNORECASE):
            winner = "FOR"
        elif re.search(r"\bAGAINST\b", first_lines, re.IGNORECASE) and not re.search(r"\bFOR\b", first_lines, re.IGNORECASE):
            winner = "AGAINST"

    # 2. Extract REASONING: <text>
    reasoning_match = re.search(
        r"(?:REASONING|JUSTIFICATION|RATIONALE)\s*[:\-]?\s*[\*\_]*\s*(.*)",
        cleaned_output,
        re.IGNORECASE | re.DOTALL,
    )
    if reasoning_match:
        extracted = reasoning_match.group(1).strip()
        if extracted:
            reasoning = extracted
    else:
        # If no explicit REASONING tag, remove any WINNER line and use the rest
        lines = [
            line for line in cleaned_output.splitlines()
            if not re.search(r"^(?:\*\*|\*|#)*\s*(?:WINNER|VICTOR|DECISION)", line, re.IGNORECASE)
        ]
        fallback_reasoning = "\n".join(lines).strip()
        if fallback_reasoning:
            reasoning = fallback_reasoning

    # Strip any leading markdown asterisks/dashes from reasoning
    reasoning = re.sub(r"^[\*\#\-\s]+", "", reasoning).strip()

    return winner, reasoning


def run_debate(topic: str, num_rounds: int = 3) -> DebateResponse:
    """Run a multi-round debate between FOR and AGAINST agents and judge the winner.

    Args:
        topic: The topic/resolution for the debate.
        num_rounds: Number of rounds (each round has FOR followed by AGAINST).

    Returns:
        DebateResponse containing topic, list of turns, winner, and judge reasoning.
    """
    transcript: List[Turn] = []

    for round_num in range(1, num_rounds + 1):
        # 1. FOR speaker
        for_prompt = build_for_prompt(topic, transcript)
        try:
            for_text = _call_llm_with_retry(for_prompt, retries=1, max_output_tokens=500)
            transcript.append(Turn(round=round_num, speaker="FOR", text=for_text))
        except Exception as e:
            transcript.append(
                Turn(
                    round=round_num,
                    speaker="SYSTEM",
                    text=f"Error generating FOR argument in round {round_num}: {str(e)}",
                )
            )

        # Spacing between turns to respect free-tier rate limits
        time.sleep(2.5)

        # 2. AGAINST speaker (sees FOR's latest argument in transcript)
        against_prompt = build_against_prompt(topic, transcript)
        try:
            against_text = _call_llm_with_retry(against_prompt, retries=1, max_output_tokens=500)
            transcript.append(Turn(round=round_num, speaker="AGAINST", text=against_text))
        except Exception as e:
            transcript.append(
                Turn(
                    round=round_num,
                    speaker="SYSTEM",
                    text=f"Error generating AGAINST argument in round {round_num}: {str(e)}",
                )
            )

        time.sleep(2.5)

    # 3. Judge evaluation
    judge_prompt = build_judge_prompt(topic, transcript)
    try:
        judge_output = _call_llm_with_retry(judge_prompt, retries=1, max_output_tokens=400)
        winner, reasoning = parse_judge_output(judge_output)
    except Exception as e:
        winner = "UNDECIDED"
        reasoning = f"Judge failed to evaluate debate: {str(e)}"
        transcript.append(
            Turn(
                round=num_rounds,
                speaker="SYSTEM",
                text=f"Error during judge evaluation: {str(e)}",
            )
        )

    return DebateResponse(
        topic=topic,
        turns=transcript,
        winner=winner,
        reasoning=reasoning,
    )


