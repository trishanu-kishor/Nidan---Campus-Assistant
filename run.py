"""
Campus Assistant - Application Launcher & CLI Utility
File: run.py

Usage:
  python run.py                 # Launch the Streamlit Web Application
  python run.py --eval          # Run benchmark evaluation suite
  python run.py --query "..."   # Query the campus orchestrator via CLI
  python run.py --port 8501     # Custom Streamlit server port
"""

import sys
import os
import socket
import argparse
import subprocess
from pathlib import Path

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def find_available_port(start_port: int = 8501, max_attempts: int = 20) -> int:
    """Finds an available TCP port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start_port


def launch_streamlit(port: int = 8501, headless: bool = False):
    """Launches the Streamlit web application on an available port."""
    app_path = PROJECT_ROOT / "app.py"
    active_port = find_available_port(port)

    print("=" * 70)
    print("🎓 NIDAN - CAMPUS ASSISTANT (ONE FRONT DOOR)")
    print(f"🌐 Launching Streamlit Web Application on: http://localhost:{active_port}")
    print("=" * 70)

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        f"--server.port={active_port}",
        f"--server.headless={'true' if headless else 'false'}",
        "--browser.gatherUsageStats=false"
    ]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Nidan Assistant stopped.")


def run_cli_query(query: str):
    """Executes a one-off query through the orchestrator."""
    from router.orchestrator import process_campus_query
    from router.classifier import CampusIntentClassifier
    
    print(f"\n🔍 Query: \"{query}\"\n")
    classifier = CampusIntentClassifier()
    routing = classifier.classify(query)
    print(f"📊 Intent Routing: {routing.detected_domains} | Primary: {routing.primary_domain} | Conf: {routing.confidence:.2f}")
    print("=" * 70)
    response = process_campus_query(query)
    print(response)
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Campus Assistant Launcher")
    parser.add_argument("--eval", action="store_true", help="Run routing benchmark evaluation harness")
    parser.add_argument("--query", "-q", type=str, help="Test a single query from the command line")
    parser.add_argument("--port", "-p", type=int, default=8501, help="Port for Streamlit server (default: 8501)")
    parser.add_argument("--headless", action="store_true", help="Run Streamlit in headless mode")

    args = parser.parse_args()

    if args.eval:
        from eval.evaluate_routing import run_evaluation
        run_evaluation(output_json=True)
    elif args.query:
        run_cli_query(args.query)
    else:
        launch_streamlit(port=args.port, headless=args.headless)


if __name__ == "__main__":
    main()
