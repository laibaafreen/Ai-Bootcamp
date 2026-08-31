from typing import Any, List


def format_transcript(transcript: List[Any]) -> str:
    """Format a list of Turn objects or dicts into a readable transcript string."""
    if not transcript:
        return "No previous rounds (Opening Round)."
    formatted = []
    for item in transcript:
        if hasattr(item, "speaker") and hasattr(item, "text"):
            round_num = getattr(item, "round", "?")
            formatted.append(f"[Round {round_num} | {item.speaker}]:\n{item.text}")
        elif isinstance(item, dict):
            round_num = item.get("round", "?")
            speaker = item.get("speaker", "UNKNOWN")
            text = item.get("text", "")
            formatted.append(f"[Round {round_num} | {speaker}]:\n{text}")
        else:
            formatted.append(str(item))
    return "\n\n".join(formatted)


def build_for_prompt(topic: str, transcript: List[Any]) -> str:
    """Build the prompt for the FOR (Proposition) speaker arguing in favor of the topic."""
    history = format_transcript(transcript)
    return (
        f"You are a competitive debater arguing strictly IN FAVOR OF (FOR / Proposition) the following topic.\n\n"
        f"Topic / Resolution: \"{topic}\"\n\n"
        f"Debate Transcript So Far:\n{history}\n\n"
        f"Guidelines:\n"
        f"- Deliver a strong, persuasive, evidence-informed case supporting the resolution.\n"
        f"- If there are prior opposition arguments in the transcript, directly refute them with counter-reasoning.\n"
        f"- Keep your argument focused, clear, and punchy (approximately 150-250 words, 2-3 structured paragraphs).\n"
        f"- Do NOT include conversational filler, meta-announcements, or greetings. Output ONLY your direct speech."
    )


def build_against_prompt(topic: str, transcript: List[Any]) -> str:
    """Build the prompt for the AGAINST (Opposition) speaker arguing against the topic."""
    history = format_transcript(transcript)
    return (
        f"You are a competitive debater arguing strictly OPPOSING (AGAINST / Opposition) the following topic.\n\n"
        f"Topic / Resolution: \"{topic}\"\n\n"
        f"Debate Transcript So Far:\n{history}\n\n"
        f"Guidelines:\n"
        f"- Deliver a strong, persuasive, evidence-informed case against the resolution.\n"
        f"- Directly rebut the FOR debater's points and expose logical flaws or practical downsides.\n"
        f"- Keep your argument focused, clear, and punchy (approximately 150-250 words, 2-3 structured paragraphs).\n"
        f"- Do NOT include conversational filler, meta-announcements, or greetings. Output ONLY your direct speech."
    )


def build_judge_prompt(topic: str, transcript: List[Any]) -> str:
    """Build the prompt for the impartial judge evaluating the debate."""
    history = format_transcript(transcript)
    return (
        f"You are an impartial, world-class debate adjudicator evaluating the following debate.\n\n"
        f"Debate Resolution: \"{topic}\"\n\n"
        f"Complete Transcript:\n{history}\n\n"
        f"Adjudication Rules:\n"
        f"1. Objectively evaluate both sides on logic, argument strength, evidence quality, and rebuttal effectiveness.\n"
        f"2. You MUST pick a definitive winner: strictly choose 'FOR' or 'AGAINST' (ties are not permitted).\n"
        f"3. Provide 2-4 sentences of clear, balanced reasoning explaining exactly why that side won the debate.\n"
        f"4. Format your output EXACTLY as follows:\n\n"
        f"WINNER: <FOR or AGAINST>\n"
        f"REASONING: <2-4 sentences of reasoned justification>"
    )

