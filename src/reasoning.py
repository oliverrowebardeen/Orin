from typing import List, Dict, Tuple
from .ollama_client import chat_with_ollama

def message_builder(question: str) -> List[Dict[str, str]]:
    """
    Build the list of messages that we send to the model.
    The model sees these as a structured converstaion.
    """

    system_prompt = (
        "You are Orin, a compact local reasoning engine running entirely on a local machine. You were build by Obard."
        "Think clearly, step by step. Show your reasoning before giving the final answer."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]

def one_reasoning_run(
    question: str,
    model: str,
    temperature: float = 0.2,
) -> str:
    """
    One call to the model with chain-of-thought reasoning.
    """
    messages = message_builder(question)
    response = chat_with_ollama(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=False,
    )

    return response

def self_consistency_reasoning(
    question: str,
    model: str,
    temperature: float = 0.7,
    num_runs: int = 5,
) -> Tuple[str, List[str]]:
    """
    self_consistency_reasoning = run the model multiple times, pick the most common answer.
    - n_samples: how many runs to do.
    - higher temperature = more diverse answers, but also more diverse errors.
    returns both:
    - the most common answer
    - the list of all answers
    """

    samples: List[str] = []

    for i in range(n_samples):
        ans = single_reasoning_run(
            question=question,
            model=model,
            temperature=temperature,
        )
        samples.append(ans)
    
    normalized = [s.strip() for s in samples]

    counts = {}
    for ans in normalized:
        counts[ans] = counts.get(ans, 0) + 1
    
    best_answer = max(counts.items(), key=lambda kv: kv[1])[0]

    return best_answer, samples
    
    