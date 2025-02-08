# freeseek/optimizer.py
import logging
import re
from collections import deque
from freeseek.config import CONFIG

logger = logging.getLogger(__name__)

class AdaptiveQueryOptimizer:
    """
    Optimizes queries by dynamically selecting models, adjusting prompts,
    handling rate limits, and caching frequent queries.
    """
    
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.priority = self.config.get("optimization_priority", "balanced")
        self.history = deque(maxlen=50)  # Store past queries for analysis
        self.cache = {}  # Cache for repeated queries
        self.rate_limit_remaining = self.config.get("rate_limit", 1000)  # Placeholder
    
    def select_model(self, query):
        """
        Selects the most suitable model based on query complexity and rate limits.
        """
        if self.rate_limit_remaining < 10:
            return "deepseek_light"  # Fallback to a lighter model under rate constraints
        
        if len(query) < 50:
            return "deepseek_light"  # Fast & cheap for short queries
        elif len(query) < 200:
            return "deepseek_v3"  # Default model
        else:
            return "deepseek_pro"  # High-quality for complex queries
    
    def optimize_prompt(self, prompt):
        """
        Adjusts the prompt based on user-defined priority and query classification.
        """
        if self.priority == "speed":
            return prompt[:250]  # Truncate for faster processing
        elif self.priority == "accuracy":
            return prompt + " Provide detailed and accurate results."
        
        return prompt  # Default (balanced)
    
    def analyze_history(self):
        """
        Evaluate past queries for patterns to refine optimization.
        """
        if len(self.history) > 10:
            avg_length = sum(len(q) for q in self.history) / len(self.history)
            logger.info(f"Average query length: {avg_length}")
    
    def classify_query(self, prompt):
        """
        Categorizes queries into types (e.g., factual, creative, coding) for better optimization.
        """
        if re.search(r'code|script|function', prompt, re.IGNORECASE):
            return "coding"
        elif re.search(r'write|story|poem', prompt, re.IGNORECASE):
            return "creative"
        return "general"
    
    def process_request(self, model, data):
        """
        Optimize request before sending it to the API, using caching and rate limit checks.
        """
        prompt = data.get("prompt", "")
        
        # Check cache
        if prompt in self.cache:
            logger.info("Returning cached optimization result.")
            return self.cache[prompt]
        
        self.history.append(prompt)  # Store query in history
        self.analyze_history()
        
        optimized_model = self.select_model(prompt)
        optimized_prompt = self.optimize_prompt(prompt)
        query_type = self.classify_query(prompt)
        
        logger.info(f"Optimized Model: {optimized_model}")
        logger.info(f"Optimized Prompt: {optimized_prompt}")
        logger.info(f"Query Type: {query_type}")
        
        result = (optimized_model, {**data, "prompt": optimized_prompt})
        self.cache[prompt] = result  # Store in cache
        
        return result