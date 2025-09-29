#!/usr/bin/env python3
"""
Simple Pokemon Battle Log Preprocessor
Creates LLM training samples from Pokemon Showdown logs
"""

import os
import json
import pandas as pd
import tyro
import random

from dataclasses import dataclass
from tqdm import tqdm
from typing import List, Dict, Optional
from rich.console import Console


@dataclass
class Args:
    """Simple preprocessing arguments"""
    dataset: str = "dataset_gen9ou_1"
    """Input CSV file with battle logs"""
    output_dir: str = "dataset/processed"
    """Output directory for processed data"""
    test_split: float = 0.2
    """Fraction of data to use for testing (default: 0.2 = 20%)"""
    val_split: float = 0.2
    """Fraction of data to use for validation (default: 0.2 = 20%)"""
    random_state: int = 42
    """Random state for reproducible splits"""


def extract_simple_battle_context(log_text: str) -> Dict:
    """Extract basic battle information from log"""
    lines = log_text.split('\n')

    context = {
        "teams": {"p1": [], "p2": []},
        "active": {"p1": None, "p2": None},
        "turn": 0,
        "recent_events": []
    }

    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            continue

        # Extract team composition
        if line.startswith("|poke|"):
            parts = line.split('|')
            if len(parts) >= 4:
                side = parts[2][:2]  # p1 or p2
                pokemon = parts[3].split(',')[0].strip()
                if pokemon not in context["teams"][side]:
                    context["teams"][side].append(pokemon)

        # Track current turn
        elif line.startswith("|turn|"):
            parts = line.split('|')
            if len(parts) >= 3 and parts[2].isdigit():
                context["turn"] = int(parts[2])

        # Track active Pokemon
        elif "|switch|" in line and ("p1a:" in line or "p2a:" in line):
            parts = line.split('|')
            if len(parts) >= 4:
                if "p1a:" in line:
                    pokemon = parts[3].split(',')[0].strip()
                    context["active"]["p1"] = pokemon
                elif "p2a:" in line:
                    pokemon = parts[3].split(',')[0].strip()
                    context["active"]["p2"] = pokemon

        # Track recent battle events
        elif any(key in line for key in ["|-damage|", "|move|", "|-weather|"]):
            context["recent_events"].append(line)
            if len(context["recent_events"]) > 5:
                context["recent_events"].pop(0)

    return context


def find_player_actions(log_text: str) -> List[Dict]:
    """Find player 1 actions from the log"""
    actions = []
    lines = log_text.split('\n')
    current_turn = 0

    for line in lines:
        line = line.strip()

        # Track turn
        if line.startswith('|turn|'):
            parts = line.split('|')
            if len(parts) >= 3 and parts[2].isdigit():
                current_turn = int(parts[2])

        # Player 1 moves
        elif 'move|p1a:' in line:
            parts = line.split('|')
            if len(parts) >= 4:
                move_name = parts[3]
                actions.append({
                    "turn": current_turn,
                    "action": f"use {move_name}",
                    "type": "move"
                })

        # Player 1 switches (skip auto-switches)
        elif 'switch|p1a:' in line and '[from]' not in line:
            parts = line.split('|')
            if len(parts) >= 4:
                pokemon = parts[3].split(',')[0].strip()
                actions.append({
                    "turn": current_turn,
                    "action": f"switch to {pokemon}",
                    "type": "switch"
                })

    return actions


def create_training_sample(log_text: str, action: Dict) -> Dict:
    """Create a training sample with input (state) and output (action)"""
    # Get battle context up to this turn
    context = extract_simple_battle_context(log_text)

    # Build the input (battle state) text
    input_lines = [f"Pokemon Battle Turn {action['turn']}", ""]

    # Add teams
    if context["teams"]["p1"]:
        input_lines.append(f"Your team: {', '.join(context['teams']['p1'][:6])}")
    if context["teams"]["p2"]:
        input_lines.append(f"Opponent team: {', '.join(context['teams']['p2'][:6])}")

    # Add active Pokemon
    if context["active"]["p1"]:
        input_lines.append(f"Your active: {context['active']['p1']}")
    if context["active"]["p2"]:
        input_lines.append(f"Enemy active: {context['active']['p2']}")

    # Add recent events
    for event in context["recent_events"]:
        if "|-damage|" in event:
            parts = event.split('|')
            if len(parts) >= 4:
                pokemon = parts[2].replace("p1a:", "").replace("p2a:", "").strip()
                hp = parts[3]
                input_lines.append(f"{pokemon} HP: {hp}")
        elif "|move|" in event:
            parts = event.split('|')
            if len(parts) >= 4:
                pokemon = parts[2].replace("p1a:", "").replace("p2a:", "").strip()
                move = parts[3]
                input_lines.append(f"{pokemon} used {move}")
        elif "|-weather|" in event:
            parts = event.split('|')
            if len(parts) >= 3:
                weather = parts[2]
                input_lines.append(f"Weather: {weather}")

    input_lines.append("")
    input_lines.append("What is the best action to take?")

    # Create input (battle state) and output (best action)
    input_text = "\n".join(input_lines)
    output_text = action['action']

    return {
        "input": input_text,
        "output": output_text
    }


def split_samples(samples: List[Dict], test_split: float, val_split: float, random_state: int = 42) -> tuple:
    """Split samples into train, validation, and test sets"""
    random.seed(random_state)

    # Shuffle samples
    shuffled_samples = samples.copy()
    random.shuffle(shuffled_samples)

    # Calculate split indices
    total_samples = len(shuffled_samples)
    test_size = int(total_samples * test_split)
    val_size = int(total_samples * val_split)

    # Split samples: test -> validation -> train
    test_samples = shuffled_samples[:test_size]
    val_samples = shuffled_samples[test_size:test_size + val_size]
    train_samples = shuffled_samples[test_size + val_size:]

    return train_samples, val_samples, test_samples


def main():
    args = tyro.cli(Args)
    console = Console()

    input_file = f"dataset/raw/{args.dataset}.csv"

    # Create output directories
    train_dir = f"{args.output_dir}/train"
    val_dir = f"{args.output_dir}/val"
    test_dir = f"{args.output_dir}/test"

    if not os.path.exists(input_file):
        console.print(f"❌ Input file not found: {input_file}", style="red")
        return

    # Load CSV data
    df = pd.read_csv(input_file, sep=';')
    all_samples = []

    # Process each battle
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing battles"):

        log_text = str(row.get('log', ''))
        if not log_text or log_text.strip() == 'nan':
            continue

        # Extract actions
        actions = find_player_actions(log_text)

        # Create training samples
        for action in actions[:5]:  # Limit to 5 actions per battle
            sample = create_training_sample(log_text, action)
            all_samples.append(sample)

    if not all_samples:
        console.print("❌ No samples created!", style="red")
        return

    # Split into train, validation, and test sets
    train_samples, val_samples, test_samples = split_samples(
        all_samples,
        args.test_split,
        args.val_split,
        args.random_state
    )

    # Create output directories
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    # Save train samples
    train_file = f"{train_dir}/{args.dataset}.jsonl"
    with open(train_file, 'w', encoding='utf-8') as f:
        for sample in train_samples:
            json.dump(sample, f, ensure_ascii=False)
            f.write('\n')

    # Save validation samples
    val_file = f"{val_dir}/{args.dataset}.jsonl"
    with open(val_file, 'w', encoding='utf-8') as f:
        for sample in val_samples:
            json.dump(sample, f, ensure_ascii=False)
            f.write('\n')

    # Save test samples
    test_file = f"{test_dir}/{args.dataset}.jsonl"
    with open(test_file, 'w', encoding='utf-8') as f:
        for sample in test_samples:
            json.dump(sample, f, ensure_ascii=False)
            f.write('\n')

    console.print(f"[green]* Train samples[/green]: {len(train_samples):6d} -> {train_file}")
    console.print(f"[yellow]* Val   samples[/yellow]: {len(val_samples):6d} -> {val_file}")
    console.print(f"[blue]* Test  samples[/blue]: {len(test_samples):6d} -> {test_file}")


if __name__ == "__main__":
    main()