import argparse
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from stt_benchmark.providers.openai_stt import OpenAIProvider
from stt_benchmark.providers.deepgram_stt import DeepgramProvider
from stt_benchmark.providers.assemblyai_stt import AssemblyAIProvider
from stt_benchmark.providers.google_stt import GoogleV1Provider, GoogleV2Provider
from stt_benchmark.providers.aws_stt import AWSTranscribeProvider
from stt_benchmark.judge.llm_judge import LLMJudge

console = Console()

def main():
    parser = argparse.ArgumentParser(description="STT Benchmarking Tool")
    parser.add_argument("audio_file", help="Path to the audio file to transcribe")
    parser.add_argument("--model-openai", default="whisper-1", help="OpenAI model")
    parser.add_argument("--model-deepgram", default="nova-2", help="Deepgram model")
    parser.add_argument("--model-assemblyai", default=None, help="AssemblyAI model")
    parser.add_argument("--model-google-v1", default="default", help="Google V1 model")
    parser.add_argument("--model-google-v2", default="chirp", help="Google V2 model")
    parser.add_argument("--model-aws", default=None, help="AWS Transcribe model") # AWS usually auto-selects or has limited options
    args = parser.parse_args()

    import csv
    import glob

    # Determine input files
    if os.path.isdir(args.audio_file):
        # Find all audio files in directory (simple extension check)
        extensions = ['*.mp3', '*.wav', '*.m4a', '*.flac', '*.ogg']
        audio_files = []
        for ext in extensions:
            audio_files.extend(glob.glob(os.path.join(args.audio_file, ext)))
        audio_files.sort()
        if not audio_files:
            console.print(f"[red]No audio files found in {args.audio_file}[/red]")
            return
    elif os.path.exists(args.audio_file):
        audio_files = [args.audio_file]
    else:
        console.print(f"[red]Error: File or directory {args.audio_file} not found.[/red]")
        return

    providers = {
        "OpenAI Whisper": (OpenAIProvider(), args.model_openai),
        "Deepgram": (DeepgramProvider(), args.model_deepgram),
        "AssemblyAI": (AssemblyAIProvider(), args.model_assemblyai),
        "Google V1": (GoogleV1Provider(), args.model_google_v1),
        # Google V2 Chirp 2/3 mapped to 'chirp' (v1) in us-central1 as fallback
        "Google V2 Chirp 2": (GoogleV2Provider(), "chirp2"),
        "Google V2 Chirp 3": (GoogleV2Provider(), "chirp3"),
        "AWS Transcribe": (AWSTranscribeProvider(), args.model_aws),
    }

    all_results = []
    provider_stats = {name: {"total_wer": 0.0, "count": 0} for name in providers.keys()}

    # Prepare CSV file
    csv_filename = "benchmark_results.csv"
    csv_headers = ["Audio File", "Provider", "Model", "Transcription", "WER", "Latency (s)", "Consensus Transcription"]
    
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(csv_headers)

    import concurrent.futures

    for audio_file in audio_files:
        console.print(f"\n[bold green]Processing file: {audio_file}[/bold green]")
        
        transcripts = {}
        latencies = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            future_to_provider = {}
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for name, (provider, model) in providers.items():
                    display_name = f"{name} ({model})" if model else name
                    task_id = progress.add_task(f"Transcribing with {display_name}...", total=None)
                    
                    future = executor.submit(provider.transcribe, audio_file, model=model)
                    future_to_provider[future] = (display_name, task_id, name, model)

                for future in concurrent.futures.as_completed(future_to_provider):
                    display_name, task_id, provider_key, model_key = future_to_provider[future]
                    try:
                        transcript, latency = future.result()
                        transcripts[display_name] = transcript
                        latencies[display_name] = latency
                        console.print(f"[green]✓ {display_name} completed in {latency:.2f}s[/green]")
                    except Exception as e:
                        console.print(f"[red]✗ {display_name} failed: {e}[/red]")
                        transcripts[display_name] = f"ERROR: {str(e)}"
                        latencies[display_name] = 0.0
                    finally:
                        progress.remove_task(task_id)

        valid_transcripts = {k: v for k, v in transcripts.items() if not v.startswith("ERROR:")}
        
        judge_result = {}
        consensus_transcript = "N/A"
        
        if len(valid_transcripts) >= 2:
            console.print("[bold blue]Judging Transcripts...[/bold blue]")
            judge = LLMJudge()
            try:
                judge_result = judge.judge_transcripts(valid_transcripts)
                consensus_transcript = judge_result.get("consensus_transcript", "N/A")
            except Exception as e:
                console.print(f"[red]Judging failed: {e}[/red]")
        else:
            console.print("[yellow]Not enough valid transcripts to judge. Skipping Judge.[/yellow]")

        # Display Individual File Results
        table = Table(title=f"Results for {os.path.basename(audio_file)}")
        table.add_column("Provider", style="cyan")
        table.add_column("Model", style="magenta")
        table.add_column("WER", style="green")
        table.add_column("Latency (s)", style="yellow")
        table.add_column("Winner", style="bold gold1")
        
        winner_name = judge_result.get("winner", "")

        # Append results to CSV and stats
        with open(csv_filename, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            
            for display_name in transcripts.keys():
                # Parse provider and model for display/CSV
                if "(" in display_name and ")" in display_name:
                    prov_name = display_name.split(" (")[0]
                    model_name = display_name.split(" (")[1].rstrip(")")
                else:
                    prov_name = display_name
                    model_name = "Default"
                
                # Get WER
                wer = judge_result.get("wers", {}).get(display_name, "N/A")
                wer_val = 0.0
                if isinstance(wer, float):
                    wer_str = f"{wer:.4f}"
                    wer_val = wer
                    # Update stats (using prov_name as key to group by provider type if desired, 
                    # but user asked for "provider name" which usually implies the specific config. 
                    # Let's use the display_name key from providers dict to match initialization)
                    # Actually, let's map back to the 'providers' keys.
                    # The display_name is constructed as "Name (Model)". 
                    # We need to match it to the keys in 'providers' dict or just use display_name.
                    # Let's use the keys from 'providers' dict.
                    # We can find the key by checking which key starts the display_name
                    
                    # Simpler: accumulate by display_name (Provider + Model)
                    if display_name not in provider_stats:
                        provider_stats[display_name] = {"total_wer": 0.0, "count": 0}
                    
                    provider_stats[display_name]["total_wer"] += wer_val
                    provider_stats[display_name]["count"] += 1
                else:
                    wer_str = "N/A"

                is_winner = display_name == winner_name
                winner_mark = "🏆" if is_winner else ""
                
                latency = latencies.get(display_name, 0.0)
                transcript_text = transcripts.get(display_name, "")

                table.add_row(prov_name, model_name, wer_str, f"{latency:.2f}", winner_mark)
                
                writer.writerow([
                    os.path.basename(audio_file),
                    prov_name,
                    model_name,
                    transcript_text,
                    wer_str,
                    f"{latency:.2f}",
                    consensus_transcript
                ])

        console.print(table)

    # Overall Summary
    console.print("\n[bold]Overall Benchmark Summary[/bold]")
    summary_table = Table(title="Average WER by Provider")
    summary_table.add_column("Provider", style="cyan")
    summary_table.add_column("Average WER", style="green")
    
    best_avg_wer = float('inf')
    overall_winner = "None"

    for name, stats in provider_stats.items():
        if stats["count"] > 0:
            avg_wer = stats["total_wer"] / stats["count"]
            summary_table.add_row(name, f"{avg_wer:.4f}")
            
            if avg_wer < best_avg_wer:
                best_avg_wer = avg_wer
                overall_winner = name
        else:
            summary_table.add_row(name, "N/A")

    console.print(summary_table)
    console.print(Panel(f"[bold green]Overall Winner: {overall_winner}[/bold green] (Lowest Average WER)", border_style="green"))
    console.print(f"\nResults saved to [bold]{csv_filename}[/bold]")

if __name__ == "__main__":
    main()
