from utils.ats_scorer import analyze_resume
from utils.ai_detector import detect_ai_content
from utils.humanizer import humanize_text
from utils.optimizer import optimize_resume

print("--- Testing ATS Scorer ---")
jd = "We are looking for a Senior Software Engineer with deep experience in Python, Machine Learning, and AWS. Must have good communication skills, API development experience, and 3 years of experience."
resume = "I am a Software Developer. I know Python and Machine Learning. I have deployed on AWS. I built REST APIs. Work Experience: I worked as a developer for 3 years, increasing revenue by 20%."
parsed_data = {
    "text": resume,
    "sections": {"experience": "I worked as a developer for 3 years, increasing revenue by 20%."},
    "warnings": []
}
print(analyze_resume(parsed_data, jd))

print("\n--- Testing AI Detector ---")
ai_text = "In conclusion, the multifaceted landscape of modern technology is a testament to human ingenuity. Moreover, we must delve into this paradigm shift."
print(detect_ai_content(ai_text))

print("\n--- Testing Humanizer ---")
print(humanize_text(ai_text, tone="Friendly", model="llama3"))

print("\n--- Testing Optimizer ---")
print(optimize_resume(resume, jd, ["communication skills", "senior software engineer"], model="llama3"))
