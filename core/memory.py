class ConversationMemory:
    """Keep a small, bounded context window for local LLM conversations."""

    def __init__(self, max_turns=6):
        self.history = []
        self.max_turns = max_turns

    def add(self, role, content):
        self.history.append({"role": role, "content": content})
        self.history = self.history[-self.max_turns * 2 :]

    def get(self):
        return self.history
