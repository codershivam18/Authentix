import os
from groq import Groq
from typing import Generator

def generate_citations(text: str, model: str = "llama3-8b-8192") -> Generator[str, None, None]:
    """
    Use Ollama to extract and format messy references into standard IEEE citations.
    """
    if not text.strip():
        yield ""
        return
        
    prompt = f"""
    You are an expert academic librarian. I will provide you with a messy list of references, URLs, or disjointed bibliography entries.
    
    Your task is to properly format ALL of them into strict IEEE citation format.
    
    IEEE Format Guidelines:
    - Include bracketed numbers (e.g., [1], [2]).
    - Format: [1] J. K. Author, "Name of paper," Abbrev. Title of Periodical, vol. x, no. x, pp. xxx-xxx, Abbrev. Month, year.
    - If a URL is provided with no other info, extract the title/author if possible, otherwise format as: [1] Title. URL (accessed Date).
    
    CRITICAL INSTRUCTION: Return ONLY the formatted citations. Do not include any conversational text like "Here are your citations". Just the list.
    
    --- MESSY REFERENCES ---
    {text}
    """
    
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You are a meticulous academic formatting tool.'},
                {'role': 'user', 'content': prompt}
            ],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        yield f"\n\nError connecting to Groq: {str(e)}"
