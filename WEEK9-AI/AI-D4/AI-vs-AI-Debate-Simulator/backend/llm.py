import os
import time
import warnings
from dotenv import find_dotenv, load_dotenv
from google import genai
from google.genai import types

# Filter automatic function calling deprecation warning if raised by library
warnings.filterwarnings("ignore", category=UserWarning, module="google.genai")

# Load environment variables from .env file
load_dotenv(find_dotenv(usecwd=True))


def call_llm(
    prompt: str,
    model: str | None = None,
    max_output_tokens: int = 500,
    temperature: float = 0.7,
) -> str:
    """Send a prompt to Gemini LLM via google-genai client and return response text.
    
    Includes resilient rate-limit handling with progressive backoff to survive RPM limits.

    Args:
        prompt: The input prompt string.
        model: Optional model identifier. Defaults to GEMINI_MODEL env var or 'gemini-3.6-flash'.
        max_output_tokens: Maximum tokens to generate (default: 500).
        temperature: Generation temperature (default: 0.7).

    Returns:
        str: Response text from the model.

    Raises:
        ValueError: If GEMINI_API_KEY / GOOGLE_API_KEY is not set.
        RuntimeError: If the API call fails or returns empty content.
    """
    # Reload in case .env was modified at runtime
    load_dotenv(find_dotenv(usecwd=True))
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY or GOOGLE_API_KEY is not set in environment or .env file. "
            "Please configure your API key in the .env file."
        )

    selected_model = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    last_error = None
    for attempt in range(4):
        try:
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
            response = client.models.generate_content(
                model=selected_model,
                contents=prompt,
                config=config,
            )

            if response.text is not None:
                return response.text.strip()

            raise RuntimeError("Gemini returned an empty response.")
        except Exception as e:
            err_str = str(e)
            last_error = e
            if attempt < 3 and ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()):
                # Rate limit hit: sleep 8s, 12s, 16s to allow the RPM quota window to reset
                sleep_time = 8 + (attempt * 4)
                time.sleep(sleep_time)
                continue
            if attempt == 3:
                raise RuntimeError(f"Error calling LLM ({selected_model}): {err_str}") from last_error
            time.sleep(1)

    raise RuntimeError(f"Error calling LLM ({selected_model}): {str(last_error)}") from last_error




