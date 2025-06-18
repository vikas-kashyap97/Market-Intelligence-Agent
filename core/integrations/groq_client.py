import requests
import logging
from typing import Dict, List, Any, Optional
from config.settings import Settings

logger = logging.getLogger(__name__)

class GroqClient:
    """Client for Groq API integration"""
    
    def __init__(self):
        self.api_key = Settings.GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.model = Settings.GROQ_MODEL
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate chat completion"""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            logger.info("Successfully generated chat completion")
            return content
            
        except Exception as e:
            logger.error(f"Failed to generate chat completion: {str(e)}")
            return "I apologize, but I encountered an error processing your request."
    
    def stream_chat_completion(self, messages: List[Dict[str, str]], 
                              temperature: float = 0.7, max_tokens: int = 1000):
        """Generate streaming chat completion"""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                stream=True
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data != '[DONE]':
                            try:
                                import json
                                chunk = json.loads(data)
                                delta = chunk["choices"][0]["delta"]
                                if "content" in delta:
                                    yield delta["content"]
                            except:
                                continue
                                
        except Exception as e:
            logger.error(f"Failed to stream chat completion: {str(e)}")
            yield "I apologize, but I encountered an error processing your request."
    
    def analyze_text(self, text: str, analysis_type: str = "summary") -> str:
        """Analyze text with specific analysis type"""
        prompts = {
            "summary": f"Provide a concise summary of the following text:\n\n{text}",
            "insights": f"Extract key insights and trends from the following text:\n\n{text}",
            "sentiment": f"Analyze the sentiment and tone of the following text:\n\n{text}",
            "keywords": f"Extract the most important keywords and topics from the following text:\n\n{text}"
        }
        
        prompt = prompts.get(analysis_type, prompts["summary"])
        
        messages = [
            {"role": "system", "content": "You are an expert analyst. Provide clear, actionable insights."},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat_completion(messages)
