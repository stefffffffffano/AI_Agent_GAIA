import asyncio
import re
import uuid

from datasets import load_dataset
from langgraph.store.memory import InMemoryStore
from langchain.embeddings import init_embeddings
from dotenv import load_dotenv

from agent.graph import build_graph 
from agent.state import State


load_dotenv()

THREAD_ID = str(uuid.uuid4())

def extract_final_answer(text: str) -> str | None:
    match = re.search(r"FINAL ANSWER:\s*(.+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def normalize_answer(answer: str) -> str:
    return answer.strip().lower()


async def run_gaia_example(
    graph,
    question: str,
    expected_answer: str,
    max_steps: int = 5
):
    #Initial state
    state = State(
        question=question,
        messages=[],  
        steps=max_steps
    )
    #Call the graph
    state = await graph.ainvoke(
            state,
            config={"configurable": {"thread_id": THREAD_ID}}
    )
    #Check if the final answer is the correct one (if present), otherwise it's a miss
    last_msg = state["messages"][-1]
    final = extract_final_answer(last_msg.content)
    correct = False
    if final:
        correct = normalize_answer(final) == normalize_answer(expected_answer)
        print(f"\nFINAL ANSWER FOUND: {final}")
        print(f"Ground truth: {expected_answer}")
        print("CORRECT!" if correct else "WRONG!")
    else:
        print("FINAL ANSWER NOT FOUND!")
        print(f"Ground truth: {expected_answer}")
    return correct



def init_store() -> InMemoryStore:
    return InMemoryStore(
        index={
            "embed": init_embeddings("openai:text-embedding-3-small"),
            "dims": 1536,
        }
    )


async def main():
    counter = 0 
    # Load GAIA dataset
    dataset = load_dataset(
        path="GAIA.py", 
        name="2023_level1",
        trust_remote_code=True,
    )

    # Test on the first question
    #Run the first 20 examples (on validation) and count successes
    print(len(dataset["validation"]))
    for i in range(len(dataset["validation"])):
        print(f"Question number {i+1}")
        example = dataset["validation"][i]
        question = example["Question"]
        expected = example["Final answer"]
        print(f"Question: {question}\n")
        print(f"Expected answer: {expected}\n")
        # Initialize store and agent
        store = init_store()
        graph = build_graph(store)

        # Execute the agent
        result = await run_gaia_example(
            graph=graph,
            question=question,
            expected_answer=expected,
            max_steps=10
        )
        if result:
            counter += 1
    print('\n\n\n\n')
    num_examples = len(dataset["validation"])
    print(f"Correct ansers out of {num_examples}: {counter}")
    print(f"Success rate: {counter/num_examples:.2%}")
    
    


if __name__ == "__main__":
    asyncio.run(main())
