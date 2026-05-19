import subprocess
import json


class ClaudeCliProvider:
    def __init__(self, cli_path: str = "claude", model: str = "claude-sonnet-4-6"):
        self.cli_path = cli_path
        self.model = model

    def call(self, system_prompt: str, user_message: str) -> str:
        full_prompt = f"{system_prompt}\n\n{user_message}"
        result = subprocess.run(
            [self.cli_path, "-p", full_prompt, "--model", self.model],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr}")
        output = result.stdout.strip()
        try:
            parsed = json.loads(output)
            return parsed.get("result", output)
        except json.JSONDecodeError:
            return output
