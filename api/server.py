#!/usr/bin/env python3
"""
Flask API Server for Experiments Lab
Bridges the static website UI with Python benchmarking tools
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import tempfile
from werkzeug.utils import secure_filename

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'asr-benchmarking'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'voice-ai-stack'))

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

UPLOAD_FOLDER = tempfile.gettempdir()
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a', 'flac', 'ogg'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/asr/benchmark', methods=['POST'])
def asr_benchmark():
    """
    ASR Benchmarking Endpoint
    Accepts audio file + provider list, runs benchmarks, returns results
    """
    try:
        # Check file
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get providers
        import json
        providers_json = request.form.get('providers', '[]')
        selected_providers = json.loads(providers_json)
        
        if not selected_providers:
            return jsonify({'error': 'No providers selected'}), 400
        
        # Import and run benchmark
        try:
            from stt_benchmark.providers.openai_stt import OpenAIProvider
            from stt_benchmark.providers.deepgram_stt import DeepgramProvider
            from stt_benchmark.providers.assemblyai_stt import AssemblyAIProvider
            from stt_benchmark.providers.google_stt import GoogleV1Provider, GoogleV2Provider
            from stt_benchmark.providers.aws_stt import AWSTranscribeProvider
            from stt_benchmark.judge.llm_judge import LLMJudge
        except ImportError as e:
            return jsonify({'error': f'Failed to import providers: {str(e)}'}), 500
        
        # Map provider names to instances (lazy initialization)
        def get_provider(key):
            provider_classes = {
                'openai': (OpenAIProvider, 'whisper-1'),
                'deepgram': (DeepgramProvider, 'nova-2'),
                'assemblyai': (AssemblyAIProvider, None),
                'google-v1': (GoogleV1Provider, 'default'),
                'google-v2-chirp2': (GoogleV2Provider, 'chirp2'),
                'google-v2-chirp3': (GoogleV2Provider, 'chirp3'),
                'aws': (AWSTranscribeProvider, None),
            }
            if key in provider_classes:
                provider_class, model = provider_classes[key]
                try:
                    return provider_class(), model, None
                except Exception as e:
                    error_msg = str(e)
                    print(f"Failed to initialize {key}: {error_msg}")
                    return None, None, error_msg
            return None, None, f"Unknown provider: {key}"
        
        # Run transcriptions
        transcripts = {}
        latencies = {}
        results = []
        
        for provider_key in selected_providers:
            provider_instance, model, error = get_provider(provider_key)
            
            if provider_instance is None:
                transcripts[provider_key] = f"ERROR: {error}"
                latencies[provider_key] = 0.0
                continue
            
            display_name = f"{provider_key}_{model}" if model else provider_key
            
            try:
                # Providers may return (transcript, latency) or (transcript, latency, timing_info)
                result = provider_instance.transcribe(filepath, model=model)
                
                if len(result) == 3:
                    transcript, latency, timing_info = result
                    # Log detailed timing breakdown
                    print(f"[LATENCY BREAKDOWN] {display_name}: {json.dumps(timing_info)}")
                else:
                    transcript, latency = result
                    timing_info = None
                
                transcripts[display_name] = transcript
                latencies[display_name] = latency
                # Store timing info for later use
                if timing_info:
                    if 'timing_infos' not in locals():
                        timing_infos = {}
                    timing_infos[display_name] = timing_info
            except Exception as e:
                print(f"Error with {provider_key}: {e}")
                import traceback
                traceback.print_exc()
                transcripts[display_name] = f"ERROR: {str(e)}"
                latencies[display_name] = 0.0
        
        # Judge transcripts if we have enough AND it's a multi-provider run
        # If it's a single provider run (parallel mode from frontend), we skip judging here
        # and let the frontend call /api/asr/judge later
        valid_transcripts = {k: v for k, v in transcripts.items() if not v.startswith("ERROR:")}
        judge_result = {}
        winner = None
        
        if len(selected_providers) > 1 and len(valid_transcripts) >= 2:
            try:
                judge = LLMJudge()
                judge_result = judge.judge_transcripts(valid_transcripts)
                winner = judge_result.get('winner', '')
            except Exception as e:
                print(f"Judging failed: {e}")
        
        # Format results
        for display_name in transcripts.keys():
            provider_name = display_name.split('_')[0]
            model_name = display_name.split('_')[1] if '_' in display_name else 'default'
            
            wer = judge_result.get('wers', {}).get(display_name, 'N/A')
            
            # Get timing info if available
            timing = locals().get('timing_infos', {}).get(display_name, {})
            
            results.append({
                'provider': provider_name,
                'model': model_name,
                'transcript': transcripts[display_name],
                'wer': wer,
                'latency': latencies.get(display_name, 0.0),
                'timing': timing
            })
            
        # Cleanup
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'results': results,
            'consensus': judge_result.get('consensus', 'N/A'),
            'winner': winner
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in ASR endpoint: {error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500

@app.route('/api/asr/judge', methods=['POST'])
def judge_results():
    try:
        data = request.json
        transcripts = data.get('transcripts', {})
        
        if not transcripts:
            return jsonify({'error': 'No transcripts provided'}), 400
            
        valid_transcripts = {k: v for k, v in transcripts.items() if not v.startswith("ERROR:")}
        
        if len(valid_transcripts) < 2:
            return jsonify({
                'consensus': 'N/A',
                'winner': None,
                'wers': {}
            })
            
        from stt_benchmark.judge.llm_judge import LLMJudge
        judge = LLMJudge()
        judge_result = judge.judge_transcripts(valid_transcripts)
        
        return jsonify(judge_result)
        
    except Exception as e:
        print(f"Judging endpoint failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-ai/run', methods=['POST'])
def voice_ai_run():
    """
    Voice AI Stack Endpoint
    Accepts audio file + STT/LLM/TTS config, runs pipeline, returns results
    """
    try:
        # Check file
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get configuration
        stt_provider = request.form.get('stt_provider', 'openai-whisper')
        llm_model = request.form.get('llm_model', 'gpt-3.5-turbo')
        tts_provider = request.form.get('tts_provider', 'elevenlabs')
        
        # Import pipeline (simplified version for demo)
        # In production, you'd wire this to the actual pipelines.py
        
        # For now, return a mock response structure
        # In a real implementation, you would:
        # from pipelines import VoicePipeline
        # pipeline = VoicePipeline(openai_key, elevenlabs_key)
        # result = pipeline.run_batch_turn(audio_file=filepath)
        
        response = {
            'transcript': 'Mock STT transcript from audio file',
            'llm_response': 'Mock LLM response based on transcript',
            'audio_url': None,  # In production, this would be a URL to the generated audio
            'metrics': {
                'stt_latency_ms': 1500,
                'llm_latency_ms': 2000,
                'tts_latency_ms': 1000,
                'e2e_latency_ms': 4500
            }
        }
        
        # Cleanup
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Experiments API is running'})

if __name__ == '__main__':
    print("Starting Experiments Lab API Server")
    print("Server will run on http://localhost:5000")
    print("Available endpoints:")
    print("  - POST /api/asr/benchmark")
    print("  - POST /api/voice-ai/run")
    print("  - GET  /api/health")
    app.run(debug=True, port=5000)
