class CharTokenizer:
    def __init__(self, text):
        # Find every unique character in the text
        self.chars = sorted(set(text))
        self.vocab_size = len(self.chars)

        # Two lookup tables:
        # stoi = string to integer (encode)
        # itos = integer to string (decode)
        self.stoi = {ch: i for i, ch in enumerate(self.chars)}
        self.itos = {i: ch for i, ch in enumerate(self.chars)}

    def encode(self, text):
        """Convert a string into a list of integers."""
        return [self.stoi[ch] for ch in text]

    def decode(self, tokens):
        """Convert a list of integers back into a string."""
        return ''.join([self.itos[i] for i in tokens])

    def save(self, path):
        """Save vocabulary to disk so we can reload it later."""
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'chars': self.chars}, f, ensure_ascii=False)
        print(f"Vocabulary saved to {path}")

    @classmethod
    def load(cls, path):
        """Reload a saved tokenizer without needing the original text."""
        import json
        obj = cls.__new__(cls)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        obj.chars = data['chars']
        obj.vocab_size = len(obj.chars)
        obj.stoi = {ch: i for i, ch in enumerate(obj.chars)}
        obj.itos = {i: ch for i, ch in enumerate(obj.chars)}
        return obj