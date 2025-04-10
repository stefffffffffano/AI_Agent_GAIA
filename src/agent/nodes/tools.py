import asyncio

from langgraph.store.base import BaseStore
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig

from agent.utils import split_model_and_provider
from agent.tools.memory import upsert_memory_func
from agent.tools.browser import web_quick_search_func
from agent.state import State
from agent.configuration import Configuration



async def tools(state: State, config: RunnableConfig, *, store: BaseStore):
    """
    Executes the tools called by the LLM.
    Allows multiple `upsert_memory` calls, but only one `web_quick_search` per step.
    If more than one `web_quick_search` is requested, only the first is executed,
    and an informative message is returned.
    """
    tool_calls = state.messages[-1].tool_calls

    if not tool_calls:
        raise ValueError("No tool calls found.")

    results = []

    # Handle upsert_memory
    upsert_calls = [tc for tc in tool_calls if tc["name"] == "upsert_memory"]
    if upsert_calls:
        saved_memories = await asyncio.gather(
            *[upsert_memory_func(**tc["args"], store=store) for tc in upsert_calls]
        )
        results.extend([
            {
                "role": "tool",
                "content": mem,
                "tool_call_id": tc["id"],
            }
            for tc, mem in zip(upsert_calls, saved_memories)
        ])

    # Handle web_quick_search (only one allowed)
    web_calls = [tc for tc in tool_calls if tc["name"] == "web_quick_search"]
    if web_calls:
        first_web_call = web_calls[0]
        configurable = Configuration.from_runnable_config(config)
        llm = init_chat_model(**split_model_and_provider(configurable.model))
        query_used = first_web_call["args"].get("query", "unknown")
        
        response = await web_quick_search_func(**first_web_call["args"], llm_model=llm)
        response_with_query = (
            f"Search result for query: '{query_used}'\n{response}"
        )
        
        results.append({
            "role": "tool",
            "content": response_with_query,
            "tool_call_id": first_web_call["id"],
        })

        if len(web_calls) > 1:
            skipped_calls = len(web_calls) - 1
            skipped_calls_content = '\n'.join([text["args"].get("query","unknown") for text in web_calls[1:]])
            results.append({
                "role": "tool",
                "content": f"Only one web_quick_search is allowed per step. "
                           f"{skipped_calls} additional call(s) were skipped.\n"
                           f"Skipped call(s): {skipped_calls_content}",
                "tool_call_id": web_calls[1]["id"]  
            })

    return {
        "messages": results,
        "steps": state.steps - 1
    }


__all__ = ["tools"]