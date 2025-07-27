import spacy
import re
import json
from info_extractor import all_possible_skills, extract_skills, normalize_text

# Load the spaCy model (reuse from info_extractor)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading en_core_web_sm model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Extended JD-specific keywords and patterns
JD_REQUIREMENT_KEYWORDS = [
    "required", "must have", "essential", "mandatory", "prerequisite",
    "minimum", "necessary", "critical", "key requirements", "qualifications",
    "skills needed", "experience required", "should have", "preferred",
    "desired", "nice to have", "bonus", "plus", "advantage"
]

JD_EXPERIENCE_KEYWORDS = [
    "years of experience", "years experience", "experience in", "expertise in",
    "background in", "proven experience", "hands-on experience", "working experience",
    "professional experience", "industry experience", "relevant experience"
]

JD_EDUCATION_KEYWORDS = [
    "degree", "bachelor", "master", "phd", "doctorate", "diploma", "certificate",
    "education", "qualification", "university", "college", "graduate"
]

def extract_jd_requirements(jd_text):
    """
    Extracts requirements from job description text.
    Returns structured data about required skills, experience, education, etc.
    """
    # Normalize the JD text
    normalized_jd = normalize_text(jd_text)
    doc = nlp(normalized_jd)
    
    # Extract required skills using the same skills list
    required_skills = extract_skills(normalized_jd, skills_list=all_possible_skills)
    
    # Extract experience requirements
    experience_requirements = extract_experience_requirements(normalized_jd)
    
    # Extract education requirements
    education_requirements = extract_education_requirements(normalized_jd)
    
    # Extract role-specific requirements
    role_requirements = extract_role_requirements(normalized_jd)
    
    # Extract company and role information
    company_info = extract_company_info(normalized_jd)
    
    # Extract requirement priority (required vs preferred)
    priority_requirements = categorize_requirements_priority(normalized_jd, required_skills)
    
    return {
        "required_skills": priority_requirements["required"],
        "preferred_skills": priority_requirements["preferred"],
        "experience_requirements": experience_requirements,
        "education_requirements": education_requirements,
        "role_requirements": role_requirements,
        "company_info": company_info,
        "all_extracted_skills": required_skills
    }

def extract_experience_requirements(text):
    """Extract experience-related requirements from JD."""
    experience_reqs = []
    
    # Look for years of experience patterns
    year_patterns = [
        r"(\d+)[\+\-\s]*(?:to|\-)?[\s]*(\d+)?[\s]*years?[\s]*(?:of[\s]*)?experience",
        r"minimum[\s]*(\d+)[\s]*years?",
        r"at least[\s]*(\d+)[\s]*years?",
        r"(\d+)\+[\s]*years?",
        r"(\d+)[\s]*or more years?"
    ]
    
    for pattern in year_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                min_years = match[0] if match[0] else None
                max_years = match[1] if len(match) > 1 and match[1] else None
                experience_reqs.append({
                    "min_years": int(min_years) if min_years else None,
                    "max_years": int(max_years) if max_years else None,
                    "type": "general"
                })
            else:
                experience_reqs.append({
                    "min_years": int(match),
                    "max_years": None,
                    "type": "general"
                })
    
    # Look for specific technology experience
    tech_experience = []
    for skill in all_possible_skills:
        skill_pattern = rf"{re.escape(skill)}[\s]*(?:experience|expertise|background)"
        if re.search(skill_pattern, text, re.IGNORECASE):
            tech_experience.append(skill)
    
    return {
        "years_required": experience_reqs,
        "technology_experience": tech_experience
    }

def extract_education_requirements(text):
    """Extract education-related requirements from JD."""
    education_reqs = []
    
    # Look for degree requirements
    degree_patterns = [
        r"bachelor'?s?[\s]*degree",
        r"master'?s?[\s]*degree", 
        r"phd|doctorate",
        r"diploma",
        r"certificate",
        r"degree[\s]*in[\s]*([a-zA-Z\s]+)",
        r"(bachelor|master|phd)[\s]*in[\s]*([a-zA-Z\s]+)"
    ]
    
    for pattern in degree_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            education_reqs.extend(matches)
    
    # Look for specific fields of study
    fields_of_study = []
    study_fields = [
        "computer science", "software engineering", "information technology",
        "engineering", "mathematics", "statistics", "data science",
        "business", "economics", "finance", "marketing"
    ]
    
    for field in study_fields:
        if re.search(rf"\b{re.escape(field)}\b", text, re.IGNORECASE):
            fields_of_study.append(field)
    
    return {
        "degree_requirements": education_reqs,
        "fields_of_study": fields_of_study
    }

def extract_role_requirements(text):
    """Extract role-specific requirements and responsibilities."""
    # Extract job title/role
    job_titles = []
    title_patterns = [
        r"(?:position|role|job)[\s]*:[\s]*([a-zA-Z\s]+)",
        r"we are looking for[\s]*(?:a|an)?[\s]*([a-zA-Z\s]+)",
        r"hiring[\s]*(?:a|an)?[\s]*([a-zA-Z\s]+)"
    ]
    
    for pattern in title_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        job_titles.extend(matches)
    
    # Extract key responsibilities
    responsibilities = []
    responsibility_indicators = [
        "responsibilities", "duties", "you will", "role involves",
        "key tasks", "main duties", "primary responsibilities"
    ]
    
    for indicator in responsibility_indicators:
        pattern = rf"{re.escape(indicator)}[\s]*:?[\s]*([^.]*)"
        matches = re.findall(pattern, text, re.IGNORECASE)
        responsibilities.extend(matches)
    
    return {
        "job_titles": job_titles,
        "responsibilities": responsibilities
    }

def extract_company_info(text):
    """Extract company and role information."""
    # Extract company name (basic pattern)
    company_patterns = [
        r"(?:company|organization)[\s]*:[\s]*([a-zA-Z\s]+)",
        r"at[\s]*([A-Z][a-zA-Z\s]+)[\s]*,",
        r"join[\s]*([A-Z][a-zA-Z\s]+)"
    ]
    
    company_names = []
    for pattern in company_patterns:
        matches = re.findall(pattern, text)
        company_names.extend(matches)
    
    # Extract location information
    location_patterns = [
        r"location[\s]*:[\s]*([a-zA-Z\s,]+)",
        r"based in[\s]*([a-zA-Z\s,]+)",
        r"([A-Z][a-zA-Z\s]+,[\s]*[A-Z]{2,})"  # City, State/Country
    ]
    
    locations = []
    for pattern in location_patterns:
        matches = re.findall(pattern, text)
        locations.extend(matches)
    
    return {
        "company_names": company_names,
        "locations": locations
    }

def categorize_requirements_priority(text, all_skills):
    """Categorize skills into required vs preferred based on context."""
    required_skills = []
    preferred_skills = []
    
    # Split text into sentences for better context analysis
    sentences = re.split(r'[.!?]\s+', text)
    
    for skill in all_skills:
        skill_contexts = []
        
        # Find sentences containing this skill
        for sentence in sentences:
            if re.search(rf"\b{re.escape(skill)}\b", sentence, re.IGNORECASE):
                skill_contexts.append(sentence.lower())
        
        # Analyze context to determine priority
        is_required = False
        is_preferred = False
        
        for context in skill_contexts:
            # Check for required indicators
            if any(keyword in context for keyword in ["required", "must", "essential", "mandatory", "critical"]):
                is_required = True
            # Check for preferred indicators
            elif any(keyword in context for keyword in ["preferred", "nice to have", "bonus", "plus", "desired"]):
                is_preferred = True
        
        # Default to required if no clear indication
        if is_required or (not is_preferred and not is_required):
            required_skills.append(skill)
        else:
            preferred_skills.append(skill)
    
    return {
        "required": required_skills,
        "preferred": preferred_skills
    }

def parse_job_description(jd_text):
    """
    Main function to parse job description and extract all relevant information.
    """
    if not jd_text or not jd_text.strip():
        return {"error": "Empty job description text provided"}
    
    try:
        extracted_data = extract_jd_requirements(jd_text)
        return {
            "success": True,
            "data": extracted_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error parsing job description: {str(e)}"
        }

# Test function
if __name__ == "__main__":
    # Sample JD for testing
    sample_jd = """
    Software Engineer - Full Stack Development
    
    We are looking for a talented Software Engineer to join our dynamic team.
    
    Required Skills:
    - 3+ years of experience in Python and JavaScript
    - Experience with React, Node.js, and MongoDB
    - Strong knowledge of REST APIs and Git
    - Bachelor's degree in Computer Science or related field
    
    Preferred Skills:
    - Experience with AWS or GCP
    - Knowledge of Docker and Kubernetes
    - Familiarity with Machine Learning
    
    Responsibilities:
    - Develop and maintain web applications
    - Collaborate with cross-functional teams
    - Write clean, maintainable code
    
    Location: San Francisco, CA
    """
    
    print("--- Testing Job Description Parser ---")
    result = parse_job_description(sample_jd)
    print(json.dumps(result, indent=2))
