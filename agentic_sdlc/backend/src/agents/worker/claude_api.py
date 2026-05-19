import anthropic


class ClaudeApiProvider:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.model = model
        self._api_key = api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def call(self, system_prompt: str, user_message: str) -> str:
        message = self._get_client().messages.create(
            model=self.model,
            max_tokens=8096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text
