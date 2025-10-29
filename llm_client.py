import openai
import json
import logging
import os

logger = logging.getLogger("llm_client")

class LLMClient:
    def __init__(self, config: dict):
        openai.api_key = os.getenv("OPENAI_API_KEY_HTEC")
        openai.base_url = config.get("base_url")
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.0)
        self.max_tokens = config.get("max_tokens", 1000)

    def run(self, prompt: str):
        try:
            resp = openai.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                messages=[
                    {"role":"system","content":"You are a professional Talent Acquisition interviewer"},
                    {"role":"user","content":prompt}
                ],
            )
            text = resp.choices[0].message.content
            return text
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise ValueError("LLM evaluation failed. LLM is not accessible.")

def safe_parse_json(text: str):
    """Attempt to parse LLM output as JSON"""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        print("Failed to parse LLM output")
        return {}