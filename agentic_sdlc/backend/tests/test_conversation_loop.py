import pytest
from unittest.mock import MagicMock, patch
from src.agents.conversation.loop import ConversationLoop, TerminationResult

def _make_config(condition="single_turn", max_turns=5,
                 participants=None, initiator="coder"):
    return {
        "participants": participants or ["coder"],
        "initiator": initiator,
        "termination": {"condition": condition, "max_turns": max_turns},
    }

def test_single_turn_terminates_immediately():
    loop = ConversationLoop(config=_make_config("single_turn"))
    result = loop.check_termination(
        turn_number=1, from_agent="coder", output="some code", config=_make_config("single_turn")
    )
    assert result == TerminationResult.COMPLETE

def test_max_turns_triggers_escalation():
    config = _make_config("reviewer_approves", max_turns=3)
    loop = ConversationLoop(config=config)
    result = loop.check_termination(
        turn_number=3, from_agent="coder", output="still working", config=config
    )
    assert result == TerminationResult.ESCALATE

def test_reviewer_approves_when_signal_present():
    config = _make_config("reviewer_approves", participants=["coder", "reviewer"],
                          initiator="coder")
    loop = ConversationLoop(config=config)
    result = loop.check_termination(
        turn_number=2, from_agent="reviewer",
        output="APPROVED: the code looks good",
        config=config,
    )
    assert result == TerminationResult.COMPLETE

def test_reviewer_not_yet_approved():
    config = _make_config("reviewer_approves", participants=["coder", "reviewer"],
                          initiator="coder")
    loop = ConversationLoop(config=config)
    result = loop.check_termination(
        turn_number=2, from_agent="reviewer",
        output="Please fix the null check on line 5",
        config=config,
    )
    assert result == TerminationResult.CONTINUE

def test_next_participant_alternates():
    config = _make_config(participants=["coder", "reviewer"], initiator="coder")
    loop = ConversationLoop(config=config)
    assert loop.next_participant(current="coder", config=config) == "reviewer"
    assert loop.next_participant(current="reviewer", config=config) == "coder"

def test_next_participant_single_loops_back():
    config = _make_config(participants=["coder"], initiator="coder")
    loop = ConversationLoop(config=config)
    assert loop.next_participant(current="coder", config=config) == "coder"
