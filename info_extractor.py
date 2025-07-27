import spacy
import re
import os
import json
from text_extractor import extract_text # Assuming text_extractor.py is in the same directory

# Load the pre-trained spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading en_core_web_sm model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Expanded the all_possible_skills list to include skills from your resume
all_possible_skills = [
    "Python", "Java", "SQL", "Machine Learning", "Data Analysis", "Project Management",
    "Communication", "Leadership", "AWS", "Azure", "GCP", "Docker", "Kubernetes",
    "JavaScript", "React", "Angular", "Node.js", "Django", "Flask", "TensorFlow",
    "PyTorch", "Scikit-learn", "Numpy", "Pandas", "Git", "Agile", "Scrum",
    "HTML", "CSS", "C++", "C#", "Ruby", "Go", "Swift", "Kotlin", "PHP", "R",
    "Excel", "PowerPoint", "Word", "Tableau", "Power BI", "Spark", "Hadoop",
    "Linux", "Windows Server", "Networking", "Cybersecurity", "DevOps", "CI/CD",
    "REST API", "Microservices", "Unit Testing", "Integration Testing", "APIs",
    "Problem Solving", "Critical Thinking", "Teamwork", "Adaptability",
    "Database Management", "Object-Oriented Programming", "Functional Programming",
    "Web Development", "Mobile Development", "Cloud Computing", "Big Data",
    "Natural Language Processing", "Computer Vision", "Deep Learning", "Reinforcement Learning",
    "Software Development Life Cycle (SDLC)", "API Design", "Data Structures", "Algorithms",
    "PostgreSQL", "MongoDB", "Tailwind", "API Development", "Parrot OS", "Cursor", "WindSurf", "Langflow",
    "SaaS", "Backend Development", "Frontend Technologies", "Content Management System (CMS)",
    "Data Integration", "JWT authentication", "Role-based access", "Analytics Dashboard"
]

def normalize_text(text):
    """
    Normalizes text by replacing multiple newlines/spaces with single spaces,
    but tries to preserve major structural breaks for sectioning.
    """
    # First, let's preserve important structural elements
    # Replace common bullet points with newlines
    text = re.sub(r'[•·▪▫▬─]\s*', '\n• ', text)
    
    # Replace common newline variations with a single space, but preserve paragraph breaks
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    
    # Replace multiple spaces with a single space but preserve line structure
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Introduce explicit newlines after common section headers to help re-segment
    section_headers = [
        "Summary", "Skills", "Experience", "Work Experience", "Professional Experience",
        "Education", "Academic Background", "Projects", "Awards", "Certifications", 
        "Contact", "About", "Profile", "Objective", "Career Objective"
    ]
    
    for header in section_headers:
        # Matches header, optional colon, then ensures newline
        text = re.sub(r'(?i)\b(' + re.escape(header) + r')\s*:\s*', r'\n\1:\n', text)
        text = re.sub(r'(?i)\b(' + re.escape(header) + r')\s*\n', r'\n\1:\n', text)
    
    # Clean up excessive newlines but preserve paragraph structure
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 newlines for paragraphs
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)  # Trim each line
    
    return text.strip()


def extract_contact_info(text):
    """
    Extracts email, phone number, and URLs (like LinkedIn) using regex.
    """
    email = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    # More robust phone number regex for various formats including Indian numbers
    phone_patterns = [
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",  # US format
        r"(?:\+?\d{1,3}[-.\s]?)?\d{10}",  # 10 digits (Indian format)
        r"(?:\+?\d{1,3}[-.\s]?)?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}",  # XXX-XXX-XXXX
        r"(?:\+?\d{1,2}[-.\s]?)?\d{10}",  # International
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,6}",  # General
        r"\+91[-.\s]?\d{10}",  # Indian format with country code
        r"(?:\+91[-.\s]?)?[6-9]\d{9}",  # Indian mobile numbers (start with 6-9)
        r"(?:\+91[-.\s]?)?[789]\d{9}",  # Indian mobile (7,8,9 start)
        r"\+91\s+\d{4}\s+\d{3}\s+\d{3}",  # Indian format with spaces: +91 8696 017 817
        r"\+\d{2}\s+\d{4}\s+\d{3}\s+\d{3}",  # International with spaces
    ]
    phone = []
    for pattern in phone_patterns:
        found_phones = re.findall(pattern, text)
        phone.extend(found_phones)
    
    # Also look for phone numbers with different separators and special characters
    additional_patterns = [
        r"(?:\+?\d{1,3}[.\-\s/]?)?\d{3,4}[.\-\s/]\d{3,4}[.\-\s/]\d{4,6}",
        r"(?:\+?\d{1,3}[\s]?)?\d{10,11}",  # Simple 10-11 digit numbers
        r"(?:\+91[\s]?)?\d{10}",  # Indian format
        r"\+91[\s\n]*\d{4}[\s\n]*\d{3}[\s\n]*\d{3}",  # Handle newlines too
    ]
    for pattern in additional_patterns:
        additional_phone = re.findall(pattern, text)
        phone.extend(additional_phone)
    
    # Regex for URLs, specifically looking for linkedin.com and other common website patterns
    url_patterns = [
        r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)",
        r"www\.[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)",
        r"linkedin\.com/in/[-a-zA-Z0-9@:%._\+~#=]*",
        r"github\.com/[-a-zA-Z0-9@:%._\+~#=]*"
    ]
    urls = []
    for pattern in url_patterns:
        urls.extend(re.findall(pattern, text))
    
    # Enhanced LinkedIn username extraction
    linkedin_patterns = [
        r"/♀?\w*linkedin[-.\w]*",  # Current pattern
        r"/♀([a-zA-Z0-9\-_]+)",   # Extract username after /♀
        r"linkedin\.com/in/([a-zA-Z0-9\-_]+)",  # Standard LinkedIn URL
        r"@([a-zA-Z0-9\-_]+)",  # Sometimes usernames appear with @
        r"/([a-zA-Z0-9\-_]+)",   # General username pattern
    ]
    
    linkedin_usernames = []
    for pattern in linkedin_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, str) and len(match) > 2:
                # Clean the username
                clean_username = match.replace('♀', '').replace('linkedin', '').strip('-._')
                if clean_username and not any(char in clean_username for char in ['@', '.com', 'gmail']):
                    linkedin_usernames.append(clean_username)
    
    # Look for LinkedIn username patterns specifically
    # Pattern: /♀nednrajat-kumawat or similar
    linkedin_username_match = re.search(r"/♀?([a-zA-Z0-9\-_]+)", text)
    if linkedin_username_match:
        username = linkedin_username_match.group(1)
        if username and len(username) > 2:
            linkedin_usernames.append(username)
    
    # Convert usernames to full LinkedIn URLs
    for username in linkedin_usernames:
        if username and username.lower() not in ['linkedin', 'www', 'com', 'gmail']:
            full_url = f"linkedin.com/in/{username}"
            if full_url not in urls:
                urls.append(full_url)

    filtered_phone = []
    for p in phone:
        # Clean the phone number - remove all non-digits to count length
        digits = re.sub(r'\D', '', p)
        if 7 <= len(digits) <= 15: # Basic check for valid phone number length
            # Clean and format the original phone number
            cleaned_phone = re.sub(r'[\n\r]', ' ', p).strip()  # Remove newlines
            cleaned_phone = re.sub(r'\s+', ' ', cleaned_phone)  # Normalize spaces
            filtered_phone.append(cleaned_phone)
    
    # Additional phone search for patterns like numbers without clear separators
    phone_fallback = re.findall(r'\b\d{10,11}\b', text)  # Look for 10-11 digit numbers
    
    # Also look for phone numbers that might be mixed with other characters
    phone_mixed = re.findall(r'(?:\+91[\s⋄]?)?\d{10}', text)  # Look for ⋄ separator
    phone.extend(phone_mixed)
    
    # Look specifically for numbers that start with common Indian mobile prefixes
    indian_mobile = re.findall(r'(?:\+91[\s⋄]?)?[6789]\d{9}', text)
    phone.extend(indian_mobile)
    
    for p in phone_fallback:
        digits_only = re.sub(r'\D', '', p)
        if len(digits_only) >= 10 and digits_only not in [re.sub(r'\D', '', existing) for existing in filtered_phone]:
            # Format the phone number nicely
            if len(digits_only) == 10 and digits_only[0] in '6789':  # Indian mobile
                formatted = f"+91-{digits_only[:5]}-{digits_only[5:]}"
                filtered_phone.append(formatted)
            elif len(digits_only) == 10:
                formatted = f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
                filtered_phone.append(formatted)
            elif len(digits_only) == 11 and digits_only.startswith('1'):
                formatted = f"+1-{digits_only[1:4]}-{digits_only[4:7]}-{digits_only[7:]}"
                filtered_phone.append(formatted)

    linkedin_url = next((url for url in urls if "linkedin.com" in url), None)
    github_url = next((url for url in urls if "github.com" in url), None)
    other_urls = [url for url in urls if "linkedin.com" not in url and "github.com" not in url]

    return {
        "email": email[0] if email else None,
        "phone": filtered_phone[0] if filtered_phone else None,
        "linkedin": linkedin_url,
        "github": github_url,
        "other_urls": other_urls
    }

def extract_skills(text, skills_list=None):
    """
    Extracts skills from text using multiple methods for better accuracy.
    """
    doc = nlp(text.lower())
    extracted_skills = set()

    # Use the provided skills list or default
    if not skills_list:
        skills_list = all_possible_skills

    # Method 1: PhraseMatcher for exact matches
    from spacy.matcher import PhraseMatcher
    matcher = PhraseMatcher(nlp.vocab)
    
    # Create patterns from the skills list
    patterns = [nlp.make_doc(skill.lower()) for skill in skills_list]
    matcher.add("SKILLS", patterns)

    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        # Add the original capitalized skill from the list
        for original_skill in skills_list:
            if original_skill.lower() == span.text:
                extracted_skills.add(original_skill)
                break
    
    # Method 2: Fuzzy matching for partial matches
    text_lower = text.lower()
    for skill in skills_list:
        skill_lower = skill.lower()
        # Check if skill appears as whole word or part of compound term
        if skill_lower in text_lower:
            # Additional validation to avoid false positives
            if (len(skill_lower) > 2 and  # Avoid matching very short terms
                (skill_lower in text_lower.split() or  # Exact word match
                 any(skill_lower in word for word in text_lower.split() if len(word) > 3))):  # Part of longer word
                extracted_skills.add(skill)
    
    # Method 3: Extract common tech patterns not in the predefined list
    tech_patterns = [
        r'\b(\w+(?:\.js|\.py|\.java|\.cpp|\.cs))\b',  # File extensions
        r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b',  # CamelCase terms
        r'\b(\w+(?:DB|SQL|API|SDK|IDE|CLI|GUI|REST|JSON|XML|HTML|CSS|UI|UX))\b',  # Tech suffixes
    ]
    
    for pattern in tech_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            potential_skill = match.group(1)
            if len(potential_skill) > 2 and potential_skill not in extracted_skills:
                # Only add if it looks like a legitimate tech term
                if any(char.isupper() for char in potential_skill) or any(suffix in potential_skill.lower() for suffix in ['js', 'py', 'sql', 'api', 'db']):
                    extracted_skills.add(potential_skill)
    
    # Clean up and return sorted list
    cleaned_skills = []
    for skill in extracted_skills:
        # Remove very short or generic terms
        if len(skill.strip()) > 1 and skill.strip().lower() not in ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']:
            cleaned_skills.append(skill.strip())
    
    return sorted(list(set(cleaned_skills)))

def extract_section(text, section_keywords, next_section_keywords=[]):
    """
    Extracts text belonging to a specific section by finding its heading
    and extracting content until the next known section heading or end of text.
    Prioritizes longer keywords for matching.
    """
    section_text = ""
    # Sort keywords by length descending to prioritize longer phrases
    sorted_section_keywords = sorted(section_keywords, key=len, reverse=True)
    
    # Try multiple patterns for section detection
    patterns = [
        r'(?i)(?:^|\n)\s*(' + '|'.join(map(re.escape, sorted_section_keywords)) + r')\s*:?\s*\n',
        r'(?i)(?:^|\n)\s*(' + '|'.join(map(re.escape, sorted_section_keywords)) + r')\s*:?\s*$',
        r'(?i)\b(' + '|'.join(map(re.escape, sorted_section_keywords)) + r')\s*:?\s*\n'
    ]
    
    start_match = None
    for pattern in patterns:
        start_match = re.search(pattern, text, re.MULTILINE)
        if start_match:
            break
    
    if start_match:
        section_start_index = start_match.end()
        temp_text = text[section_start_index:].strip()

        # Create patterns for the end of this section
        if next_section_keywords:
            sorted_next_section_keywords = sorted(next_section_keywords, key=len, reverse=True)
            end_patterns = [
                r'(?i)(?:^|\n)\s*(' + '|'.join(map(re.escape, sorted_next_section_keywords)) + r')\s*:?\s*\n',
                r'(?i)(?:^|\n)\s*(' + '|'.join(map(re.escape, sorted_next_section_keywords)) + r')\s*:?\s*$',
                r'(?i)\b(' + '|'.join(map(re.escape, sorted_next_section_keywords)) + r')\s*:?\s*\n'
            ]
            
            end_match = None
            for pattern in end_patterns:
                end_match = re.search(pattern, temp_text, re.MULTILINE)
                if end_match:
                    break
            
            if end_match:
                section_end_index = end_match.start()
                section_text = temp_text[:section_end_index].strip()
            else:
                section_text = temp_text
        else:
            section_text = temp_text

    return section_text

def parse_education_entries(education_text):
    """Parses raw education text into structured entries."""
    entries = []
    # Split by lines that strongly indicate a new education entry
    # Refined regex to better capture common education entry patterns
    potential_entry_splits = re.split(
        r'(?i)\n(?=\s*(?:Bachelor(?:\'s)?|Master(?:\'s)?|PhD|Doctorate|Diploma|Certificate|University|College|Institute|' +
        r'\b(?:of\s+Technology|of\s+Science|of\s+Arts|of\s+Engineering)\b|' + # Degrees
        r'\b\d{4}\b|' + # Year at start of line
        r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b|' + # City, State pattern
        r'\b(?:GPA|CGPA)\b|' + # GPA/CGPA indicators
        r'\b(?:Coursework|Relevant Courses)\b' +
        r'))',
        education_text.strip()
    )
    
    # Filter out empty strings and add to entries
    for entry_raw in potential_entry_splits:
        entry = entry_raw.strip()
        if entry: # Ensure the entry is not empty
            entries.append(entry)
            
    # If no splits occurred and the original education_text was not empty, treat it as one entry
    if not entries and education_text.strip():
        entries.append(education_text.strip())

    # Further refinement could involve grouping lines that belong to the same entry
    # For now, let's just use the direct splits.
    
    return sorted(list(set(entries)))


def parse_experience_entries(experience_text):
    """Parses raw experience text into structured entries."""
    entries = []
    # Split by lines that strongly indicate a new experience entry.
    # Refined regex to better capture common experience entry patterns
    potential_entry_splits = re.split(
        r'(?i)\n(?=\s*(?:^\d{4}\s*[-–]\s*(?:Present|\d{4})|' + # Date range at start of line (e.g., 2020 - Present)
        r'^\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*\|\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|' + # "Job Title | Company" pattern
        r'^\s*(?:Founder|Lead Developer|Backend Developer|Software Engineer|Manager|Analyst|Specialist|Associate|Intern|Consultant|Engineer|Developer|Architect|Director|President|CEO|CTO|VP)\b|' + # Common job titles
        r'\b(?:Company|Organization|Employer)\b' +
        r'))',
        experience_text.strip()
    )
    
    for entry_raw in potential_entry_splits:
        entry = entry_raw.strip()
        if entry:
            entries.append(entry)

    # If no splits occurred and the original experience_text was not empty, treat it as one entry
    if not entries and experience_text.strip():
        entries.append(experience_text.strip())
        
    return sorted(list(set(entries)))


def parse_resume(file_path):
    """
    Parses a resume file to extract key information.
    """
    text = extract_text(file_path)
    if not text:
        return {"error": "Could not extract text from file.", "parsed_data": {}}

    # --- Initial Name Extraction from raw text before full normalization ---
    name = None
    raw_lines = [line.strip() for line in text.split('\n') if line.strip()]
    if raw_lines:
        # Try multiple lines for name extraction
        for i, raw_line in enumerate(raw_lines[:3]):  # Check first 3 lines
            # Heuristic for name: 2-5 words, proper case, no numbers/emails, and not starting with a number
            words = raw_line.split()
            if len(words) >= 2 and len(words) <= 5 and \
               not re.search(r'[@\d]', raw_line) and \
               all(word[0].isupper() for word in words if word) and \
               not re.match(r'^\d', raw_line) and \
               not any(keyword.lower() in raw_line.lower() for keyword in ["summary", "skills", "experience", "education", "profile", "contact", "docker", "problem", "soft"]):
                # Additional check: should look like a real name (contains typical name patterns)
                if any(len(word) >= 2 for word in words):  # At least one word should be 2+ chars
                    name = raw_line
                    break
                
    # --- Normalize Text for other extractions ---
    normalized_text = normalize_text(text)
    doc = nlp(normalized_text)

    # --- Major Section Keywords ---
    major_section_keywords = [
        "summary", "profile", "skills", "experience", "work experience",
        "professional experience", "employment history", "career history",
        "education", "academic qualifications", "qualification", "qualifications",
        "academic background", "degrees", "projects", "awards", "publications",
        "certifications", "contact"
    ]

    # --- Fallback Name Extraction using spaCy on normalized text (if not found initially) ---
    if not name:
        # Search for PERSON entities in the first few lines of the normalized text
        potential_name_area_normalized = " ".join([line.strip() for line in normalized_text.split('\n') if line.strip()][:5]) # Increased lines to check
        doc_name_area = nlp(potential_name_area_normalized)
        for ent in doc_name_area.ents:
            if ent.label_ == "PERSON":
                # Heuristic: Name should have at least two words, not contain email (@) or digits,
                # not be excessively long, and not be a common section header or skill.
                if len(ent.text.split()) >= 2 and len(ent.text.split()) <= 5 and not re.search(r'[@\\d]', ent.text):
                    temp_name = ent.text.strip()
                    if temp_name.lower() not in [kw.lower() for kw in major_section_keywords] and \
                       temp_name.lower() not in [skill.lower() for skill in all_possible_skills]: # Avoid skills as names
                        name = temp_name
                        break
        # If spaCy still didn't find a good name, try a more general approach on the first line
        if not name and raw_lines:
            # A very lenient check for the first line if all else fails, assuming it's the name
            # This is a last resort and might pick up non-names if the resume is poorly formatted.
            first_line_candidate = raw_lines[0]
            if len(first_line_candidate.split()) >= 2 and len(first_line_candidate.split()) <= 5 and \
               not re.search(r'[@\\d]', first_line_candidate) and \
               not any(keyword.lower() in first_line_candidate.lower() for keyword in ["summary", "skills", "experience", "education", "profile", "contact"]):
                name = first_line_candidate


    # --- Contact Info ---
    contact_info = extract_contact_info(normalized_text)
    
    # --- Skills ---
    skills = extract_skills(normalized_text, skills_list=all_possible_skills)
    
    # --- Education ---
    education_section_text = extract_section(normalized_text, 
                                            section_keywords=["education", "academic qualifications", "qualification", "qualifications", "academic background", "degrees"],
                                            next_section_keywords=[kw for kw in major_section_keywords if kw not in ["education", "academic qualifications", "qualification", "qualifications", "academic background", "degrees"]])
    
    # Debug: if no education section found, try to find education info anywhere in text
    if not education_section_text.strip():
        # Look for degree keywords anywhere in the text
        degree_indicators = ["university", "college", "bachelor", "master", "degree", "phd", "diploma", "institute", "academic", "graduation", "graduated"]
        for line in normalized_text.split('\n'):
            if any(indicator in line.lower() for indicator in degree_indicators):
                education_section_text += line + '\n'
    
    education = parse_education_entries(education_section_text)
    
    # --- Experience ---
    experience_section_text = extract_section(normalized_text, 
                                            section_keywords=["experience", "work experience", "professional experience", "employment history", "career history"],
                                            next_section_keywords=[kw for kw in major_section_keywords if kw not in ["experience", "work experience", "professional experience", "employment history", "career history"]])
    
    # Debug: if no experience section found, try to find work-related content
    if not experience_section_text.strip():
        # Look for experience indicators anywhere in the text
        work_indicators = ["intern", "developer", "engineer", "analyst", "manager", "founded", "worked", "company", "organization", "employed", "position", "role"]
        for line in normalized_text.split('\n'):
            if any(indicator in line.lower() for indicator in work_indicators):
                experience_section_text += line + '\n'
    
    experience = parse_experience_entries(experience_section_text)

    # --- Projects ---
    projects = []
    # Look for project indicators in the text
    project_lines = []
    for line in normalized_text.split('\n'):
        line_lower = line.lower()
        if any(indicator in line_lower for indicator in ["project", "developed", "built", "created", "designed", "implemented", "artisanconnect", "platform"]):
            if line.strip() and len(line.strip()) > 10:  # Meaningful project lines
                project_lines.append(line.strip())
    
    # Group consecutive project lines
    if project_lines:
        current_project = ""
        for line in project_lines:
            if line.endswith(':') or any(word in line.lower() for word in ["project", "platform", "application"]):
                if current_project:
                    projects.append(current_project.strip())
                current_project = line
            else:
                current_project += " " + line
        if current_project:
            projects.append(current_project.strip())

    return {
        "name": name,
        "contact_info": contact_info,
        "skills": skills,
        "education": education,
        "experience": experience,
        "projects": projects,
        "leadership": [] # Placeholder for leadership, will need dedicated extraction
    }

if __name__ == "__main__":
    print("\n--- Starting Resume Information Extraction Test ---") # This line is changed for verification

    pdf_sample_path = "dummy.pdf"
    docx_sample_path = "dummy.docx" 

    # --- Test with dummy.pdf ---
    if os.path.exists(pdf_sample_path):
        print(f"\n--- Testing with {pdf_sample_path} ---")
        parsed_pdf_data = parse_resume(pdf_sample_path)
        print(json.dumps(parsed_pdf_data, indent=4))
        with open("parsed_dummy_pdf.json", "w") as f:
            json.dump(parsed_pdf_data, f, indent=4)
        print("Parsed data saved to parsed_dummy_pdf.json")
    else:
        print(f"\nSkipping PDF test: {pdf_sample_path} not found.")

    # --- Test with dummy.docx ---
    if os.path.exists(docx_sample_path):
        print(f"\n--- Testing with {docx_sample_path} ---")
        parsed_docx_data = parse_resume(docx_sample_path)
        print(json.dumps(parsed_docx_data, indent=4))
        with open("parsed_dummy_docx.json", "w") as f:
            json.dump(parsed_docx_data, f, indent=4)
        print("Parsed data saved to parsed_dummy_docx.json")
    else:
        print(f"\nSkipping DOCX test: {docx_sample_path} not found.")

    print("\n--- Information Extraction Testing Complete ---")
    print("Ensure 'dummy.pdf' and 'dummy.docx' contain resume-like text for accurate testing.")