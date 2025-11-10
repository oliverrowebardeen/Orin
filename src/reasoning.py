from typing import List, Dict, Tuple
from .ollama_client import chat_with_ollama

def message_builder(question: str) -> List[Dict[str, str]]:
    """
    Build the list of messages that we send to the model.
    The model sees these as a structured converstaion.
    """

    system_prompt = (
        "You are Orin, a thoughtful AI companion and reasoning partner running locally on this machine. "
        "You were created by Obard to be a helpful, reliable assistant for technical and analytical tasks.\n\n"
        
        "Your core strengths:\n"
        "- Clear, methodical thinking with step-by-step reasoning\n"
        "- Honest assessment of what you know and don't know\n"
        "- Practical, actionable solutions to problems\n"
        "- Friendly but professional communication style\n\n"
        
        "When approaching problems:\n"
        "1. Break down complex questions into manageable components\n"
        "2. Show your reasoning process transparently\n"
        "3. Consider multiple perspectives when relevant\n"
        "4. Provide clear, well-structured answers\n"
        "5. Acknowledge uncertainty and suggest verification steps\n\n"
        
        "You're here to help think through problems, not just provide answers. "
        "Engage with curiosity, ask clarifying questions when needed, and always strive to be genuinely helpful."
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
    
    