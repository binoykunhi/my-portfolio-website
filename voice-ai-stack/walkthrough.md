# Voice AI Playground Walkthrough

## Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure Keys**:
   Copy `.env.example` to `.env` and add your API keys:
   ```bash
   cp .env.example .env
   # Edit .env with OPENAI_API_KEY and ELEVENLABS_API_KEY
   ```

## Running the Playground
Start the application:
```bash
python main.py
```

### Menu Options
1. **Run Batch Pipeline**: Speak a sentence. The system will wait for silence, process everything sequentially, and reply.
2. **Run Streaming Pipeline**: Speak a sentence. The system will process streams in parallel (where possible) and reply faster.
3. **Run Both**: Runs Batch then Streaming on the same turn logic (sequential execution for comparison).

## Viewing Results
- **Console Output**: Shows real-time status and transcriptions.
- **Metrics**: After each turn, metrics are calculated and saved.
- **Logs**: Check `results.jsonl` for detailed JSON logs containing all timestamps and metrics.

## Troubleshooting
- **Microphone Issues**: Ensure your default microphone is set correctly in your OS settings.
- **API Errors**: Check your `.env` file and ensure you have credits/quota for OpenAI and ElevenLabs.
