import os
from groq import Groq
from typing import Generator

def optimize_resume(resume_text: str, job_desc: str, missing_keywords: list, model: str = "llama3-8b-8192") -> Generator[str, None, None]:
    """
    Use Groq to rewrite the resume to naturally include missing keywords from the job description.
    """
    if not resume_text.strip() or not job_desc.strip():
        return ""
        
    if missing_keywords:
        keywords_str = ", ".join(missing_keywords)
        keyword_instruction = f"The resume is missing these crucial ATS keywords: {keywords_str}.\nYour task is to seamlessly integrate these keywords into the experience, summary, or skills sections naturally without keyword-stuffing."
    else:
        keyword_instruction = "The resume already matches the key qualifications. Your task is to perform an elite-level polish."

    prompt = f"""
    You are an elite Executive Resume Writer and ATS Optimization Expert. 
    I will provide you with a resume draft and a target job description. 
    
    {keyword_instruction}
    
    To ensure this resume outperforms top competitors on the market, strictly follow these elite standards:
    1. Use the STAR method (Situation, Task, Action, Result) for bullet points.
    2. Start every bullet point with a high-impact Action Verb (e.g., Spearheaded, Engineered, Orchestrated).
    3. Quantify achievements with concrete metrics, percentages, and dollar amounts wherever logically possible based on the provided context.
    4. Eliminate weak language, passive voice, and generic filler phrases.
    5. Ensure the formatting remains clean, professional, and strictly ATS-parseable.
    
    CRITICAL INSTRUCTION: Return ONLY the optimized resume text. Do NOT include any conversational filler. Just output the raw text.

    --- JOB DESCRIPTION ---
    {job_desc}
    
    --- ORIGINAL RESUME ---
    {resume_text}
    """
    
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a professional resume writer.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"\n\nError connecting to Groq: {str(e)}\nPlease check your GROQ_API_KEY."
