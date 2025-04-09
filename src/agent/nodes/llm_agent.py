from typing import Any

from langgraph.store.base import BaseStore
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langchain_core.callbacks import BaseCallbackHandler

from agent.utils import count_tokens, split_model_and_provider
from agent.tools.memory import upsert_memory
from agent.tools.browser import web_quick_search
from agent.state import State
from agent.configuration import Configuration


class PromptDebugHandler(BaseCallbackHandler):
    """
    For debug only: print the full prompt sent to the LLM.
    """
    def on_llm_start(self, serialized: dict, prompts: list[str], **kwargs: Any) -> None:
        print("\n================== FULL PROMPT SENT TO LLM ==================\n")
        for i, prompt in enumerate(prompts):
            print(f"--- Prompt {i+1} ---\n{prompt}\n")
        print("=============================================================\n")



async def call_model(state: State, config: RunnableConfig,*,store:BaseStore) -> dict:
    """
    Main graph node: calls the LLM with the current state. It manages the context window and the memory.
    Context window is divided into three sections following MEMGPT approach: system messages, working
    context (memories) and FIFO queue of messages. Dimensions are checked by counting tokens. 

    Based on the context, the LLM may decide to call tools or not.
    Description of tools is provided when they are bounded to the LLM itself in json format.
    """

    configurable = Configuration.from_runnable_config(config)
    MAX_FIFO_TOKENS = configurable.max_fifo_tokens
    MAX_WORKING_CONTEXT_TOKENS = configurable.max_working_context_tokens

    assert store is not None, "Store not injected!"

    # FIFO messages (limited by token budget)
    fifo_token_counter = 0
    fifo_messages_to_be_included = 0
    for m in state.messages:
        fifo_token_counter += count_tokens(m)
        if fifo_token_counter < MAX_FIFO_TOKENS:
            fifo_messages_to_be_included += 1
        else:
            break

    fifo_messages = state.messages[-fifo_messages_to_be_included:]

    # Semantic memory (working context)
    recent_messages = state.messages[-3:]
    search_query = " ".join([m.content for m in recent_messages if hasattr(m, "content")])
    results = await store.asearch("memories", query=search_query, limit=10)

    working_context_token_counter = 0
    working_context = []
    for mem in results:
        content = mem.value.get("content", "")
        context = mem.value.get("context", "")
        mem_str = f"{content} ({context})"
        tok = count_tokens(mem_str)
        if working_context_token_counter + tok < MAX_WORKING_CONTEXT_TOKENS:
            working_context.append(f"{mem.key.upper()}: {mem_str}, score={mem.score:.2f}")
            working_context_token_counter += tok
        else:
            break
    newline='\n'
    if working_context:
        memories_str = f"""
        You are provided with contextual memories retrieved from past interactions.
        Use them if they are relevant.

        <memories>
        {newline.join(working_context)}
        </memories>
        """
    else:
        memories_str = ""
    
    # FIFO as string->messages are counted to give a context of the flow to the LLM 
    queue_lines = [f"Message number {i+1}: {m.content}" for i, m in enumerate(fifo_messages)]
    queue_str = "\n".join(queue_lines)

    # Final prompt
    system_prompt = configurable.system_prompt.format(
        question=state.question,
        memories=memories_str,
        queue=queue_str
    )

    llm = init_chat_model(**split_model_and_provider(configurable.model))
    debug_config = RunnableConfig(callbacks=[PromptDebugHandler()])
    llm_with_tools = llm.bind_tools([upsert_memory, web_quick_search])

    messages = [{"role": "system", "content": system_prompt}]
    msg = await llm_with_tools.ainvoke(messages, config=debug_config)

    return {"messages": [msg],
            "steps": state.steps - 1}