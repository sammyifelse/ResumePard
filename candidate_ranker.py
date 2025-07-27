import json
import os
from typing import List, Dict, Tuple
from resume_matcher import match_resume_to_jd, ResumeJDMatcher
from info_extractor import parse_resume
from jd_processor import parse_job_description

class CandidateRanker:
    """
    Advanced candidate ranking system that processes multiple resumes against a job description
    and ranks candidates based on various criteria.
    """
    
    def __init__(self):
        self.matcher = ResumeJDMatcher()
        
        # Additional ranking criteria weights
        self.ranking_weights = {
            "overall_match_score": 0.50,    # 50% - Core matching score
            "skill_diversity": 0.15,        # 15% - Breadth of skills
            "experience_quality": 0.20,     # 20% - Quality of experience
            "education_level": 0.10,        # 10% - Education background
            "project_relevance": 0.05       # 5% - Project quality
        }
    
    def rank_candidates(self, resume_files: List[str], jd_text: str, output_file: str = None) -> Dict:
        """
        Rank multiple candidates against a job description.
        
        Args:
            resume_files: List of paths to resume files
            jd_text: Job description text
            output_file: Optional path to save ranking results
            
        Returns:
            Dictionary containing ranked candidates and analysis
        """
        
        print(f"🔍 Starting candidate ranking for {len(resume_files)} resumes...")
        
        # Parse job description once
        jd_data = parse_job_description(jd_text)
        if not jd_data.get("success"):
            return {"error": f"Error parsing job description: {jd_data.get('error')}"}
        
        candidates = []
        errors = []
        
        # Process each resume
        for i, resume_file in enumerate(resume_files, 1):
            print(f"📄 Processing resume {i}/{len(resume_files)}: {os.path.basename(resume_file)}")
            
            try:
                # Parse resume
                resume_data = parse_resume(resume_file)
                if "error" in resume_data:
                    errors.append({"file": resume_file, "error": resume_data["error"]})
                    continue
                
                # Calculate match score
                match_result = self.matcher.calculate_overall_match_score(resume_data, jd_data)
                
                # Calculate additional ranking metrics
                additional_scores = self._calculate_additional_scores(resume_data, jd_data["data"])
                
                # Calculate final ranking score
                final_score = self._calculate_final_ranking_score(match_result, additional_scores)
                
                candidate_info = {
                    "file_path": resume_file,
                    "file_name": os.path.basename(resume_file),
                    "candidate_name": resume_data.get("name", "Unknown"),
                    "email": resume_data.get("contact_info", {}).get("email", "No email provided"),
                    "phone": resume_data.get("contact_info", {}).get("phone", "No phone provided"),
                    "linkedin": resume_data.get("contact_info", {}).get("linkedin", "No LinkedIn provided"),
                    "overall_match_score": match_result.get("overall_score", 0),
                    "match_level": match_result.get("match_level", "Poor Match"),
                    "final_ranking_score": final_score,
                    "skill_analysis": match_result.get("skill_analysis", {}),
                    "experience_analysis": match_result.get("experience_analysis", {}),
                    "education_analysis": match_result.get("education_analysis", {}),
                    "project_analysis": match_result.get("project_analysis", {}),
                    "additional_scores": additional_scores,
                    "recommendations": match_result.get("recommendations", []),
                    "resume_summary": self._generate_candidate_summary(resume_data)
                }
                
                candidates.append(candidate_info)
                
            except Exception as e:
                errors.append({"file": resume_file, "error": str(e)})
                print(f"❌ Error processing {resume_file}: {str(e)}")
        
        # Sort candidates by final ranking score (highest first) with tie-breaking
        candidates.sort(key=lambda x: (
            x["final_ranking_score"],  # Primary: final score
            x.get("overall_match_score", 0),  # Secondary: base match score
            len(x.get("skill_analysis", {}).get("required_matches", [])),  # Tertiary: required skills matched
            len(x.get("skill_analysis", {}).get("preferred_matches", [])),  # Quaternary: preferred skills matched
            x.get("candidate_name", "").lower()  # Final: alphabetical by name
        ), reverse=True)
        
        # Add ranking positions
        for i, candidate in enumerate(candidates, 1):
            candidate["rank"] = i
            candidate["percentile"] = round((len(candidates) - i + 1) / len(candidates) * 100, 1)
        
        # Generate ranking analysis
        ranking_analysis = self._generate_ranking_analysis(candidates, jd_data["data"])
        
        result = {
            "success": True,
            "total_candidates": len(candidates),
            "processing_errors": len(errors),
            "job_description_summary": self._summarize_jd(jd_data["data"]),
            "ranking_analysis": ranking_analysis,
            "candidates": candidates,
            "errors": errors if errors else None
        }
        
        # Save to file if requested
        if output_file:
            self._save_ranking_results(result, output_file)
            print(f"💾 Results saved to {output_file}")
        
        return result
    
    def _calculate_additional_scores(self, resume_data: Dict, jd_data: Dict) -> Dict:
        """Calculate additional scoring metrics beyond basic matching with better differentiation."""
        
        scores = {}
        
        # Skill diversity score with improved calculation
        resume_skills = resume_data.get("skills", [])
        # Ensure resume_skills is a list and contains valid strings
        if not isinstance(resume_skills, list):
            resume_skills = []
        resume_skills = [skill for skill in resume_skills if skill and isinstance(skill, str)]
        
        skill_categories = self.matcher.skill_categories if hasattr(self.matcher, 'skill_categories') else {}
        
        if skill_categories:
            categories_covered = 0
            for category, category_skills in skill_categories.items():
                if not isinstance(category_skills, list):
                    continue
                category_skills_lower = [skill.lower() for skill in category_skills if skill and isinstance(skill, str)]
                resume_skills_lower = [skill.lower() for skill in resume_skills if skill and isinstance(skill, str)]
                
                # Check for matches in this category (fuzzy matching)
                if any(any(cat_skill in resume_skill or resume_skill in cat_skill 
                          for resume_skill in resume_skills_lower) 
                      for cat_skill in category_skills_lower):
                    categories_covered += 1
            
            scores["skill_diversity"] = categories_covered / len(skill_categories) if skill_categories else 0
        else:
            # Fallback with better differentiation based on actual skill count and diversity
            unique_skills = len(set(skill.lower() for skill in resume_skills))
            skill_diversity_base = min(unique_skills / 15, 1.0)  # Cap at 15 unique skills
            
            # Add bonus for skill variety (different types of skills)
            technical_skills = ["python", "java", "javascript", "react", "sql", "aws", "docker", "kubernetes"]
            soft_skills = ["leadership", "communication", "teamwork", "problem solving", "management"]
            
            tech_count = sum(1 for skill in resume_skills if any(tech in skill.lower() for tech in technical_skills))
            soft_count = sum(1 for skill in resume_skills if any(soft in skill.lower() for soft in soft_skills))
            
            variety_bonus = min((tech_count + soft_count) / 10, 0.3)  # Up to 30% bonus for variety
            scores["skill_diversity"] = min(skill_diversity_base + variety_bonus, 1.0)
        
        # Experience quality score (based on variety and depth) - improved
        experience_entries = resume_data.get("experience", [])
        # Ensure experience_entries is a list and contains valid strings
        if not isinstance(experience_entries, list):
            experience_entries = []
        safe_experience = []
        for exp in experience_entries:
            if exp and isinstance(exp, str):
                safe_experience.append(exp)
            elif exp:
                safe_experience.append(str(exp))
        
        experience_text = " ".join(safe_experience).lower() if safe_experience else ""
        
        quality_indicators = [
            "led", "managed", "developed", "designed", "implemented", "created",
            "improved", "optimized", "launched", "delivered", "architected",
            "built", "established", "coordinated", "supervised", "mentored",
            "collaborated", "executed", "achieved", "enhanced", "streamlined"
        ]
        
        # Count unique quality indicators + add bonus for experience variety
        quality_matches = set()
        for indicator in quality_indicators:
            if indicator in experience_text:
                quality_matches.add(indicator)
        
        base_quality_score = len(quality_matches) / len(quality_indicators)
        
        # Add bonus for experience length and variety with better differentiation
        exp_length_bonus = min(len(safe_experience) / 4, 0.25)  # Up to 25% bonus for experience variety
        exp_word_count = len(experience_text.split())
        exp_detail_bonus = min(exp_word_count / 300, 0.15)  # Up to 15% bonus for detailed experience
        
        # Add bonus for specific experience keywords that show seniority
        senior_keywords = ["senior", "lead", "principal", "architect", "manager", "director", "head"]
        achievement_keywords = ["increased", "reduced", "improved", "saved", "generated", "boosted"]
        
        senior_bonus = sum(0.02 for keyword in senior_keywords if keyword in experience_text)  # 2% per senior keyword
        achievement_bonus = sum(0.01 for keyword in achievement_keywords if keyword in experience_text)  # 1% per achievement
        
        scores["experience_quality"] = min(base_quality_score + exp_length_bonus + exp_detail_bonus + senior_bonus + achievement_bonus, 1.0)
        
        # Education level score - improved with more granular scoring
        education_entries = resume_data.get("education", [])
        # Ensure education_entries is a list and contains valid strings
        if not isinstance(education_entries, list):
            education_entries = []
        safe_education = []
        for edu in education_entries:
            if edu and isinstance(edu, str):
                safe_education.append(edu)
            elif edu:
                safe_education.append(str(edu))
        
        education_text = " ".join(safe_education).lower() if safe_education else ""
        
        education_score = 0.1  # Base score for having any education info
        
        # Degree level scoring
        if "phd" in education_text or "doctorate" in education_text or "doctoral" in education_text:
            education_score = 1.0
        elif "master" in education_text or "mba" in education_text or "m.s" in education_text or "m.a" in education_text:
            education_score = 0.8
        elif "bachelor" in education_text or "b.s" in education_text or "b.a" in education_text or "b.tech" in education_text:
            education_score = 0.6
        elif any(term in education_text for term in ["degree", "diploma", "certificate", "graduation"]):
            education_score = 0.4
        
        # Add bonus for relevant fields
        relevant_fields = ["computer science", "engineering", "technology", "software", "information technology"]
        if any(field in education_text for field in relevant_fields):
            education_score += 0.1
        
        # Add bonus for multiple degrees
        degree_count = education_text.count("degree") + education_text.count("bachelor") + education_text.count("master") + education_text.count("phd")
        if degree_count > 1:
            education_score += 0.1
        
        scores["education_level"] = min(education_score, 1.0)
        
        # Project relevance score - enhanced
        projects = resume_data.get("projects", [])
        jd_skills = jd_data.get("required_skills", []) + jd_data.get("preferred_skills", [])
        
        if projects and jd_skills:
            # Ensure projects are strings and handle None values
            safe_projects = []
            for project in projects:
                if project and isinstance(project, str):
                    safe_projects.append(project)
                elif project:
                    safe_projects.append(str(project))
            
            projects_text = " ".join(safe_projects).lower() if safe_projects else ""
            jd_skills_lower = [skill.lower() for skill in jd_skills if skill]
            
            # Count skill mentions in projects (fuzzy matching)
            relevant_skills_in_projects = []
            for skill in jd_skills:
                skill_lower = skill.lower()
                if skill_lower in projects_text:
                    relevant_skills_in_projects.append(skill)
                else:
                    # Check for partial matches
                    for project_word in projects_text.split():
                        if skill_lower in project_word or project_word in skill_lower:
                            relevant_skills_in_projects.append(skill)
                            break
            
            # Remove duplicates and calculate score
            relevant_skills_in_projects = list(set(relevant_skills_in_projects))
            base_project_score = len(relevant_skills_in_projects) / len(jd_skills)
            
            # Add bonus for project quantity and detail with better granularity
            project_bonus = min(len(safe_projects) / 2.5, 0.15)  # Up to 15% bonus for multiple projects
            project_detail = len(projects_text.split())
            detail_bonus = min(project_detail / 150, 0.08)  # Up to 8% bonus for detailed projects
            
            # Add bonus for project complexity indicators
            complexity_indicators = ["architecture", "scalability", "performance", "optimization", "integration", "deployment"]
            complexity_bonus = sum(0.01 for indicator in complexity_indicators if indicator in projects_text)  # 1% per complexity indicator
            
            scores["project_relevance"] = min(base_project_score + project_bonus + detail_bonus + complexity_bonus, 1.0)
        else:
            # Give differentiated credit based on having projects
            if projects and len(projects) > 0:
                # Scale based on number of projects and their content
                project_count_bonus = min(len(projects) / 5, 0.4)  # Up to 40% for having multiple projects
                if isinstance(projects, list) and projects:
                    content_length = sum(len(str(p)) for p in projects if p)
                    content_bonus = min(content_length / 200, 0.2)  # Up to 20% for project content
                    scores["project_relevance"] = min(0.3 + project_count_bonus + content_bonus, 1.0)
                else:
                    scores["project_relevance"] = 0.3
            else:
                scores["project_relevance"] = 0.1  # Lower neutral score
        
        return scores
    
    def _calculate_final_ranking_score(self, match_result: Dict, additional_scores: Dict) -> float:
        """Calculate the final ranking score using weighted combination with better differentiation."""
        
        # Convert overall match score to 0-1 scale - handle None values
        base_score = (match_result.get("overall_score", 0) or 0) / 100
        
        # Add small random factor to ensure no two candidates have exactly the same score
        import random
        random.seed(hash(str(match_result)) % (2**32))  # Deterministic randomness based on match_result
        uniqueness_factor = random.uniform(0.001, 0.009)  # Small random factor (0.1% to 0.9%)
        
        # Calculate weighted score with more precision
        final_score = (
            base_score * self.ranking_weights["overall_match_score"] +
            additional_scores.get("skill_diversity", 0) * self.ranking_weights["skill_diversity"] +
            additional_scores.get("experience_quality", 0) * self.ranking_weights["experience_quality"] +
            additional_scores.get("education_level", 0) * self.ranking_weights["education_level"] +
            additional_scores.get("project_relevance", 0) * self.ranking_weights["project_relevance"] +
            uniqueness_factor  # Add small differentiation factor
        )
        
        # Add bonus scoring for specific differentiators
        bonus_score = 0
        
        # Skill analysis bonus
        skill_analysis = match_result.get("skill_analysis", {})
        required_matches = len(skill_analysis.get("required_matches", []))
        preferred_matches = len(skill_analysis.get("preferred_matches", []))
        
        # Give bonus based on exact number of skill matches
        bonus_score += (required_matches * 0.002)  # 0.2% per required skill match
        bonus_score += (preferred_matches * 0.001)  # 0.1% per preferred skill match
        
        # Experience quality bonus
        experience_analysis = match_result.get("experience_analysis", {})
        if experience_analysis.get("meets_year_requirement"):
            bonus_score += 0.005  # 0.5% bonus for meeting experience requirements
        
        # Education bonus
        education_analysis = match_result.get("education_analysis", {})
        if education_analysis.get("degree_match"):
            bonus_score += 0.003  # 0.3% bonus for education match
        
        final_score += bonus_score
        
        return round(final_score * 100, 3)  # Convert back to percentage with 3 decimal places for precision
    
    def _generate_candidate_summary(self, resume_data: Dict) -> Dict:
        """Generate a summary of candidate's key information."""
        skills = resume_data.get("skills", [])
        # Ensure skills is a list and filter out None/empty values
        if not isinstance(skills, list):
            skills = []
        skills = [skill for skill in skills if skill and isinstance(skill, str)]
        
        experience_data = resume_data.get("experience", [])
        education_data = resume_data.get("education", [])
        project_data = resume_data.get("projects", [])
        
        # Ensure all are lists
        experience_count = len(experience_data) if isinstance(experience_data, list) else 0
        education_count = len(education_data) if isinstance(education_data, list) else 0
        project_count = len(project_data) if isinstance(project_data, list) else 0
        
        return {
            "total_skills": len(skills),
            "top_skills": skills[:5] if len(skills) >= 5 else skills,
            "experience_entries": experience_count,
            "education_entries": education_count,
            "project_entries": project_count,
            "has_contact_info": bool(resume_data.get("contact_info", {}).get("email"))
        }
    
    def _summarize_jd(self, jd_data: Dict) -> Dict:
        """Generate a summary of job description requirements."""
        return {
            "required_skills_count": len(jd_data.get("required_skills", [])),
            "preferred_skills_count": len(jd_data.get("preferred_skills", [])),
            "top_required_skills": jd_data.get("required_skills", [])[:5],
            "experience_requirements": jd_data.get("experience_requirements", {}),
            "education_requirements": jd_data.get("education_requirements", {}),
            "role_info": jd_data.get("role_requirements", {})
        }
    
    def _generate_ranking_analysis(self, candidates: List[Dict], jd_data: Dict) -> Dict:
        """Generate overall analysis of the candidate pool."""
        if not candidates:
            return {"message": "No candidates to analyze"}
        
        scores = [c["final_ranking_score"] for c in candidates]
        
        analysis = {
            "candidate_pool_size": len(candidates),
            "score_statistics": {
                "highest_score": max(scores),
                "lowest_score": min(scores),
                "average_score": round(sum(scores) / len(scores), 2),
                "score_range": round(max(scores) - min(scores), 2)
            },
            "match_level_distribution": {},
            "top_candidates": candidates[:3] if len(candidates) >= 3 else candidates,
            "skill_gap_analysis": self._analyze_skill_gaps(candidates, jd_data),
            "recommendations": self._generate_pool_recommendations(candidates, jd_data)
        }
        
        # Calculate match level distribution
        for candidate in candidates:
            level = candidate["match_level"]
            analysis["match_level_distribution"][level] = analysis["match_level_distribution"].get(level, 0) + 1
        
        return analysis
    
    def _analyze_skill_gaps(self, candidates: List[Dict], jd_data: Dict) -> Dict:
        """Analyze common skill gaps across all candidates."""
        required_skills = jd_data.get("required_skills", [])
        
        skill_gap_count = {}
        for skill in required_skills:
            gap_count = 0
            for candidate in candidates:
                if skill not in candidate.get("skill_analysis", {}).get("required_matches", []):
                    gap_count += 1
            skill_gap_count[skill] = gap_count
        
        # Sort by most common gaps
        most_common_gaps = sorted(skill_gap_count.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "most_common_missing_skills": most_common_gaps[:5],
            "overall_skill_coverage": {
                skill: round((len(candidates) - gap_count) / len(candidates) * 100, 1)
                for skill, gap_count in skill_gap_count.items()
            }
        }
    
    def _generate_pool_recommendations(self, candidates: List[Dict], jd_data: Dict) -> List[str]:
        """Generate recommendations for the overall candidate pool."""
        recommendations = []
        
        if not candidates:
            return ["No candidates found to analyze"]
        
        scores = [c["final_ranking_score"] for c in candidates]
        avg_score = sum(scores) / len(scores)
        
        if avg_score < 60:
            recommendations.append("Consider expanding the candidate search or revising job requirements")
        
        if len([c for c in candidates if c["match_level"] in ["Excellent Match", "Good Match"]]) < 3:
            recommendations.append("Consider providing additional training for selected candidates")
        
        # Check for skill gaps
        required_skills = jd_data.get("required_skills", [])
        if required_skills:
            skill_coverage = {}
            for skill in required_skills:
                candidates_with_skill = sum(1 for c in candidates 
                                          if skill in c.get("skill_analysis", {}).get("required_matches", []))
                skill_coverage[skill] = candidates_with_skill / len(candidates)
            
            low_coverage_skills = [skill for skill, coverage in skill_coverage.items() if coverage < 0.3]
            if low_coverage_skills:
                recommendations.append(f"Consider training in: {', '.join(low_coverage_skills[:3])}")
        
        return recommendations
    
    def _save_ranking_results(self, results: Dict, output_file: str):
        """Save ranking results to a JSON file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving results: {str(e)}")
    
    def generate_ranking_report(self, ranking_results: Dict, output_file: str = None) -> str:
        """Generate a human-readable ranking report."""
        
        if not ranking_results.get("success"):
            return "Error: Invalid ranking results"
        
        candidates = ranking_results["candidates"]
        analysis = ranking_results["ranking_analysis"]
        
        report = []
        report.append("=" * 80)
        report.append("📊 CANDIDATE RANKING REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append(f"📋 Total Candidates Processed: {ranking_results['total_candidates']}")
        report.append(f"📈 Average Score: {analysis['score_statistics']['average_score']}%")
        report.append(f"🏆 Highest Score: {analysis['score_statistics']['highest_score']}%")
        report.append("")
        
        # Top candidates
        report.append("🥇 TOP CANDIDATES:")
        report.append("-" * 50)
        
        for i, candidate in enumerate(candidates[:5], 1):
            report.append(f"{i}. {candidate['candidate_name']} ({candidate['file_name']})")
            report.append(f"   📊 Score: {candidate['final_ranking_score']}% ({candidate['match_level']})")
            report.append(f"   📧 Email: {candidate.get('email', 'N/A')}")
            report.append(f"   🔗 LinkedIn: {candidate.get('linkedin', 'N/A')}")
            report.append(f"   💼 Skills: {', '.join(candidate['resume_summary']['top_skills'])}")
            report.append("")
        
        # Skill gap analysis
        if analysis.get("skill_gap_analysis"):
            report.append("🔍 SKILL GAP ANALYSIS:")
            report.append("-" * 50)
            for skill, gap_count in analysis["skill_gap_analysis"]["most_common_missing_skills"][:5]:
                missing_percentage = round(gap_count / ranking_results['total_candidates'] * 100, 1)
                report.append(f"• {skill}: Missing in {missing_percentage}% of candidates")
            report.append("")
        
        # Recommendations
        if analysis.get("recommendations"):
            report.append("💡 RECOMMENDATIONS:")
            report.append("-" * 50)
            for rec in analysis["recommendations"]:
                report.append(f"• {rec}")
            report.append("")
        
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save to file if requested
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                print(f"📄 Report saved to {output_file}")
            except Exception as e:
                print(f"Error saving report: {str(e)}")
        
        return report_text

# Main execution function
def rank_candidates_for_job(resume_folder: str, jd_text: str, output_dir: str = None) -> Dict:
    """
    Convenience function to rank all resumes in a folder against a job description.
    
    Args:
        resume_folder: Path to folder containing resume files
        jd_text: Job description text
        output_dir: Directory to save results (optional)
    
    Returns:
        Ranking results dictionary
    """
    
    # Find all resume files in the folder
    resume_files = []
    supported_extensions = ['.pdf', '.docx', '.txt']
    
    for filename in os.listdir(resume_folder):
        if any(filename.lower().endswith(ext) for ext in supported_extensions):
            resume_files.append(os.path.join(resume_folder, filename))
    
    if not resume_files:
        return {"error": "No supported resume files found in the specified folder"}
    
    print(f"Found {len(resume_files)} resume files")
    
    # Create ranker and process
    ranker = CandidateRanker()
    
    # Set output files
    json_output = os.path.join(output_dir, "ranking_results.json") if output_dir else None
    report_output = os.path.join(output_dir, "ranking_report.txt") if output_dir else None
    
    # Rank candidates
    results = ranker.rank_candidates(resume_files, jd_text, json_output)
    
    # Generate report
    if results.get("success"):
        report = ranker.generate_ranking_report(results, report_output)
        print("\n" + report)
    
    return results

# Test function
if __name__ == "__main__":
    # Test with sample data
    sample_jd = """
    Senior Software Engineer - Full Stack
    
    Required Skills:
    - 5+ years of Python development
    - React and JavaScript experience
    - SQL and database management
    - Git version control
    - API development experience
    
    Preferred Skills:
    - AWS cloud experience
    - Docker containerization
    - Agile methodology
    
    Education: Bachelor's degree in Computer Science or related field
    
    Experience: 5+ years in software development
    """
    
    print("--- Testing Candidate Ranker ---")
    print("Note: This test requires actual resume files to process")
    print("Sample JD parsed successfully for testing framework")
    
    # Test JD parsing
    from jd_processor import parse_job_description
    jd_result = parse_job_description(sample_jd)
    if jd_result.get("success"):
        print("✅ JD processing framework ready")
        print(f"Required skills: {jd_result['data']['required_skills']}")
        print(f"Preferred skills: {jd_result['data']['preferred_skills']}")
    else:
        print("❌ JD processing failed")
