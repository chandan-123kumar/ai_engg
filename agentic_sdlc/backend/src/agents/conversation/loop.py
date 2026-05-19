from enum import Enum


class TerminationResult(str, Enum):
    COMPLETE = "complete"
    CONTINUE = "continue"
    ESCALATE = "escalate"


APPROVAL_SIGNALS = ("APPROVED", "LGTM", "looks good", "approved")


class ConversationLoop:
    def __init__(self, config: dict):
        self.config = config

    def check_termination(self, turn_number: int, from_agent: str,
                          output: str, config: dict) -> TerminationResult:
        termination = config.get("termination", {})
        condition = termination.get("condition", "single_turn")
        max_turns = termination.get("max_turns", 1)

        if turn_number >= max_turns and condition != "single_turn":
            return TerminationResult.ESCALATE

        if condition == "single_turn":
            return TerminationResult.COMPLETE

        if condition == "reviewer_approves":
            participants = config.get("participants", [])
            if len(participants) > 1:
                reviewer = participants[-1]
                if from_agent == reviewer:
                    if any(sig.lower() in output.lower() for sig in APPROVAL_SIGNALS):
                        return TerminationResult.COMPLETE
            return TerminationResult.CONTINUE

        if condition == "tool_success":
            if '"success": true' in output or "'success': True" in output:
                return TerminationResult.COMPLETE
            return TerminationResult.CONTINUE

        return TerminationResult.CONTINUE

    def next_participant(self, current: str, config: dict) -> str:
        participants = config.get("participants", [])
        if len(participants) <= 1:
            return participants[0] if participants else current
        idx = participants.index(current) if current in participants else 0
        return participants[(idx + 1) % len(participants)]
