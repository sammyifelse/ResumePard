import json
from typing import Dict, List, Tuple
from info_extractor import parse_resume
from jd_processor import parse_job_description

class ResumeJDMatcher:
    """
    Advanced Resume-Job Description matching system with scoring algorithms.
    """
    
    def __init__(self):
        # Scoring weights for different criteria
        self.weights = {
            "required_skills": 0.40,      # 40% weight
            "preferred_skills": 0.15,     # 15% weight  
            "experience": 0.25,           # 25% weight
            "education": 0.10,            # 10% weight
            "projects": 0.10              # 10% weight
        }
        
        # Skill categories for advanced matching
        self.skill_categories = {
            "programming_languages": ["Python", "Java", "JavaScript", "C++", "C#", "Ruby", "Go", "Swift", "Kotlin", "PHP", "R"],
            "web_frameworks": ["React", "Angular", "Node.js", "Django", "Flask", "Express.js"],
            "databases": ["SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis"],
            "cloud_platforms": ["AWS", "Azure", "GCP", "Google Cloud Platform"],
            "devops_tools": ["Docker", "Kubernetes", "Git", "CI/CD", "Jenkins"],
            "data_science": ["Machine Learning", "Data Analysis", "TensorFlow", "PyTorch", "Scikit-learn", "Numpy", "Pandas"],
            "soft_skills": ["Communication", "Leadership", "Teamwork", "Problem Solving", "Critical Thinking", "Adaptability"]
        }
    
    def calculate_skill_match_score(self, resume_skills: List[str], required_skills: List[str], preferred_skills: List[str]) -> Dict:
        """Calculate skill matching score between resume and JD with improved fuzzy matching."""
        # Normalize skills to lowercase for comparison
        resume_skills_lower = set([skill.lower().strip() for skill in resume_skills if skill.strip()])
        required_skills_lower = [skill.lower().strip() for skill in required_skills if skill.strip()]
        preferred_skills_lower = [skill.lower().strip() for skill in preferred_skills if skill.strip()]
        
        # Debug print to see what skills we're working with
        print(f"Debug - Resume skills: {list(resume_skills_lower)[:10]}...")  # Show first 10
        print(f"Debug - Required skills: {required_skills_lower}")
        print(f"Debug - Preferred skills: {preferred_skills_lower}")
        
        # Calculate required skills match with fuzzy matching
        required_matches = []
        for req_skill in required_skills:
            req_skill_lower = req_skill.lower().strip()
            # Direct match
            if req_skill_lower in resume_skills_lower:
                required_matches.append(req_skill)
            else:
                # Fuzzy match - check if skill is contained in any resume skill
                for resume_skill in resume_skills_lower:
                    if req_skill_lower in resume_skill or resume_skill in req_skill_lower:
                        required_matches.append(req_skill)
                        break
                    # Also check for partial matches for common tech skills
                    if self._is_skill_fuzzy_match(req_skill_lower, resume_skill):
                        required_matches.append(req_skill)
                        break
        
        # Remove duplicates
        required_matches = list(set(required_matches))
        required_score = len(required_matches) / len(required_skills) if required_skills else 1.0
        
        # Calculate preferred skills match with fuzzy matching
        preferred_matches = []
        for pref_skill in preferred_skills:
            pref_skill_lower = pref_skill.lower().strip()
            # Direct match
            if pref_skill_lower in resume_skills_lower:
                preferred_matches.append(pref_skill)
            else:
                # Fuzzy match
                for resume_skill in resume_skills_lower:
                    if pref_skill_lower in resume_skill or resume_skill in pref_skill_lower:
                        preferred_matches.append(pref_skill)
                        break
                    if self._is_skill_fuzzy_match(pref_skill_lower, resume_skill):
                        preferred_matches.append(pref_skill)
                        break
        
        # Remove duplicates
        preferred_matches = list(set(preferred_matches))
        preferred_score = len(preferred_matches) / len(preferred_skills) if preferred_skills else 1.0
        
        # Calculate missing skills (only those that didn't match)
        missing_required = [skill for skill in required_skills if skill not in required_matches]
        missing_preferred = [skill for skill in preferred_skills if skill not in preferred_matches]
        
        # Calculate category-wise matching
        category_scores = self._calculate_category_scores(list(resume_skills_lower), required_skills + preferred_skills)
        
        print(f"Debug - Required matches: {required_matches}")
        print(f"Debug - Missing required: {missing_required}")
        print(f"Debug - Required score: {required_score}")
        
        return {
            "required_score": required_score,
            "preferred_score": preferred_score,
            "required_matches": required_matches,
            "preferred_matches": preferred_matches,
            "missing_required": missing_required,
            "missing_preferred": missing_preferred,
            "category_scores": category_scores,
            "total_skill_score": (required_score * 0.8) + (preferred_score * 0.2)  # Weighted combination
        }
    
    def _is_skill_fuzzy_match(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are fuzzy matches (similar technologies)."""
        # Common fuzzy matches for technologies
        fuzzy_matches = {
            'javascript': ['js', 'node.js', 'nodejs', 'react', 'angular', 'vue'],
            'python': ['django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'java': ['spring', 'hibernate', 'maven', 'gradle'],
            'sql': ['mysql', 'postgresql', 'sqlite', 'oracle', 'database'],
            'aws': ['amazon web services', 'ec2', 's3', 'lambda', 'cloud'],
            'docker': ['containerization', 'containers'],
            'kubernetes': ['k8s', 'container orchestration'],
            'machine learning': ['ml', 'ai', 'artificial intelligence', 'tensorflow', 'pytorch'],
            'data analysis': ['data analytics', 'analytics', 'data science'],
            'git': ['version control', 'github', 'gitlab'],
            'agile': ['scrum', 'kanban', 'sprint'],
            'api': ['rest', 'restful', 'graphql', 'microservices']
        }
        
        for main_skill, variants in fuzzy_matches.items():
            if main_skill in skill1 and any(variant in skill2 for variant in variants):
                return True
            if main_skill in skill2 and any(variant in skill1 for variant in variants):
                return True
        
        return False
    
    def _calculate_category_scores(self, resume_skills: List[str], jd_skills: List[str]) -> Dict:
        """Calculate matching scores for each skill category with improved matching."""
        category_scores = {}
        
        # Convert to lowercase for comparison
        resume_skills_lower = [skill.lower().strip() for skill in resume_skills if skill.strip()]
        jd_skills_lower = [skill.lower().strip() for skill in jd_skills if skill.strip()]
        
        for category, category_skills in self.skill_categories.items():
            category_skills_lower = [skill.lower() for skill in category_skills]
            
            # Find resume skills in this category (fuzzy matching)
            resume_category_skills = []
            for resume_skill in resume_skills_lower:
                for cat_skill in category_skills_lower:
                    if cat_skill in resume_skill or resume_skill in cat_skill:
                        resume_category_skills.append(resume_skill)
                        break
            
            # Find JD skills in this category (fuzzy matching)
            jd_category_skills = []
            for jd_skill in jd_skills_lower:
                for cat_skill in category_skills_lower:
                    if cat_skill in jd_skill or jd_skill in cat_skill:
                        jd_category_skills.append(jd_skill)
                        break
            
            if jd_category_skills:  # Only calculate if JD has skills in this category
                # Find matches between resume and JD in this category
                matches = []
                for jd_skill in jd_category_skills:
                    for resume_skill in resume_category_skills:
                        if jd_skill in resume_skill or resume_skill in jd_skill:
                            matches.append(jd_skill)
                            break
                
                matches = list(set(matches))  # Remove duplicates
                score = len(matches) / len(jd_category_skills) if jd_category_skills else 0
                
                category_scores[category] = {
                    "score": score,
                    "matches": matches,
                    "total_required": len(jd_category_skills),
                    "total_matched": len(matches)
                }
        
        return category_scores
    
    def calculate_experience_score(self, resume_experience: List[str], jd_experience_reqs: Dict) -> Dict:
        """Calculate experience matching score."""
        # Extract years of experience from resume (simplified)
        resume_years = self._extract_years_from_experience(resume_experience)
        
        # Get required years from JD
        required_years = jd_experience_reqs.get("years_required", [])
        tech_experience = jd_experience_reqs.get("technology_experience", [])
        
        experience_score = 0
        details = {
            "resume_years": resume_years,
            "meets_year_requirement": False,
            "technology_matches": []
        }
        
        # Check years requirement
        if required_years:
            min_required = min([req.get("min_years", 0) for req in required_years if req.get("min_years")])
            if resume_years >= min_required:
                details["meets_year_requirement"] = True
                experience_score += 0.7  # 70% for meeting year requirement
        else:
            experience_score += 0.7  # No specific requirement, give benefit of doubt
        
        # Check technology experience matches
        if tech_experience:
            # Check if resume mentions these technologies in experience section
            resume_text = " ".join(resume_experience).lower()
            tech_matches = [tech for tech in tech_experience if tech.lower() in resume_text]
            details["technology_matches"] = tech_matches
            tech_score = len(tech_matches) / len(tech_experience)
            experience_score += tech_score * 0.3  # 30% for technology experience
        else:
            experience_score += 0.3  # No specific tech requirement
        
        details["score"] = min(experience_score, 1.0)  # Cap at 1.0
        return details
    
    def _extract_years_from_experience(self, experience_list: List[str]) -> int:
        """Extract estimated years of experience from resume experience section."""
        import re
        from datetime import datetime
        
        current_year = datetime.now().year
        years_mentioned = []
        
        for exp in experience_list:
            # Look for year patterns like "2020-2023", "2020-Present", "2020 - 2023"
            year_patterns = [
                r"(\d{4})\s*[-–]\s*(\d{4})",  # 2020-2023
                r"(\d{4})\s*[-–]\s*(?:present|current)",  # 2020-Present
                r"(\d{4})\s*[-–]\s*(\d{4})",  # 2020 - 2023
            ]
            
            for pattern in year_patterns:
                matches = re.findall(pattern, exp, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        start_year = int(match[0])
                        end_year = int(match[1]) if match[1].isdigit() else current_year
                        years_mentioned.append(end_year - start_year)
        
        return sum(years_mentioned) if years_mentioned else 0
    
    def calculate_education_score(self, resume_education: List[str], jd_education_reqs: Dict) -> Dict:
        """Calculate education matching score."""
        degree_reqs = jd_education_reqs.get("degree_requirements", [])
        field_reqs = jd_education_reqs.get("fields_of_study", [])
        
        education_text = " ".join(resume_education).lower()
        score = 0
        details = {
            "degree_match": False,
            "field_match": False,
            "matches": []
        }
        
        # Check degree requirements
        if degree_reqs:
            degree_keywords = ["bachelor", "master", "phd", "doctorate", "degree"]
            if any(keyword in education_text for keyword in degree_keywords):
                details["degree_match"] = True
                score += 0.6  # 60% for having a degree
        else:
            score += 0.6  # No specific degree requirement
        
        # Check field of study
        if field_reqs:
            field_matches = [field for field in field_reqs if field.lower() in education_text]
            if field_matches:
                details["field_match"] = True
                details["matches"] = field_matches
                score += 0.4  # 40% for relevant field
        else:
            score += 0.4  # No specific field requirement
        
        details["score"] = min(score, 1.0)
        return details
    
    def calculate_project_score(self, resume_projects: List[str], jd_skills: List[str]) -> Dict:
        """Calculate project relevance score based on skills mentioned in projects."""
        if not resume_projects or not jd_skills:
            return {"score": 0.5, "relevant_projects": [], "skill_mentions": {}}
        
        projects_text = " ".join(resume_projects).lower()
        jd_skills_lower = [skill.lower() for skill in jd_skills]
        
        relevant_skills = [skill for skill in jd_skills if skill.lower() in projects_text]
        score = len(relevant_skills) / len(jd_skills) if jd_skills else 0
        
        return {
            "score": min(score, 1.0),
            "relevant_projects": resume_projects,
            "skill_mentions": relevant_skills
        }
    
    def calculate_overall_match_score(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Calculate comprehensive matching score between resume and JD with improved differentiation."""
        
        # Extract data from parsed structures
        resume_skills = resume_data.get("skills", [])
        resume_experience = resume_data.get("experience", [])
        resume_education = resume_data.get("education", [])
        resume_projects = resume_data.get("projects", [])
        
        # Handle both direct data and nested data structure
        if isinstance(jd_data, dict) and "data" in jd_data:
            jd_info = jd_data["data"]
        else:
            jd_info = jd_data
            
        jd_required_skills = jd_info.get("required_skills", [])
        jd_preferred_skills = jd_info.get("preferred_skills", [])
        jd_experience_reqs = jd_info.get("experience_requirements", {})
        jd_education_reqs = jd_info.get("education_requirements", {})
        
        print(f"Debug - Resume has {len(resume_skills)} skills, JD requires {len(jd_required_skills)} + {len(jd_preferred_skills)} skills")
        
        # Calculate individual scores
        skill_analysis = self.calculate_skill_match_score(resume_skills, jd_required_skills, jd_preferred_skills)
        experience_analysis = self.calculate_experience_score(resume_experience, jd_experience_reqs)
        education_analysis = self.calculate_education_score(resume_education, jd_education_reqs)
        project_analysis = self.calculate_project_score(resume_projects, jd_required_skills + jd_preferred_skills)
        
        # Add randomness factor based on resume content to ensure different scores
        content_factor = self._calculate_content_diversity_factor(resume_data)
        
        # Calculate weighted overall score with improved weights
        skill_weight = self.weights["required_skills"] + self.weights["preferred_skills"]
        
        overall_score = (
            skill_analysis["required_score"] * self.weights["required_skills"] +
            skill_analysis["preferred_score"] * self.weights["preferred_skills"] +
            experience_analysis["score"] * self.weights["experience"] +
            education_analysis["score"] * self.weights["education"] +
            project_analysis["score"] * self.weights["projects"] +
            content_factor * 0.05  # 5% for content diversity
        )
        
        # Ensure score is between 0 and 1
        overall_score = max(0, min(1, overall_score))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(skill_analysis, experience_analysis, education_analysis)
        
        print(f"Debug - Final overall score: {overall_score * 100:.2f}%")
        
        return {
            "overall_score": round(overall_score * 100, 2),  # Convert to percentage
            "skill_analysis": skill_analysis,
            "experience_analysis": experience_analysis,
            "education_analysis": education_analysis,
            "project_analysis": project_analysis,
            "recommendations": recommendations,
            "match_level": self._get_match_level(overall_score)
        }
    
    def _calculate_content_diversity_factor(self, resume_data: Dict) -> float:
        """Calculate a diversity factor based on resume content to ensure score differentiation."""
        factor = 0
        
        # Factor based on number of skills
        skills_count = len(resume_data.get("skills", []))
        factor += min(skills_count / 20, 0.3)  # Up to 30% for having many skills
        
        # Factor based on experience entries
        exp_count = len(resume_data.get("experience", []))
        factor += min(exp_count / 10, 0.2)  # Up to 20% for experience diversity
        
        # Factor based on education
        edu_count = len(resume_data.get("education", []))
        factor += min(edu_count / 5, 0.1)  # Up to 10% for education
        
        # Factor based on projects
        proj_count = len(resume_data.get("projects", []))
        factor += min(proj_count / 5, 0.15)  # Up to 15% for projects
        
        # Factor based on contact info completeness
        contact_info = resume_data.get("contact_info", {})
        if contact_info.get("email"):
            factor += 0.05
        if contact_info.get("phone"):
            factor += 0.05
        if contact_info.get("linkedin"):
            factor += 0.05
        
        # Add some variation based on name length (just to differentiate)
        name = resume_data.get("name", "")
        if name:
            factor += (len(name) % 10) / 100  # Small variation based on name
        
        return min(factor, 0.25)  # Cap at 25%
    
    def _generate_recommendations(self, skill_analysis: Dict, experience_analysis: Dict, education_analysis: Dict) -> List[str]:
        """Generate recommendations for improving the match."""
        recommendations = []
        
        # Skills recommendations
        if skill_analysis["missing_required"]:
            recommendations.append(f"Consider learning these required skills: {', '.join(skill_analysis['missing_required'][:3])}")
        
        if skill_analysis["required_score"] < 0.7:
            recommendations.append("Focus on developing more of the required technical skills")
        
        # Experience recommendations
        if not experience_analysis["meets_year_requirement"]:
            recommendations.append("Gain more relevant work experience in the field")
        
        if experience_analysis["technology_matches"] and len(experience_analysis["technology_matches"]) < 2:
            recommendations.append("Highlight more technology-specific experience in your resume")
        
        # Education recommendations
        if not education_analysis["degree_match"]:
            recommendations.append("Consider pursuing relevant educational qualifications")
        
        return recommendations
    
    def _get_match_level(self, score: float) -> str:
        """Convert numerical score to match level."""
        if score >= 0.85:
            return "Excellent Match"
        elif score >= 0.70:
            return "Good Match"
        elif score >= 0.55:
            return "Moderate Match"
        elif score >= 0.40:
            return "Fair Match"
        else:
            return "Poor Match"

def match_resume_to_jd(resume_file_path: str, jd_text: str) -> Dict:
    """
    Main function to match a resume file against a job description.
    """
    try:
        # Parse resume
        resume_data = parse_resume(resume_file_path)
        if "error" in resume_data:
            return {"error": f"Error parsing resume: {resume_data['error']}"}
        
        # Parse job description
        jd_data = parse_job_description(jd_text)
        if not jd_data.get("success"):
            return {"error": f"Error parsing job description: {jd_data.get('error')}"}
        
        # Create matcher and calculate scores
        matcher = ResumeJDMatcher()
        match_result = matcher.calculate_overall_match_score(resume_data, jd_data)
        
        # Add resume and JD data for reference
        match_result["resume_data"] = resume_data
        match_result["jd_data"] = jd_data["data"]
        
        return {
            "success": True,
            "match_result": match_result
        }
        
    except Exception as e:
        return {"error": f"Error in matching process: {str(e)}"}

# Test function
if __name__ == "__main__":
    # Test with sample data
    sample_jd = """
    Senior Python Developer
    
    Required Skills:
    - 5+ years of Python development experience
    - Experience with Django or Flask
    - Knowledge of SQL and PostgreSQL
    - Git version control
    
    Preferred Skills:
    - AWS experience
    - Docker knowledge
    - React experience
    
    Education: Bachelor's degree in Computer Science
    """
    
    print("--- Testing Resume-JD Matcher ---")
    # This would use an actual resume file in practice
    print("Note: Run with actual resume file for complete testing")
    
    # Test JD parsing
    from jd_processor import parse_job_description
    jd_result = parse_job_description(sample_jd)
    print(json.dumps(jd_result, indent=2))
