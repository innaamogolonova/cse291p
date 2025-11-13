#!/usr/bin/env python3
"""
Clang Static Analyzer wrapper for detecting memory safety issues.
"""

import subprocess
import os
from typing import List, Dict, Optional


class CSAWrapper:
    """Wrapper for running Clang Static Analyzer on C/C++ source code."""

    # Memory-safety focused checkers
    MEMORY_CHECKERS = [
        "core.NullDereference",
        "core.UndefinedBinaryOperatorResult",
        "core.uninitialized.Branch",
        "core.uninitialized.UndefReturn",
        "core.uninitialized.ArraySubscript",
        "core.uninitialized.Assign",
        "cplusplus.NewDelete",
        "cplusplus.NewDeleteLeaks",
        "unix.Malloc",
        "unix.MallocSizeof",
        "unix.MismatchedDeallocator",
        "alpha.security.ArrayBound",
        "alpha.security.ArrayBoundV2",
        "alpha.security.ReturnPtrRange",
        "alpha.unix.cstring.BufferOverlap",
        "alpha.unix.cstring.OutOfBounds",
    ]

    def __init__(self, clang_path: str = "clang"):
        """Initialize CSA wrapper.

        Args:
            clang_path: Path to clang executable
        """
        self.clang_path = clang_path
        self._verify_clang()

    def _verify_clang(self):
        """Verify clang is available and supports static analysis."""
        try:
            result = subprocess.run(
                [self.clang_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"Using: {result.stdout.splitlines()[0]}")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(f"Clang not found or not working: {e}")

    def find_source_files(
        self,
        root_dir: str,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[str]:
        """Find C/C++ source files, excluding fuzzer directories.

        Args:
            root_dir: Root directory to search
            exclude_patterns: Patterns to exclude (default: fuzzer-related)

        Returns:
            List of absolute paths to source files
        """
        if exclude_patterns is None:
            exclude_patterns = [
                "fuzz", "afl", "honggfuzz", "libfuzzer",
                "test", "tests", "example", "examples"
            ]

        source_files = []
        extensions = {".c", ".cpp", ".cc", ".cxx", ".c++"}

        for root, dirs, files in os.walk(root_dir):
            # Skip directories matching exclude patterns
            dirs[:] = [
                d for d in dirs
                if not any(pattern in d.lower() for pattern in exclude_patterns)
            ]

            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    # Additional check: skip if path contains exclude patterns
                    full_path = os.path.join(root, file)
                    if not any(pattern in full_path.lower() for pattern in exclude_patterns):
                        source_files.append(os.path.abspath(full_path))

        return sorted(source_files)

    def analyze_file(
        self,
        source_file: str,
        extra_args: Optional[List[str]] = None
    ) -> Dict:
        """Run CSA on a single file.

        Args:
            source_file: Path to source file
            extra_args: Additional compiler arguments (e.g., include paths)

        Returns:
            Dictionary with analysis results
        """
        if extra_args is None:
            extra_args = []

        # Build checker arguments
        checker_args = []
        for checker in self.MEMORY_CHECKERS:
            checker_args.extend(["-Xclang", f"-analyzer-checker={checker}"])

        # Base command
        cmd = [
            self.clang_path,
            "--analyze",
            "-Xclang", "-analyzer-output=text",
        ]
        cmd.extend(checker_args)
        cmd.extend(extra_args)
        cmd.append(source_file)

        result = {
            "file": source_file,
            "success": False,
            "warnings": [],
            "errors": [],
            "stdout": "",
            "stderr": ""
        }

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout per file
            )

            result["stdout"] = proc.stdout
            result["stderr"] = proc.stderr
            result["success"] = proc.returncode == 0

            # Parse warnings from stderr (clang analyzer outputs to stderr)
            if proc.stderr:
                result["warnings"] = self._parse_text_output(proc.stderr)

        except subprocess.TimeoutExpired:
            result["errors"].append("Analysis timeout (60s)")
        except Exception as e:
            result["errors"].append(f"Analysis failed: {str(e)}")

        return result

    def _parse_text_output(self, output: str) -> List[Dict]:
        """Parse text output from clang analyzer.

        Args:
            output: stderr output from clang

        Returns:
            List of warning dictionaries
        """
        warnings = []
        current_warning = None

        for line in output.splitlines():
            # Match warning/error lines: "file.c:123:45: warning: message"
            if ": warning:" in line or ": error:" in line:
                if current_warning:
                    warnings.append(current_warning)

                parts = line.split(":", 4)
                if len(parts) >= 5:
                    current_warning = {
                        "file": parts[0].strip(),
                        "line": parts[1].strip(),
                        "column": parts[2].strip(),
                        "severity": parts[3].strip(),
                        "message": parts[4].strip(),
                        "context": []
                    }
            elif current_warning and line.strip():
                # Additional context lines
                current_warning["context"].append(line)

        if current_warning:
            warnings.append(current_warning)

        return warnings

    def analyze_directory(
        self,
        root_dir: str,
        max_files: Optional[int] = None,
        extra_args: Optional[List[str]] = None
    ) -> Dict:
        """Run CSA on all source files in a directory.

        Args:
            root_dir: Root directory containing source code
            max_files: Maximum number of files to analyze (for testing)
            extra_args: Additional compiler arguments

        Returns:
            Dictionary with aggregated results
        """
        print(f"\n=== CSA Analysis of {root_dir} ===\n")

        source_files = self.find_source_files(root_dir)

        if not source_files:
            return {
                "error": "No source files found",
                "files_analyzed": 0,
                "results": []
            }

        if max_files:
            source_files = source_files[:max_files]

        print(f"Found {len(source_files)} source files to analyze")

        results = {
            "files_analyzed": 0,
            "files_with_warnings": 0,
            "total_warnings": 0,
            "results": []
        }

        for i, source_file in enumerate(source_files, 1):
            print(f"[{i}/{len(source_files)}] Analyzing {os.path.basename(source_file)}...", end=" ")

            file_result = self.analyze_file(source_file, extra_args=extra_args)
            results["results"].append(file_result)
            results["files_analyzed"] += 1

            if file_result["warnings"]:
                results["files_with_warnings"] += 1
                results["total_warnings"] += len(file_result["warnings"])
                print(f"WARNING: {len(file_result['warnings'])} warnings")
            else:
                print("OK")

        return results

    def summarize_results(self, results: Dict) -> str:
        """Create a human-readable summary of analysis results.

        Args:
            results: Results from analyze_directory

        Returns:
            Formatted summary string
        """
        if "error" in results:
            return f"Error: {results['error']}"

        summary = [
            f"\n{'='*60}",
            "CSA Analysis Summary",
            f"{'='*60}",
            f"Files analyzed: {results['files_analyzed']}",
            f"Files with warnings: {results['files_with_warnings']}",
            f"Total warnings: {results['total_warnings']}",
            f"{'='*60}\n"
        ]

        if results['total_warnings'] > 0:
            summary.append("\nWarnings by file:")
            summary.append("-" * 60)

            for file_result in results['results']:
                if file_result['warnings']:
                    rel_path = os.path.basename(file_result['file'])
                    summary.append(f"\n{rel_path}: {len(file_result['warnings'])} warnings")

                    for warning in file_result['warnings']:
                        summary.append(
                            f"  Line {warning['line']}: {warning['message']}"
                        )

        return "\n".join(summary)


if __name__ == "__main__":
    # Simple test
    import sys

    if len(sys.argv) < 2:
        print("Usage: python csa_wrapper.py <directory>")
        sys.exit(1)

    wrapper = CSAWrapper()
    results = wrapper.analyze_directory(sys.argv[1], max_files=10)
    print(wrapper.summarize_results(results))
