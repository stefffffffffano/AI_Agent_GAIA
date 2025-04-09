from langgraph.graph import END

from agent.state import State


def route_message(state: State):
    """Determine the next step based on the presence of tool calls."""
    msg = state.messages[-1]
    if msg.tool_calls and state.steps > 0:
        # If there are tool calls and steps left, continue the conversation
        return "tools"
    # Otherwise, finish; user can send the next message
    return END

__all__ = ["route_message"]