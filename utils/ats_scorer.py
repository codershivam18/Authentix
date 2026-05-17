from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
import re

# Load the sentence transformer model globally to avoid reloading on every request
_model_cache = None

def get_model():
    global _model_cache
    if _model_cache is None:
        _model_cache = SentenceTransformer('all-MiniLM-L6-v2')
    return _model_cache

# Common soft skills dictionary
SOFT_SKILLS = {
    'communication', 'leadership', 'teamwork', 'problem-solving', 'adaptability', 
    'time management', 'critical thinking', 'collaboration', 'creativity', 'work ethic',
    'interpersonal skills', 'attention to detail', 'flexibility', 'organization', 'conflict resolution',
    'emotional intelligence', 'active listening', 'decision making', 'mentoring', 'networking'
}

# Indian degree patterns
INDIAN_DEGREES = [
    r'\bb\.?tech\b', r'\bb\.?e\b', r'\bm\.?tech\b', r'\bmca\b', r'\bbca\b', 
    r'\bb\.?sc\b', r'\bm\.?sc\b', r'\bpgdm\b', r'\bmba\b', r'\bbba\b'
]

# Common action verbs for bullet points
ACTION_VERBS = [
    'achieved', 'developed', 'managed', 'created', 'improved', 'led', 'designed', 
    'implemented', 'increased', 'reduced', 'optimized', 'spearheaded', 'resolved', 
    'delivered', 'launched', 'analyzed', 'coordinated', 'engineered', 'built'
]

def extract_keywords(text, top_n=30):
    """Extract top keywords using TF-IDF and separate into hard and soft skills."""
    if not text.strip():
        return [], []
    
    clean_text = re.sub(r'[^a-zA-Z\s\+]', '', text.lower()) # Keep '+' for C++ etc
    
    custom_stop_words = list(ENGLISH_STOP_WORDS) + [
        'experience', 'years', 'looking', 'good', 'deep', 'skills', 'work', 
        'team', 'required', 'preferred', 'ability', 'strong', 'understanding', 
        'working', 'knowledge', 'plus', 'must', 'have', 'excellent', 'role',
        'requirements', 'responsibilities', 'qualifications', 'degree'
    ]
    
    try:
        vectorizer = TfidfVectorizer(stop_words=custom_stop_words, max_features=100, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform([clean_text])
        feature_names = vectorizer.get_feature_names_out()
        
        scores = tfidf_matrix.toarray()[0]
        keywords = [(feature_names[i], scores[i]) for i in range(len(feature_names))]
        keywords = sorted(keywords, key=lambda x: x[1], reverse=True)[:top_n]
        
        extracted_kws = [k[0] for k in keywords]
        
        soft_skills = [kw for kw in extracted_kws if any(s in kw for s in SOFT_SKILLS)]
        hard_skills = [kw for kw in extracted_kws if kw not in soft_skills]
        
        return hard_skills, soft_skills
    except Exception:
        return [], []

def score_bullet_points(experience_text):
    """Analyze bullet points in experience section."""
    lines = experience_text.split('\n')
    bullets = [l for l in lines if l.strip().startswith('-') or l.strip().startswith('•') or '*' in l]
    
    if not bullets:
        return {"score": 0, "advice": "Use bullet points in your experience section to make it readable."}
        
    metrics_count = sum(1 for b in bullets if re.search(r'\d+|%|\$', b))
    action_verbs_count = sum(1 for b in bullets if any(av in b.lower() for av in ACTION_VERBS))
    
    score = 0
    advice = []
    
    if metrics_count >= len(bullets) * 0.3:
        score += 50
    else:
        advice.append("Quantify more achievements with numbers, percentages, or dollars.")
        
    if action_verbs_count >= len(bullets) * 0.5:
        score += 50
    else:
        advice.append("Start more bullet points with strong action verbs (e.g., 'Developed', 'Led').")
        
    if not advice:
        advice.append("Great job using action verbs and metrics in your bullet points.")
        score = 100
        
    return {"score": score, "advice": advice[0]}

def analyze_resume(parsed_data, job_desc: str):
    """
    5-Pillar ATS Scoring:
    - Keyword Match (40%)
    - Experience Relevance (25%)
    - Skills Coverage (15%)
    - Format & Readability (10%)
    - Section Structure (10%)
    """
    if not parsed_data or not job_desc:
        return {"overall_score": 0, "error": "Missing data"}
        
    resume_text = parsed_data['text']
    sections = parsed_data['sections']
    warnings = parsed_data['warnings']
    resume_lower = resume_text.lower()
    
    model = get_model()
    recommendations = []
    
    # 1. Keyword Match (40%) - Exact + Semantic
    jd_hard, jd_soft = extract_keywords(job_desc, top_n=30)
    jd_all_kws = jd_hard + jd_soft
    
    matched_exact = []
    matched_semantic = []
    missing_kws = []
    
    if jd_all_kws:
        resume_embeddings = None
        for kw in jd_all_kws:
            # Exact match
            if re.search(r'\b' + re.escape(kw) + r'\b', resume_lower):
                matched_exact.append(kw)
            else:
                # Semantic match check (lazy load embeddings)
                if resume_embeddings is None:
                    # chunk resume into sentences/phrases
                    phrases = [p for p in re.split(r'[.\n]', resume_lower) if len(p.strip()) > 10]
                    if not phrases:
                        phrases = [resume_lower]
                    resume_embeddings = model.encode(phrases, convert_to_tensor=True)
                
                kw_embedding = model.encode(kw, convert_to_tensor=True)
                cosine_scores = util.cos_sim(kw_embedding, resume_embeddings)[0]
                max_score = float(max(cosine_scores)) if len(cosine_scores) > 0 else 0
                
                if max_score > 0.65: # Semantic match threshold
                    matched_semantic.append((kw, max_score))
                else:
                    missing_kws.append(kw)
    
    keyword_score = 0
    if jd_all_kws:
        exact_weight = len(matched_exact)
        sem_weight = len(matched_semantic) * 0.8 # Semantic match worth slightly less
        keyword_score = min(100, ((exact_weight + sem_weight) / len(jd_all_kws)) * 100)
    else:
        keyword_score = 100 # No keywords found in JD
        
    if missing_kws:
        recommendations.append(f"Add exact missing keywords: {', '.join(missing_kws[:5])}")

    # 2. Experience Relevance (25%)
    exp_score = 0
    exp_text = sections.get('experience', '')
    if exp_text:
        emb_exp = model.encode([exp_text], convert_to_tensor=True)
        emb_jd = model.encode([job_desc], convert_to_tensor=True)
        exp_score = float(util.cos_sim(emb_exp, emb_jd)[0][0]) * 100
        if exp_score < 50:
            recommendations.append("Tailor your experience section to sound more like the job description.")
    else:
        recommendations.append("Add a clear 'Experience' or 'Work History' section.")
        
    bullet_analysis = score_bullet_points(exp_text)
    exp_score = (exp_score * 0.7) + (bullet_analysis['score'] * 0.3)
    if "Great job" not in bullet_analysis['advice']:
        recommendations.append(bullet_analysis['advice'])

    # 3. Skills Coverage (15%)
    res_hard, res_soft = extract_keywords(resume_text, top_n=30)
    skills_score = 0
    if res_hard or res_soft:
        # Just having a good mix of skills extracted gets you points
        skills_score = min(100, (len(res_hard) + len(res_soft)) * 3)
    else:
        recommendations.append("Your skills are hard to extract. Create a clear 'Skills' section.")

    # 4. Format & Readability (10%)
    format_score = 100
    if warnings:
        format_score -= 50
        recommendations.extend(warnings)
    
    word_count = len(resume_text.split())
    if word_count < 200:
        format_score -= 20
        recommendations.append("Resume is too short. Aim for at least 300 words.")
    elif word_count > 1000:
        format_score -= 10
        recommendations.append("Resume is getting long. Ensure it's concise.")

    # 5. Section Structure (10%)
    struct_score = 100
    missing_sections = [k for k, v in sections.items() if not v]
    if missing_sections:
        struct_score -= len(missing_sections) * 20
        recommendations.append(f"Missing distinct sections: {', '.join(missing_sections).title()}")
        
    # Check Indian Education
    edu_text = sections.get('education', '').lower()
    has_indian_deg = any(re.search(pat, edu_text) for pat in INDIAN_DEGREES)
    if edu_text and not has_indian_deg and not re.search(r'\bbachelors|masters|phd|b\.a\.|b\.s\.\b', edu_text):
        recommendations.append("Ensure your degree is explicitly stated in the Education section.")

    # Aggregate
    overall_score = (
        (keyword_score * 0.40) +
        (exp_score * 0.25) +
        (skills_score * 0.15) +
        (format_score * 0.10) +
        (struct_score * 0.10)
    )

    return {
        "overall_score": round(max(0, min(100, overall_score))),
        "sub_scores": {
            "Keyword Match": round(max(0, min(100, keyword_score))),
            "Experience Relevance": round(max(0, min(100, exp_score))),
            "Skills Coverage": round(max(0, min(100, skills_score))),
            "Format & Readability": round(max(0, min(100, format_score))),
            "Section Structure": round(max(0, min(100, struct_score)))
        },
        "matched_exact": matched_exact,
        "matched_semantic": [m[0] for m in matched_semantic],
        "missing_keywords": missing_kws,
        "recommendations": recommendations,
        "warnings": warnings
    }
