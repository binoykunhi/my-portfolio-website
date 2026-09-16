from openai import OpenAI
from typing import Generator, Optional

class LLMClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.system_prompt = "You are a helpful voice assistant. Keep your responses concise and conversational."

    def generate_batch(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4o", # Or gpt-3.5-turbo
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        stream = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def judge_interaction(self, transcript: str, response: str) -> dict:
        """
        Asks the LLM to judge the quality of the interaction.
        """
        prompt = f"""
        Rate the following voice interaction on a scale of 1-5 (5 being best).
        Consider:
        1. Accuracy of the transcript (implied context).
        2. Relevance and helpfulness of the response.
        
        Transcript: "{transcript}"
        Response: "{response}"
        
        Return ONLY a JSON object with keys "score" (float) and "reason" (string).
        """
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4o", # Use a smart model for judging
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            import json
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            return {"score": 0.0, "reason": f"Error judging: {e}"}
