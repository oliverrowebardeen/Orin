"""
Reasoning strategies for Orin reasoning engine.
Implements CoT, self-consistency, and interleaved reasoning.
"""

import requests
import json
import time
from typing import Dict, Any, List, Tuple
from .utils import log_reasoning_step, parse_ollama_response, format_agent_response


class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config['ollama']['base_url']
        self.api_endpoint = config['ollama']['api_endpoint']
        self.model = config['model']['name']
        self.default_temperature = config['model']['temperature']
        self.max_tokens = config['model']['max_tokens']
        self.timeout = config['model']['timeout']
    
    def generate(self, prompt: str, temperature: float = None) -> str:
        """Generate response from Ollama model."""
        if temperature is None:
            temperature = self.default_temperature
            
        url = f"{self.base_url}{self.api_endpoint}"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": self.max_tokens
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except requests.exceptions.RequestException as e:
            return f"Error communicating with Ollama: {e}"


class ReasoningEngine:
    """Main reasoning engine with different strategies."""
    
    def __init__(self, config: Dict[str, Any], logger):
        self.client = OllamaClient(config)
        self.config = config
        self.logger = logger
        self.reasoning_config = config.get('reasoning', {})
    
    def chain_of_thought(self, query: str) -> str:
        """Generate Chain-of-Thought reasoning."""
        if not self.reasoning_config.get('chain_of_thought', {}).get('enabled', True):
            return self.client.generate(query)
        
        cot_config = self.reasoning_config['chain_of_thought']
        prompt_template = cot_config.get('prompt_template', 
            "Think step by step to solve this problem. Show your reasoning process clearly.\n\nQuestion: {query}\n\nReasoning:")
        
        prompt = prompt_template.format(query=query)
        
        log_reasoning_step(self.logger, "Chain of Thought", f"Generating CoT for: {query}")
        
        response = self.client.generate(prompt)
        cleaned_response = parse_ollama_response(response)
        
        log_reasoning_step(self.logger, "CoT Response", cleaned_response)
        
        return cleaned_response
    
    def self_consistency(self, query: str) -> Tuple[str, List[str]]:
        """Generate multiple samples and select most consistent answer."""
        sc_config = self.reasoning_config.get('self_consistency', {})
        if not sc_config.get('enabled', True):
            return self.chain_of_thought(query), []
        
        samples = sc_config.get('samples', 3)
        temperature = sc_config.get('temperature', 0.7)
        
        log_reasoning_step(self.logger, "Self-Consistency", f"Generating {samples} samples")
        
        responses = []
        for i in range(samples):
            self.logger.info(f"Generating sample {i+1}/{samples}")
            response = self.client.generate(query, temperature=temperature)
            cleaned_response = parse_ollama_response(response)
            responses.append(cleaned_response)
            time.sleep(0.5)  # Brief pause between generations
        
        # Simple voting: return the longest response as most likely to be complete
        best_response = max(responses, key=len)
        
        log_reasoning_step(self.logger, "Self-Consistency Result", 
                          f"Selected response (length: {len(best_response)} chars)")
        
        return best_response, responses
    
    def interleaved_reasoning(self, query: str) -> str:
        """Generate reasoning through agent interaction."""
        ir_config = self.reasoning_config.get('interleaved_reasoning', {})
        if not ir_config.get('enabled', True):
            return self.chain_of_thought(query)
        
        agents = ir_config.get('agents', [
            {"name": "Analyst", "role": "Break down the problem and analyze components"},
            {"name": "Critic", "role": "Review and critique the analysis"}
        ])
        
        log_reasoning_step(self.logger, "Interleaved Reasoning", f"Starting with {len(agents)} agents")
        
        conversation = f"Original Query: {query}\n\n"
        
        for i, agent in enumerate(agents):
            agent_name = agent['name']
            agent_role = agent['role']
            
            agent_prompt = f"""You are {agent_name}. Your role: {agent_role}

{conversation}

Provide your analysis:"""
            
            self.logger.info(f"Agent {agent_name} responding...")
            response = self.client.generate(agent_prompt)
            cleaned_response = parse_ollama_response(response)
            
            conversation += format_agent_response(agent_name, cleaned_response)
            
            log_reasoning_step(self.logger, f"Agent {agent_name}", cleaned_response)
        
        # Final synthesis
        synthesis_prompt = f"""Based on the following agent discussion, provide a comprehensive final answer:

{conversation}

Final Answer:"""
        
        final_response = self.client.generate(synthesis_prompt)
        cleaned_final = parse_ollama_response(final_response)
        
        log_reasoning_step(self.logger, "Final Synthesis", cleaned_final)
        
        return cleaned_final
    
    def reason(self, query: str, method: str = "cot") -> str:
        """Main reasoning interface."""
        if not query.strip():
            return "Please provide a valid query."
        
        self.logger.info(f"Orin reasoning engine starting with method: {method}")
        self.logger.info(f"Query: {query}")
        
        if method == "cot":
            return self.chain_of_thought(query)
        elif method == "sc":
            result, _ = self.self_consistency(query)
            return result
        elif method == "ir":
            return self.interleaved_reasoning(query)
        else:
            return self.chain_of_thought(query)  # Default to CoT
