#!/usr/bin/env python3
"""
ResumePard System Test - Comprehensive Demo
Demonstrates all features of the ResumePard matching system.
"""

import os
import json
from main_matcher import ResumePardMatcher

def create_sample_job_description():
    """Create a sample job description for testing."""
    return """
    Senior Python Developer - Remote Opportunity
    
    We are seeking an experienced Senior Python Developer to join our growing team. 
    
    Required Skills:
    - 5+ years of Python development experience
    - Strong knowledge of Django or Flask frameworks
    - Experience with SQL databases (PostgreSQL, MySQL)
    - RESTful API development and integration
    - Git version control
    - Agile/Scrum methodology experience
    
    Preferred Skills:
    - Machine Learning experience (scikit-learn, TensorFlow)
    - Docker and containerization
    - AWS cloud services
    - React.js or Vue.js frontend experience
    - CI/CD pipeline experience
    - Unit testing and TDD practices
    
    Education Requirements:
    - Bachelor's degree in Computer Science, Engineering, or related field
    - OR equivalent work experience
    
    Experience Requirements:
    - Minimum 5 years of professional software development
    - At least 3 years of Python-specific development
    - Experience leading technical projects
    - Previous work in fast-paced startup environment preferred
    
    Responsibilities:
    - Design and develop scalable web applications
    - Collaborate with cross-functional teams
    - Mentor junior developers
    - Participate in code reviews and technical discussions
    - Contribute to architectural decisions
    
    Benefits:
    - Competitive salary ($90,000 - $130,000)
    - Remote work flexibility
    - Health, dental, and vision insurance
    - 401(k) matching
    - Professional development budget
    """

def demo_single_resume_analysis():
    """Demonstrate single resume analysis."""
    print("🔍 DEMO: Single Resume Analysis")
    print("=" * 50)
    
    matcher = ResumePardMatcher()
    jd_text = create_sample_job_description()
    
    # Check if we have any resume files
    resume_files = []
    for filename in os.listdir("."):
        if filename.lower().endswith(('.pdf', '.docx', '.txt')):
            resume_files.append(filename)
    
    if not resume_files:
        print("❌ No resume files found in current directory")
        print("💡 Please add some resume files (.pdf, .docx, or .txt) to test")
        return False
    
    # Analyze the first resume found
    resume_file = resume_files[0]
    print(f"📄 Analyzing: {resume_file}")
    
    result = matcher.analyze_single_resume(resume_file, jd_text, save_result=True)
    
    if result.get("success"):
        match_summary = result["match_summary"]
        print(f"✅ Analysis completed successfully!")
        print(f"📊 Overall Score: {match_summary['overall_score']}%")
        print(f"🎯 Match Level: {match_summary['match_level']}")
        print(f"💪 Key Strengths: {', '.join(match_summary['key_strengths'])}")
        print(f"📈 Areas for Improvement: {len(match_summary['improvement_areas'])} identified")
        return True
    else:
        print(f"❌ Analysis failed: {result.get('error')}")
        return False

def demo_job_description_analysis():
    """Demonstrate job description analysis."""
    print("\n📋 DEMO: Job Description Analysis")
    print("=" * 50)
    
    matcher = ResumePardMatcher()
    jd_text = create_sample_job_description()
    
    result = matcher.analyze_job_description(jd_text, save_result=True)
    
    if result.get("success"):
        summary = result["requirements_summary"]
        print(f"✅ JD Analysis completed successfully!")
        print(f"🔧 Required Skills: {summary['total_required_skills']}")
        print(f"⭐ Preferred Skills: {summary['total_preferred_skills']}")
        print(f"📅 Experience Required: {summary.get('experience_requirements', {}).get('min_years', 'Not specified')}")
        print(f"🎓 Education Level: {summary.get('education_requirements', {}).get('degree_level', 'Not specified')}")
        
        insights = result.get("insights", [])
        if insights:
            print(f"💡 Insights: {insights[0]}")
        
        return True
    else:
        print(f"❌ JD Analysis failed: {result.get('error')}")
        return False

def demo_batch_processing():
    """Demonstrate batch resume processing."""
    print("\n🔄 DEMO: Batch Resume Processing")
    print("=" * 50)
    
    matcher = ResumePardMatcher()
    
    # Check for resume files in current directory
    resume_files = [f for f in os.listdir(".") if f.lower().endswith(('.pdf', '.docx', '.txt'))]
    
    if len(resume_files) < 1:
        print("❌ Need at least 1 resume file for batch processing demo")
        return False
    
    result = matcher.batch_process_resumes(".", "demo_batch_results")
    
    if result.get("success"):
        print(f"✅ Batch processing completed!")
        print(f"📁 Processed: {result['successfully_processed']}/{result['total_files']} files")
        
        if result.get("summary_stats"):
            stats = result["summary_stats"]
            print(f"📊 Average skills per resume: {stats['average_skills_per_resume']}")
            print(f"🎯 Total unique skills found: {stats['total_unique_skills']}")
            
            if stats.get("most_common_skills"):
                top_skill = stats["most_common_skills"][0]
                print(f"🏆 Most common skill: {top_skill[0]} ({top_skill[1]} candidates)")
        
        return True
    else:
        print(f"❌ Batch processing failed: {result.get('error')}")
        return False

def demo_candidate_ranking():
    """Demonstrate candidate ranking."""
    print("\n🏆 DEMO: Candidate Ranking")
    print("=" * 50)
    
    matcher = ResumePardMatcher()
    jd_text = create_sample_job_description()
    
    # Check for multiple resume files
    resume_files = [f for f in os.listdir(".") if f.lower().endswith(('.pdf', '.docx', '.txt'))]
    
    if len(resume_files) < 2:
        print("❌ Need at least 2 resume files for ranking demo")
        print("💡 Add more resume files to see ranking in action")
        return False
    
    result = matcher.rank_multiple_candidates(".", jd_text, "demo_ranking_results", min_score=0.0)
    
    if result.get("success"):
        candidates = result.get("candidates", [])
        print(f"✅ Ranking completed for {len(candidates)} candidates!")
        
        if candidates:
            print("\n🥇 TOP 3 CANDIDATES:")
            for i, candidate in enumerate(candidates[:3], 1):
                print(f"{i}. {candidate['candidate_name']}")
                print(f"   📊 Score: {candidate['final_ranking_score']}%")
                print(f"   🎯 Level: {candidate['match_level']}")
                print(f"   📄 File: {candidate['file_name']}")
                
                # Show top strengths
                if candidate.get('detailed_analysis', {}).get('skill_analysis', {}).get('required_matches'):
                    req_skills = len(candidate['detailed_analysis']['skill_analysis']['required_matches'])
                    print(f"   💪 Required skills: {req_skills}")
                print()
        
        return True
    else:
        print(f"❌ Ranking failed: {result.get('error')}")
        return False

def demo_system_capabilities():
    """Demonstrate the system's core capabilities."""
    print("🚀 ResumePard System Capabilities Demo")
    print("=" * 60)
    print("This demo will showcase all major features of ResumePard:")
    print("1. Job Description Analysis")
    print("2. Single Resume Analysis")
    print("3. Batch Resume Processing")
    print("4. Candidate Ranking")
    print()
    
    # Run all demos
    results = []
    
    results.append(demo_job_description_analysis())
    results.append(demo_single_resume_analysis())
    results.append(demo_batch_processing())
    results.append(demo_candidate_ranking())
    
    # Summary
    print("\n📈 DEMO SUMMARY")
    print("=" * 50)
    successful_demos = sum(results)
    total_demos = len(results)
    
    print(f"✅ Successful demos: {successful_demos}/{total_demos}")
    
    if successful_demos == total_demos:
        print("🎉 All demos completed successfully!")
        print("💡 ResumePard is ready for production use!")
    elif successful_demos > 0:
        print("⚠️  Some demos completed successfully.")
        print("💡 Add more resume files to test all features.")
    else:
        print("❌ No demos completed successfully.")
        print("💡 Please check your setup and add resume files.")
    
    print("\n📁 Generated Files:")
    generated_files = [
        "jd_analysis.json",
        "analysis_*.json",
        "demo_batch_results/",
        "demo_ranking_results/"
    ]
    
    for file_pattern in generated_files:
        if "*" not in file_pattern:
            if os.path.exists(file_pattern):
                print(f"  ✅ {file_pattern}")
            else:
                print(f"  ❌ {file_pattern}")
        else:
            # Check for wildcard patterns
            import glob
            matching_files = glob.glob(file_pattern)
            if matching_files:
                for file in matching_files:
                    print(f"  ✅ {file}")
            else:
                print(f"  ❌ {file_pattern}")

if __name__ == "__main__":
    try:
        demo_system_capabilities()
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        print("💡 Please check your setup and try again.")
    
    print("\n🔚 Demo completed. Thank you for trying ResumePard!")
