import os
import subprocess
import logging
import sys

# Add parent directory to sys.path so we can import 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_scenarios():
    scenarios = [
        ("data/samples/Problem Statement Scenario1.mp4", "config/scenario1_config.yaml"),
        ("data/samples/Problem Statement Scenario2.mp4", "config/scenario2_config.yaml"),
        ("data/samples/Problem Statement Scenario3.mp4", "config/scenario3_config.yaml")
    ]
    
    print("=" * 50)
    print("AI-BagCounter: Batch Scenario Processor")
    print("=" * 50)
    
    results_summary = []

    for video, config in scenarios:
        if not os.path.exists(video):
            print(f"[SKIP] Video not found: {video}")
            continue
        
        print(f"\n[RUNNING] Processing {video} with {config}...")
        
        cmd = [
            "python", "scripts/main.py",
            "--video", video,
            "--config", config
        ]
        
        try:
            # We use subprocess to keep it clean and isolated
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # Parse output for summary table
                lines = result.stdout.splitlines()
                in_count = 0
                out_count = 0
                for line in lines:
                    if "IN:" in line:
                        in_count = line.split(":")[-1].strip()
                    if "OUT:" in line:
                        out_count = line.split(":")[-1].strip()
                
                results_summary.append({
                    "scenario": video,
                    "in": in_count,
                    "out": out_count,
                    "total": int(in_count) + int(out_count)
                })
                print(f"[SUCCESS] {video} processed.")
            else:
                print(f"[ERROR] Failed to process {video}")
                print(result.stderr)
        except Exception as e:
            print(f"[ERROR] An exception occurred: {e}")

    # Print Summary Table
    if results_summary:
        print("\n" + "=" * 60)
        print(f"{'Scenario':<40} | {'IN':<5} | {'OUT':<5} | {'Total':<5}")
        print("-" * 60)
        for res in results_summary:
            print(f"{res['scenario']:<40} | {res['in']:<5} | {res['out']:<5} | {res['total']:<5}")
        print("=" * 60)
    else:
        print("\n[INFO] No scenarios were processed. Please ensure video files are in the root directory.")

if __name__ == "__main__":
    run_scenarios()
