import inspect
from deepgram import DeepgramClient
from google.cloud import speech_v2

print("--- DEEPGRAM ---")
try:
    client = DeepgramClient(api_key="dummy")
    method = client.listen.v1.media.transcribe_file
    print(f"transcribe_file signature: {inspect.signature(method)}")
    print(f"transcribe_file doc: {method.__doc__}")
except Exception as e:
    print(f"Deepgram error: {e}")

print("\n--- GOOGLE V2 ---")
try:
    print(f"speech_v2.types dir: {[x for x in dir(speech_v2.types) if 'Config' in x]}")
except Exception as e:
    print(f"Google error: {e}")
