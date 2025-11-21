#!/usr/bin/env python3
"""Analyze cocotb profiling results"""

import pstats
import sys
from pathlib import Path


def analyze_profile(profile_file="profile.pstat"):
    """Generate human-readable profile report"""

    if not Path(profile_file).exists():
        print(f"Error: {profile_file} not found")
        print("Run simulation with: COCOTB_ENABLE_PROFILING=1 make sim")
        return

    print("=" * 80)
    print(f"Cocotb Profiling Report: {profile_file}")
    print("=" * 80)
    print()

    # Load profile data
    stats = pstats.Stats(profile_file)

    # Sort by cumulative time
    print("TOP 20 FUNCTIONS BY CUMULATIVE TIME:")
    print("-" * 80)
    stats.sort_stats("cumulative")
    stats.print_stats(20)

    print("\n" + "=" * 80)
    print("TOP 20 FUNCTIONS BY TOTAL TIME:")
    print("-" * 80)
    stats.sort_stats("time")
    stats.print_stats(20)

    print("\n" + "=" * 80)
    print("TOP 20 FUNCTIONS BY NUMBER OF CALLS:")
    print("-" * 80)
    stats.sort_stats("calls")
    stats.print_stats(20)

    print("\n" + "=" * 80)
    print("Profile analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    profile_file = sys.argv[1] if len(sys.argv) > 1 else "profile.pstat"
    analyze_profile(profile_file)
