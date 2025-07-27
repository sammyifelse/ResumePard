#!/usr/bin/env python3
"""
ResumePard - Advanced Resume-Job Description Matching System
Main interface for comprehensive resume analysis and candidate ranking.
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Optional

# Import our modules
from info_extractor import parse_resume
from jd_processor import parse_job_description
from resume_matcher import match_resume_to_jd
from candidate_ranker import CandidateRanker, rank_candidates_for_job

class ResumePardMatcher:
    """
    Main interface for the ResumePard matching system.
    Provides unified access to all matching and ranking functionality.
    """
    
    def __init__(self):
        self.ranker = CandidateRanker()
        print("🚀 ResumePard Matcher initialized successfully!")
    
    def analyze_single_resume(self, resume_path: str, jd_text: str, save_result: bool = True) -> Dict:
        """
        Analyze a single resume against a job description.
        
        Args:
            resume_path: Path to the resume file
            jd_text: Job description text
            save_result: Whether to save results to JSON file
            
        Returns:
            Analysis results dictionary
        """
        
        print(f"📄 Analyzing resume: {os.path.basename(resume_path)}")
        
        try:
            # Match resume to JD
            result = match_resume_to_jd(resume_path, jd_text)
            
            if not result.get("success"):
                return result
            
            match_data = result["match_result"]
            
            # Enhanced result with additional information
            enhanced_result = {
                "analysis_type": "single_resume",
                "resume_file": os.path.basename(resume_path),
                "candidate_name": match_data["resume_data"].get("name", "Unknown"),
                "timestamp": self._get_timestamp(),
                "match_summary": {
                    "overall_score": match_data["overall_score"],
                    "match_level": match_data["match_level"],
                    "key_strengths": self._extract_strengths(match_data),
                    "improvement_areas": match_data["recommendations"]
                },
                "detailed_analysis": match_data,
                "success": True
            }
            
            # Save result if requested
            if save_result:
                output_file = f"analysis_{os.path.splitext(os.path.basename(resume_path))[0]}.json"
                self._save_json(enhanced_result, output_file)
                print(f"💾 Analysis saved to {output_file}")
            
            return enhanced_result
            
        except Exception as e:
            return {"success": False, "error": f"Analysis failed: {str(e)}"}
    
    def rank_multiple_candidates(self, 
                               resume_folder: str, 
                               jd_text: str, 
                               output_folder: str = "results",
                               min_score: float = 0.0) -> Dict:
        """
        Rank multiple candidates from a folder of resumes.
        
        Args:
            resume_folder: Path to folder containing resume files
            jd_text: Job description text
            output_folder: Folder to save results
            min_score: Minimum score threshold for inclusion
            
        Returns:
            Ranking results dictionary
        """
        
        print(f"🔍 Ranking candidates from folder: {resume_folder}")
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        try:
            # Rank candidates
            results = rank_candidates_for_job(resume_folder, jd_text, output_folder)
            
            if not results.get("success"):
                return results
            
            # Filter by minimum score if specified
            if min_score > 0:
                filtered_candidates = [
                    c for c in results["candidates"] 
                    if c["final_ranking_score"] >= min_score
                ]
                results["candidates"] = filtered_candidates
                results["filtered_by_min_score"] = min_score
                print(f"🎯 Filtered to {len(filtered_candidates)} candidates with score >= {min_score}%")
            
            # Generate summary report
            self._print_ranking_summary(results)
            
            return results
            
        except Exception as e:
            return {"success": False, "error": f"Ranking failed: {str(e)}"}
    
    def compare_candidates(self, resume_paths: List[str], jd_text: str) -> Dict:
        """
        Compare specific candidates against each other and the JD.
        
        Args:
            resume_paths: List of paths to resume files
            jd_text: Job description text
            
        Returns:
            Comparison results dictionary
        """
        
        print(f"⚖️ Comparing {len(resume_paths)} candidates...")
        
        candidates_analysis = []
        
        for resume_path in resume_paths:
            result = self.analyze_single_resume(resume_path, jd_text, save_result=False)
            if result.get("success"):
                candidates_analysis.append(result)
            else:
                print(f"❌ Failed to analyze {resume_path}: {result.get('error')}")
        
        if not candidates_analysis:
            return {"success": False, "error": "No candidates could be analyzed"}
        
        # Sort by score
        candidates_analysis.sort(key=lambda x: x["match_summary"]["overall_score"], reverse=True)
        
        # Generate comparison insights
        comparison = {
            "success": True,
            "comparison_type": "direct_comparison",
            "total_candidates": len(candidates_analysis),
            "timestamp": self._get_timestamp(),
            "candidates": candidates_analysis,
            "comparison_insights": self._generate_comparison_insights(candidates_analysis),
            "winner": candidates_analysis[0] if candidates_analysis else None
        }
        
        return comparison
    
    def analyze_job_description(self, jd_text: str, save_result: bool = True) -> Dict:
        """
        Analyze a job description to extract requirements and insights.
        
        Args:
            jd_text: Job description text
            save_result: Whether to save results to JSON file
            
        Returns:
            JD analysis results
        """
        
        print("📋 Analyzing job description...")
        
        try:
            jd_result = parse_job_description(jd_text)
            
            if not jd_result.get("success"):
                return jd_result
            
            jd_data = jd_result["data"]
            
            # Enhanced JD analysis
            enhanced_analysis = {
                "analysis_type": "job_description",
                "timestamp": self._get_timestamp(),
                "requirements_summary": {
                    "total_required_skills": len(jd_data.get("required_skills", [])),
                    "total_preferred_skills": len(jd_data.get("preferred_skills", [])),
                    "experience_requirements": jd_data.get("experience_requirements", {}),
                    "education_requirements": jd_data.get("education_requirements", {})
                },
                "detailed_requirements": jd_data,
                "insights": self._generate_jd_insights(jd_data),
                "success": True
            }
            
            # Save result if requested
            if save_result:
                output_file = "jd_analysis.json"
                self._save_json(enhanced_analysis, output_file)
                print(f"💾 JD analysis saved to {output_file}")
            
            return enhanced_analysis
            
        except Exception as e:
            return {"success": False, "error": f"JD analysis failed: {str(e)}"}
    
    def batch_process_resumes(self, resume_folder: str, output_folder: str = "batch_results") -> Dict:
        """
        Process multiple resumes to extract information without JD matching.
        
        Args:
            resume_folder: Path to folder containing resume files
            output_folder: Folder to save results
            
        Returns:
            Batch processing results
        """
        
        print(f"🔄 Batch processing resumes from: {resume_folder}")
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Find resume files
        resume_files = []
        supported_extensions = ['.pdf', '.docx', '.txt']
        
        for filename in os.listdir(resume_folder):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                resume_files.append(os.path.join(resume_folder, filename))
        
        if not resume_files:
            return {"success": False, "error": "No supported resume files found"}
        
        processed_resumes = []
        errors = []
        
        for resume_file in resume_files:
            try:
                print(f"📄 Processing: {os.path.basename(resume_file)}")
                resume_data = parse_resume(resume_file)
                
                if "error" not in resume_data:
                    processed_data = {
                        "file_name": os.path.basename(resume_file),
                        "candidate_name": resume_data.get("name", "Unknown"),
                        "contact_info": resume_data.get("contact_info", {}),
                        "skills_count": len(resume_data.get("skills", [])),
                        "skills": resume_data.get("skills", []),
                        "experience_count": len(resume_data.get("experience", [])),
                        "education_count": len(resume_data.get("education", [])),
                        "projects_count": len(resume_data.get("projects", [])),
                        "full_data": resume_data
                    }
                    processed_resumes.append(processed_data)
                    
                    # Save individual resume data
                    individual_file = os.path.join(output_folder, f"parsed_{os.path.splitext(os.path.basename(resume_file))[0]}.json")
                    self._save_json(resume_data, individual_file)
                    
                else:
                    errors.append({"file": resume_file, "error": resume_data["error"]})
                    
            except Exception as e:
                errors.append({"file": resume_file, "error": str(e)})
        
        # Generate summary
        batch_results = {
            "success": True,
            "processing_type": "batch_resume_extraction",
            "timestamp": self._get_timestamp(),
            "total_files": len(resume_files),
            "successfully_processed": len(processed_resumes),
            "errors": len(errors),
            "resumes": processed_resumes,
            "error_details": errors if errors else None,
            "summary_stats": self._generate_batch_stats(processed_resumes)
        }
        
        # Save batch summary
        summary_file = os.path.join(output_folder, "batch_summary.json")
        self._save_json(batch_results, summary_file)
        print(f"📊 Batch summary saved to {summary_file}")
        
        return batch_results
    
    # Helper methods
    def _extract_strengths(self, match_data: Dict) -> List[str]:
        """Extract key strengths from match analysis."""
        strengths = []
        
        skill_analysis = match_data.get("skill_analysis", {})
        if skill_analysis.get("required_matches"):
            strengths.append(f"Has {len(skill_analysis['required_matches'])} required skills")
        
        if skill_analysis.get("preferred_matches"):
            strengths.append(f"Has {len(skill_analysis['preferred_matches'])} preferred skills")
        
        exp_analysis = match_data.get("experience_analysis", {})
        if exp_analysis.get("meets_year_requirement"):
            strengths.append("Meets experience requirements")
        
        edu_analysis = match_data.get("education_analysis", {})
        if edu_analysis.get("degree_match"):
            strengths.append("Has relevant education background")
        
        return strengths[:3]  # Top 3 strengths
    
    def _generate_comparison_insights(self, candidates: List[Dict]) -> Dict:
        """Generate insights from candidate comparison."""
        scores = [c["match_summary"]["overall_score"] for c in candidates]
        
        return {
            "score_spread": round(max(scores) - min(scores), 2),
            "average_score": round(sum(scores) / len(scores), 2),
            "top_performer": candidates[0]["candidate_name"] if candidates else None,
            "close_competition": max(scores) - scores[1] < 10 if len(scores) > 1 else False,
            "standout_winner": max(scores) - scores[1] > 20 if len(scores) > 1 else False
        }
    
    def _generate_jd_insights(self, jd_data: Dict) -> List[str]:
        """Generate insights about the job description."""
        insights = []
        
        required_skills = jd_data.get("required_skills", [])
        preferred_skills = jd_data.get("preferred_skills", [])
        
        if len(required_skills) > 10:
            insights.append("High number of required skills - consider prioritizing the most critical ones")
        
        if len(preferred_skills) > len(required_skills):
            insights.append("More preferred than required skills - good balance for attracting diverse candidates")
        
        exp_reqs = jd_data.get("experience_requirements", {}).get("years_required", [])
        if exp_reqs:
            min_years = min([req.get("min_years", 0) for req in exp_reqs if req.get("min_years")])
            if min_years > 7:
                insights.append("High experience requirement may limit candidate pool")
        
        return insights
    
    def _generate_batch_stats(self, resumes: List[Dict]) -> Dict:
        """Generate statistics from batch processing."""
        if not resumes:
            return {}
        
        total_skills = sum(r["skills_count"] for r in resumes)
        avg_skills = round(total_skills / len(resumes), 1)
        
        # Most common skills
        all_skills = []
        for resume in resumes:
            all_skills.extend(resume["skills"])
        
        skill_count = {}
        for skill in all_skills:
            skill_count[skill] = skill_count.get(skill, 0) + 1
        
        top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "average_skills_per_resume": avg_skills,
            "total_unique_skills": len(skill_count),
            "most_common_skills": top_skills,
            "candidates_with_contact_info": sum(1 for r in resumes if r["full_data"].get("contact_info", {}).get("email"))
        }
    
    def _print_ranking_summary(self, results: Dict):
        """Print a summary of ranking results."""
        candidates = results.get("candidates", [])
        if not candidates:
            print("No candidates found")
            return
        
        print("\n🏆 RANKING SUMMARY:")
        print("=" * 50)
        
        for i, candidate in enumerate(candidates[:5], 1):
            print(f"{i}. {candidate['candidate_name']}")
            print(f"   Score: {candidate['final_ranking_score']}% ({candidate['match_level']})")
            print(f"   File: {candidate['file_name']}")
            print()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _save_json(self, data: Dict, filename: str):
        """Save data to JSON file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving {filename}: {str(e)}")

def main():
    """Command-line interface for ResumePard."""
    parser = argparse.ArgumentParser(description="ResumePard - Advanced Resume-JD Matching System")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single resume analysis
    single_parser = subparsers.add_parser('analyze', help='Analyze single resume against JD')
    single_parser.add_argument('resume', help='Path to resume file')
    single_parser.add_argument('jd', help='Job description text or file path')
    single_parser.add_argument('--save', action='store_true', help='Save results to file')
    
    # Multiple candidate ranking
    rank_parser = subparsers.add_parser('rank', help='Rank multiple candidates')
    rank_parser.add_argument('folder', help='Folder containing resume files')
    rank_parser.add_argument('jd', help='Job description text or file path')
    rank_parser.add_argument('--output', default='results', help='Output folder for results')
    rank_parser.add_argument('--min-score', type=float, default=0.0, help='Minimum score threshold')
    
    # Batch processing
    batch_parser = subparsers.add_parser('batch', help='Batch process resumes')
    batch_parser.add_argument('folder', help='Folder containing resume files')
    batch_parser.add_argument('--output', default='batch_results', help='Output folder')
    
    # JD analysis
    jd_parser = subparsers.add_parser('analyze-jd', help='Analyze job description')
    jd_parser.add_argument('jd', help='Job description text or file path')
    jd_parser.add_argument('--save', action='store_true', help='Save results to file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize matcher
    matcher = ResumePardMatcher()
    
    # Helper function to read JD
    def read_jd(jd_input):
        if os.path.isfile(jd_input):
            with open(jd_input, 'r', encoding='utf-8') as f:
                return f.read()
        return jd_input
    
    # Execute commands
    try:
        if args.command == 'analyze':
            jd_text = read_jd(args.jd)
            result = matcher.analyze_single_resume(args.resume, jd_text, args.save)
            print(json.dumps(result, indent=2))
            
        elif args.command == 'rank':
            jd_text = read_jd(args.jd)
            result = matcher.rank_multiple_candidates(args.folder, jd_text, args.output, args.min_score)
            if result.get("success"):
                print(f"✅ Successfully ranked {result['total_candidates']} candidates")
            else:
                print(f"❌ Error: {result.get('error')}")
                
        elif args.command == 'batch':
            result = matcher.batch_process_resumes(args.folder, args.output)
            if result.get("success"):
                print(f"✅ Successfully processed {result['successfully_processed']}/{result['total_files']} resumes")
            else:
                print(f"❌ Error: {result.get('error')}")
                
        elif args.command == 'analyze-jd':
            jd_text = read_jd(args.jd)
            result = matcher.analyze_job_description(jd_text, args.save)
            print(json.dumps(result, indent=2))
            
    except Exception as e:
        print(f"❌ Command failed: {str(e)}")

if __name__ == "__main__":
    main()
