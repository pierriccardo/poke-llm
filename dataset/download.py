import os
import re
import tyro
import requests
import pandas as pd

from dataclasses import dataclass
from typing import Optional

# API base URL
API_URL = "https://entertainment-philips-louisiana-interfaces.trycloudflare.com"


@dataclass
class Args:
    format: str = "[Gen 9] OU"
    num_logs: int = 10000
    name: Optional[str] = None

    def __post__init__(self):
        if self.name is None:
            cleaned = re.sub(r'[^A-Za-z0-9]', '', self.format)
            cleaned = cleaned.lower()
            self.name = f"dataset_{cleaned}_{self.num_logs}"


args = tyro.cli(Args)

# get dataset as JSON
response = requests.get(f"{API_URL}/dataset", params={
    "format": args.format,
    "num_logs": args.num_logs,
    "output_format": "json"  # or "csv"
})

if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data['logs'])

    os.makedirs("dataset/raw", exist_ok=True)

    df.to_csv(f"dataset/raw/{args.name}.csv", index=False, sep=';', encoding='utf-8')
    print("========== Download Completed ==========")
    print(df.head(3))
    print(f"Columns: {df.columns.tolist()}")
    print(f"Rating range: {df['rating'].min()} - {df['rating'].max()}")
else:
    print(f"Error: {response.status_code} - {response.text}")