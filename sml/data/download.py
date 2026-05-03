import requests
import os

url = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
save_path = "data/input.txt"

print("Downloading TinyShakespeare...")
response = requests.get(url)
response.raise_for_status()

with open(save_path, "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"Saved to {save_path}")
print(f"Total characters: {len(response.text):,}")