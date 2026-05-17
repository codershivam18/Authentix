import os
from groq import Groq
from typing import Dict, Generator

def humanize_text(text: str, tone: str = "Professional", model: str = "llama3-8b-8192") -> Generator[str, None, None]:
    """
    Use Ollama to rewrite the text to sound more natural and provide an Academic Humanization Report.
    """
    if not text.strip():
        return {"rewritten_text": "", "report": ""}
        
    ieee_instructions = ""
    if tone == "IEEE Standard":
        ieee_instructions = "- STRICTLY adhere to IEEE format: Maintain a formal, third-person objective tone. Be concise, precise, and highly technical. Avoid colloquialisms and emotive language. Balance active and passive voice appropriately for scientific reporting."

    prompt = f"""
    You are an elite academic editor and stealth copywriter. 
    I will provide you with a draft text that was likely written by AI.
    
    Task 1: Rewrite the text to bypass all AI detectors and sound 100% written by a human expert.
    To achieve market-leading "humanization", you MUST follow these psychological writing rules:
    - Maximize Burstiness: Heavily vary sentence lengths. Mix very short, punchy sentences with longer, complex compound sentences.
    - Maximize Perplexity: Avoid highly predictable word choices. Use a rich, nuanced vocabulary, but do not use overly flowery language.
    - Ban AI Vocabulary: Strictly prohibit words like 'delve', 'moreover', 'testament to', 'landscape', 'robust', 'tapestry', 'crucial', and 'vital'.
    - Imperfect Flow: Introduce slight conversational phrasing or transitions that humans naturally use but AI avoids. Use active voice primarily.
    - Tone Calibration: Make the tone {tone}.
    {ieee_instructions}
    
    Task 2: Provide a brief "Changes Log" report explaining the major stylistic choices you made to remove the AI footprint.
    
    FORMAT YOUR RESPONSE EXACTLY AS FOLLOWS (with the exact delimiters):
    
    === REWRITTEN TEXT ===
    [Insert rewritten text here]
    
    === CHANGES REPORT ===
    [Insert markdown report here]
    
    Original Text:
    {text}
    """
    
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'You are a helpful, expert academic writer.'},
                {'role': 'user', 'content': prompt}
            ],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        yield f"\n\nError connecting to Groq: {str(e)}"
