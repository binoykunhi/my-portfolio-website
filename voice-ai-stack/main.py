import os
import sys
import time
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich.table import Table

from pipelines import VoicePipeline

# Load environment variables
load_dotenv()

console = Console()

def check_health(openai_key: str, elevenlabs_key: str) -> bool:
    """
    Performs a quick health check on services.
    """
    console.print("[bold yellow]Running Startup Health Checks...[/bold yellow]")
    all_passed = True

    # Check Keys
    if not openai_key:
        console.print("[red]❌ OPENAI_API_KEY is missing.[/red]")
        all_passed = False
    else:
        console.print("[green]✅ OPENAI_API_KEY found.[/green]")

    if not elevenlabs_key:
        console.print("[red]❌ ELEVENLABS_API_KEY is missing.[/red]")
        all_passed = False
    else:
        console.print("[green]✅ ELEVENLABS_API_KEY found.[/green]")

    if not all_passed:
        return False

    # Optional: Check connectivity (Mocked for speed/safety in this playground context)
    # In a real app, we'd make a minimal API call.
    # For now, we assume keys are valid if present to avoid burning credits on startup.
    console.print("[green]✅ Connectivity checks skipped (assuming valid keys).[/green]")
    
    return True

def print_metrics_table(turns: list):
    if not turns:
        console.print("[yellow]No metrics for this session yet.[/yellow]")
        return

    table = Table(title="Session Metrics (Master Prompt Aligned)", show_lines=True)
    table.add_column("ID", style="dim", width=8)
    table.add_column("Mode", style="cyan")
    table.add_column("Transcript", style="green")
    table.add_column("Response", style="blue")
    table.add_column("STT (ms)", justify="right")
    table.add_column("LLM (ms)", justify="right")
    table.add_column("TTS (ms)", justify="right")
    table.add_column("Perceived (ms)", justify="right", style="bold yellow")
    table.add_column("E2E (ms)", justify="right")
    table.add_column("WER", justify="right")
    table.add_column("Judge", justify="right")

    for turn in turns:
        metrics = turn.metrics
        mode = turn.pipeline_mode
        turn_id = turn.turn_id[:8]
        
        # Text Snippets
        transcript = turn.user_transcript_text or ""
        response = turn.llm_response_text or ""
        transcript_snip = (transcript[:30] + "...") if len(transcript) > 30 else transcript
        response_snip = (response[:30] + "...") if len(response) > 30 else response
        
        # Metrics Helper
        def fmt(val, suffix="", allow_zero=False):
            if val is None:
                return "-"
            if val == 0 and not allow_zero:
                return "-"
            return f"{val:.0f}{suffix}" # Display ms as integer

        # Select appropriate metrics based on mode
        if mode == "batch":
            stt = fmt(metrics.get('stt_batch_processing_latency_ms'))
        else:
            # For streaming, use Final Latency as the main STT metric for the table?
            # Or Partial? Prompt says "STT latency" in summary. 
            # Let's show Final Latency for consistency with "how long it took".
            stt = fmt(metrics.get('stt_streaming_final_latency_ms'))
            
        llm = fmt(metrics.get('llm_time_to_first_token_ms')) # TTFT is usually the key metric
        tts = fmt(metrics.get('tts_time_to_first_audio_chunk_ms')) # TTFA
        
        perceived = fmt(metrics.get('perceived_latency_ms'))
        e2e = fmt(metrics.get('e2e_latency_ms'))
        
        wer = fmt(turn.wer, allow_zero=True)
        judge = fmt(turn.judge_score, allow_zero=True)

        table.add_row(turn_id, mode, transcript_snip, response_snip, stt, llm, tts, perceived, e2e, wer, judge)
    
    console.print(table)

def main():
    console.print(Panel.fit("[bold blue]Voice AI Playground[/bold blue]\n[dim]Batch vs Streaming Latency Benchmarking[/dim]"))

    openai_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")

    if not check_health(openai_key, elevenlabs_key):
        console.print("[bold red]Health checks failed. Please check .env file.[/bold red]")
        # Allow exit or continue? Prompt says "do not proceed to full tests until resolved"
        # But for development, maybe we want to allow mock mode?
        # We'll exit for now to be strict.
        sys.exit(1)

    pipeline = VoicePipeline(openai_key, elevenlabs_key)
    
    # Auto-calibrate on startup
    pipeline.calibrate()

    while True:
        console.print("\n[bold]Select an option:[/bold]")
        console.print("1) Run batch pipeline once")
        console.print("2) Run streaming pipeline once")
        console.print("3) View recent metrics")
        console.print("4) Quit")

        choice_str = Prompt.ask("Enter choice", choices=["1", "2", "3", "4"])
        choice = int(choice_str)

        if choice == 1:
            try:
                pipeline.run_batch_turn()
            except Exception as e:
                console.print(f"[bold red]Error in Batch Pipeline:[/bold red] {e}")
                pipeline.metrics.log_error("batch", "run", str(e))

        elif choice == 2:
            try:
                pipeline.run_streaming_turn()
            except Exception as e:
                console.print(f"[bold red]Error in Streaming Pipeline:[/bold red] {e}")
                pipeline.metrics.log_error("streaming", "run", str(e))

        elif choice == 3:
            print_metrics_table(pipeline.metrics.session_turns)

        elif choice == 4:
            # Save session to CSV
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"results-{timestamp}.csv"
            pipeline.metrics.save_session_to_csv(filename)
            console.print(f"[green]Session metrics saved to {filename}[/green]")
            console.print("[bold blue]Goodbye![/bold blue]")
            break

if __name__ == "__main__":
    main()
