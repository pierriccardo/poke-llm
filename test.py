import requests
import tyro

from dataclasses import dataclass


@dataclass
class Args:
    url: str = "https://tower-suddenly-rotation-mph.trycloudflare.com"
    key: str = "your key here"
    """Cloudflare random url"""


args = tyro.cli(Args)


# Configuration
URL = f"{args.url}/generate"
API_KEY = args.key


def test_api(prompt, max_tokens=50):
    """Quick test of the API"""
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    data = {
        "prompt": prompt,
        "max_new_tokens": max_tokens
    }
    print("\n" + "=" * 30)
    print(f"[Prompt]: {prompt}")

    try:
        response = requests.post(URL, json=data, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print(f"[Generated]: {result['text']}")
            return result
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None


if __name__ == "__main__":
    print("API Poke-LLM Test")
    test_api("I am playing pokemon showdown and facing lapras, my current pokemon is pikachu I should play the move ")
    test_api("Flowers are ", 50)
    test_api("Pokèmon are ", 50)
