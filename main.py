#!/usr/bin/env python3
"""
Main entry point for LLM-integrated static analysis.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from analyzers.csa_wrapper import CSAWrapper


def analyze_case(case_id: int, max_files: int = None):
    """Analyze a specific ARVO case.

    Args:
        case_id: Case ID to analyze
        max_files: Maximum number of files to analyze (None for all)
    """
    # Path to buggy source
    case_dir = Path("data") / "cases" / str(case_id)
    buggy_src = case_dir / "buggy_src"

    if not buggy_src.exists():
        print(f"Error: Case {case_id} not found at {buggy_src}")
        print(f"Run: bash scripts/extract_case.sh {case_id}")
        return None

    # Find the actual project directory (not fuzzers)
    project_dirs = []
    for item in buggy_src.iterdir():
        if item.is_dir():
            # Skip fuzzer directories
            if not any(fuzz in item.name.lower() for fuzz in ["fuzz", "afl", "honggfuzz", "libfuzzer"]):
                project_dirs.append(item)

    if not project_dirs:
        print(f"Error: No project directories found in {buggy_src}")
        return None

    # Use the first non-fuzzer directory
    target_dir = project_dirs[0]
    print(f"Analyzing case {case_id}: {target_dir.name}")

    # Run CSA analysis
    wrapper = CSAWrapper()
    results = wrapper.analyze_directory(str(target_dir), max_files=max_files)

    # Print summary
    print(wrapper.summarize_results(results))

    # Save results
    output_dir = Path("data") / "results"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"case_{case_id}_csa.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    return results


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        case_id = int(sys.argv[1])
        max_files = int(sys.argv[2]) if len(sys.argv) > 2 else None
    else:
        # Default to case 289
        case_id = 289
        max_files = 20  # Limit for initial testing

    print(f"{'='*60}")
    print(f"LLM-Integrated Static Analysis")
    print(f"{'='*60}\n")

    results = analyze_case(case_id, max_files=max_files)

    if results and results.get("total_warnings", 0) > 0:
        print("\nStatic analysis found potential issues.")
        print("Next step: LLM integration to analyze and fix bugs")
    else:
        print("\nNo warnings found by static analysis")
        print("Note: The actual bug may require runtime analysis or deeper inspection")


if __name__ == "__main__":
    main()
