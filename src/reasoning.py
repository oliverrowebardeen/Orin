from typing import List, Dict, Tuple
from .llamacpp_client import chat_with_llamacpp

def message_builder(question: str) -> List[Dict[str, str]]:
    """
    Build the list of messages that we send to the model.
    The model sees these as a structured conversation.
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

def should_show_thinking(question: str) -> bool:
    """
    Determine if we should show chain-of-thought thinking for this question.
    Returns True for complex questions, False for simple ones.
    """
    question_lower = question.lower().strip()
    
    # Simple greetings and basic questions - no thinking needed
    simple_patterns = [
        r'^(hi|hello|hey|yo)$',
        r'^(how are you|how\'s it going)$',
        r'^(what is your name|who are you)$',
        r'^(thanks|thank you|bye|goodbye)$',
        r'^(yes|no|maybe|ok|okay)$',
        r'^(help|\?)$',
    ]
    
    # Complex questions that benefit from thinking
    complex_patterns = [
        r'what is',
        r'how does',
        r'why does',
        r'explain',
        r'describe',
        r'compare',
        r'analyze',
        r'evaluate',
        r'reasoning',
        r'interleaved',
        r'machine learning',
        r'neural network',
        r'attention mechanism',
    ]
    
    import re
    
    # Check if it's a simple pattern
    for pattern in simple_patterns:
        if re.match(pattern, question_lower):
            return False
    
    # Check if it contains complex indicators
    for pattern in complex_patterns:
        if re.search(pattern, question_lower):
            return True
    
    # Default: if it's longer than 10 words, show thinking
    return len(question.split()) > 10

def one_reasoning_run(
    question: str,
    temperature: float = 0.2,
    stream: bool = True,
) -> str:
    """
    One call to the model with chain-of-thought reasoning.
    If stream=True, shows thinking in real-time for complex questions.
    """
    # Determine if we should show thinking
    show_thinking = should_show_thinking(question)

    messages = message_builder(question)
    response = chat_with_llamacpp(
        messages=messages,
        temperature=temperature,
        stream=stream,  # Always stream to show output in real-time
        show_thinking=show_thinking,  # Pass this to control thinking display
    )

    return response

def self_consistency_reasoning(
    question: str,
    temperature: float = 0.7,
    num_runs: int = 5,
) -> Tuple[str, List[str]]:
    """
    self_consistency_reasoning = run the model multiple times, pick the most common answer.
    - num_runs: how many runs to do.
    - higher temperature = more diverse answers, but also more diverse errors.
    returns both:
    - the most common answer
    - the list of all answers
    """

    samples: List[str] = []

    for i in range(num_runs):
        ans = one_reasoning_run(
            question=question,
            temperature=temperature,
        )
        samples.append(ans)
    
    normalized = [s.strip() for s in samples]

    counts = {}
    for ans in normalized:
        counts[ans] = counts.get(ans, 0) + 1
    
    best_answer = max(counts.items(), key=lambda kv: kv[1])[0]

    return best_answer, samples
    
    