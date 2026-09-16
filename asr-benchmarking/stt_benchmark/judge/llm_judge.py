import json
import jiwer
from openai import OpenAI
from stt_benchmark.config import OPENAI_API_KEY

class LLMJudge:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def judge_transcripts(self, transcripts: dict[str, str]) -> dict:
        """
        Judge the quality of transcripts by generating a consensus and calculating WER.

        Args:
            transcripts (dict): A dictionary where keys are provider names and values are transcripts.

        Returns:
            dict: A dictionary containing the winner, reasoning, consensus transcript, and WERs.
        """
        
        prompt = f"""
        You are an expert linguist and audio transcription judge.
        I will provide you with transcripts from different Speech-to-Text providers for the same audio file.
        
        Your task is to:
        1. Analyze all transcripts to determine the most likely correct transcription (Consensus Transcript).
        2. Evaluate them and determine which one is the best based on accuracy and readability.
        
        Here are the transcripts:
        {json.dumps(transcripts, indent=2)}
        
        Please output your judgment in JSON format with the following keys:
        - "consensus_transcript": The text you believe is the most accurate representation of the audio.
        - "winner": The name of the provider with the best transcript.
        - "reasoning": A brief explanation of why this provider was chosen.
        """

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        consensus = result["consensus_transcript"]
        
        # Calculate WER
        wers = {}
        transformation = jiwer.Compose([
            jiwer.ToLowerCase(),
            jiwer.RemovePunctuation(),
            jiwer.RemoveMultipleSpaces(),
            jiwer.Strip(),
            jiwer.ExpandCommonEnglishContractions(),
            lambda x: [sentence.split() for sentence in x]
        ])

        for provider, text in transcripts.items():
            wer = jiwer.wer(
                consensus, 
                text, 
                reference_transform=transformation, 
                hypothesis_transform=transformation
            )
            wers[provider] = round(wer, 4)

        result["wers"] = wers
        return result
