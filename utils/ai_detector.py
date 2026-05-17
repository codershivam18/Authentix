import os
import re
from typing import Dict, Any
from groq import Groq

# Common phrases often used by AI models (especially ChatGPT)
AI_PHRASES = [
    "in summary", "in conclusion", "it is important to note", 
    "delve into", "testament to", "crucial", "landscape",
    "moreover", "furthermore", "additionally", "a tapestry of",
    "navigating the", "realm of", "multifaceted", "plethora",
    "paradigm shift", "dynamic", "transformative", "leverage"
]

def calculate_burstiness(text: str) -> float:
    """Calculate burstiness (variation in sentence length)."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
    
    if len(sentences) < 2:
        return 0.5
        
    lengths = [len(s.split()) for s in sentences]
    avg_len = sum(lengths) / len(lengths)
    variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
    std_dev = variance ** 0.5
    cv = std_dev / (avg_len + 1e-5)
    return min(1.0, cv / 0.8)

def detect_ai_content(text: str, model: str = "llama3-8b-8192") -> Dict[str, Any]:
    """
    Simulate an AI detection score using heuristics and generate a detailed Academic Report using Ollama.
    """
    if not text.strip() or len(text.split()) < 10:
        return {
            "score": 0,
            "report": "Text is too short to evaluate properly.",
            "suspicious_phrases": []
        }
        
    text_lower = text.lower()
    
    # 1. Check for AI phrases
    found_phrases = []
    for phrase in AI_PHRASES:
        if re.search(r'\b' + re.escape(phrase) + r'\b', text_lower):
            found_phrases.append(phrase)
            
    phrase_score = min(100, len(found_phrases) * 15)
    burstiness = calculate_burstiness(text)
    burstiness_ai_prob = (1.0 - burstiness) * 100
    ai_prob = (phrase_score * 0.6) + (burstiness_ai_prob * 0.4)
    ai_prob = max(0, min(100, ai_prob))
    
    # 2. Generate Academic Report via Ollama
    prompt = f"""
    You are an expert academic reviewer and AI plagiarism detector. 
    Analyze the following text for signs of AI generation (e.g., lack of human nuance, uniform sentence structures, robotic transitions, hallucinatory or overly verbose academic phrasing).
    
    Provide a detailed "Academic Integrity Report" in markdown format, tailored to IEEE academic standards. 
    Include:
    1. A brief executive summary of your findings.
    2. A stylistic analysis (pointing out specific sentences that sound too robotic, use classic AI filler words, or violate IEEE formal tone).
    3. Actionable advice for the author to make it sound like authentic, human-written IEEE research (e.g., using precise technical language, objective tone).
    
    CRITICAL INSTRUCTION: Return ONLY the markdown report. Do not add conversational wrappers.
    
    --- TEXT ---
    {text}
    """
    
    report_md = "Error generating detailed report."
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You are a strict academic reviewer.'},
                {'role': 'user', 'content': prompt}
            ]
        )
        report_md = response.choices[0].message.content.strip()
    except Exception as e:
        report_md = f"Error connecting to Groq: {str(e)}\n\nPlease check your GROQ_API_KEY."
        
    return {
        "score": round(ai_prob),
        "report": report_md,
        "suspicious_phrases": found_phrases
    }
