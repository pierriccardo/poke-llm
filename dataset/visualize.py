#!/usr/bin/env python3
"""
Simple Pokemon Training Sample Visualizer
Clean and simple visualization for processed JSONL datasets
"""

import os
import json
import tyro
from typing import List, Dict
from dataclasses import dataclass
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich import print as rprint


@dataclass
class Args:
    """Simple Pokemon Training Sample Visualizer"""
    dataset: str = "dataset_gen9ou_1"
    """Name of JSONL dataset file in dataset/processed/ folder"""
    num_samples: int = 1
    """Number of samples to display per split (default: 1)"""


def visualize_sample(sample: Dict, sample_num: int) -> None:
    """Rich visualization of a single training sample with colored JSON"""
    console = Console()

    # Create a pretty JSON representation
    json_str = json.dumps(sample, indent=2, ensure_ascii=False)

    # Create syntax-highlighted JSON
    syntax = Syntax(
        json_str,
        "json",
        theme="monokai",
        line_numbers=True,
        word_wrap=True
    )

    # Create a panel with the sample
    panel = Panel(
        syntax,
        title=f"[bold blue]SAMPLE {sample_num}[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()  # Add spacing between samples


def visualize_dataset(filepath: str, num_samples: int = 5) -> None:
    """Visualize samples from a processed JSONL dataset file"""
    console = Console()

    if not os.path.exists(filepath):
        console.print(f"[red]❌ File not found: {filepath}[/red]")
        return

    console.print(f"[green]📊 Loading samples from: {filepath}[/green]")

    samples = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        sample = json.loads(line)
                        samples.append(sample)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        console.print(f"[red]❌ Error reading file: {e}[/red]")
        return

    if not samples:
        console.print("[red]❌ No valid samples found[/red]")
        return

    console.print()

    # Display the requested number of samples
    for i, sample in enumerate(samples[:num_samples], 1):
        visualize_sample(sample, i)


def visualize_all_splits(dataset_name: str, num_samples: int = 1) -> None:
    """Visualize samples from train, val, and test splits"""
    console = Console()

    # Define the splits to show
    splits = [
        ("train", "🟢 TRAIN"),
        ("val", "🟡 VAL"),
        ("test", "🔵 TEST")
    ]

    for split_name, split_emoji in splits:
        filepath = f"dataset/processed/{split_name}/{dataset_name}.jsonl"

        console.print(f"\n{split_emoji} [bold]{split_name.upper()}[/bold] SPLIT")
        console.print("=" * 60)

        if os.path.exists(filepath):
            visualize_dataset(filepath, num_samples)
        else:
            console.print(f"[red]❌ {split_name} split not found: {filepath}[/red]")


def main():
    args = tyro.cli(Args)

    # Always show samples from all available splits (train, val, test)
    visualize_all_splits(args.dataset, args.num_samples)


if __name__ == "__main__":
    main()
