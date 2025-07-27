#!/usr/bin/env python3
"""
ResumePard Streamlit Web Application
Advanced AI-Powered Resume-Job Description Matching System
"""

import streamlit as st
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import tempfile
import shutil
from typing import List, Dict, Optional

# Import our ResumePard modules
from text_extractor import extract_text
from info_extractor import parse_resume
from jd_processor import parse_job_description
from resume_matcher import match_resume_to_jd
from candidate_ranker import CandidateRanker, rank_candidates_for_job
from main_matcher import ResumePardMatcher

# Helper functions to handle None data gracefully
def safe_get(data, *keys, default=None):
    """Safely get nested dictionary values without throwing NoneType errors."""
    try:
        result = data
        for key in keys:
            if result is None:
                return default
            if isinstance(result, dict):
                result = result.get(key)
            elif isinstance(result, list) and isinstance(key, int) and 0 <= key < len(result):
                result = result[key]
            else:
                return default
        return result if result is not None else default
    except (TypeError, KeyError, IndexError):
        return default

def safe_candidate_data(candidate):
    """Ensure candidate data has all required fields with safe defaults."""
    if not candidate:
        return {
            'rank': 0,
            'file_name': 'Unknown',
            'candidate_name': 'Unknown Candidate',
            'email': 'No email provided',
            'phone': 'No phone provided',
            'linkedin': 'No LinkedIn provided',
            'final_ranking_score': 0.0,
            'match_level': 'Unknown',
            'skill_analysis': {},
            'experience_analysis': {},
            'education_analysis': {},
            'project_analysis': {},
            'additional_scores': {},
            'recommendations': [],
            'resume_summary': {
                'total_skills': 0,
                'top_skills': [],
                'experience_entries': 0,
                'education_entries': 0,
                'project_entries': 0,
                'has_contact_info': False
            }
        }
    
    # Check if candidate has detailed_analysis structure or direct fields
    detailed_analysis = safe_get(candidate, 'detailed_analysis', default={})
    
    # Extract analysis data from either detailed_analysis or direct fields
    skill_analysis = safe_get(candidate, 'skill_analysis', default={})
    if not skill_analysis and detailed_analysis:
        skill_analysis = safe_get(detailed_analysis, 'skill_analysis', default={})
    
    experience_analysis = safe_get(candidate, 'experience_analysis', default={})
    if not experience_analysis and detailed_analysis:
        experience_analysis = safe_get(detailed_analysis, 'experience_analysis', default={})
    
    education_analysis = safe_get(candidate, 'education_analysis', default={})
    if not education_analysis and detailed_analysis:
        education_analysis = safe_get(detailed_analysis, 'education_analysis', default={})
    
    project_analysis = safe_get(candidate, 'project_analysis', default={})
    if not project_analysis and detailed_analysis:
        project_analysis = safe_get(detailed_analysis, 'project_analysis', default={})
    
    # Handle recommendations from either location
    recommendations = safe_get(candidate, 'recommendations', default=[])
    if not recommendations and detailed_analysis:
        recommendations = safe_get(detailed_analysis, 'recommendations', default=[])

    return {
        'rank': safe_get(candidate, 'rank', default=0),
        'file_name': safe_get(candidate, 'file_name', default='Unknown'),
        'candidate_name': safe_get(candidate, 'candidate_name', default='Unknown Candidate'),
        'email': safe_get(candidate, 'email', default='No email provided'),
        'phone': safe_get(candidate, 'phone', default='No phone provided'),
        'linkedin': safe_get(candidate, 'linkedin', default='No LinkedIn provided'),
        'final_ranking_score': safe_get(candidate, 'final_ranking_score', default=0.0),
        'match_level': safe_get(candidate, 'match_level', default='Unknown'),
        'skill_analysis': skill_analysis,
        'experience_analysis': experience_analysis,
        'education_analysis': education_analysis,
        'project_analysis': project_analysis,
        'additional_scores': safe_get(candidate, 'additional_scores', default={}),
        'recommendations': recommendations,
        'resume_summary': safe_get(candidate, 'resume_summary', default={
            'total_skills': 0,
            'top_skills': [],
            'experience_entries': 0,
            'education_entries': 0,
            'project_entries': 0,
            'has_contact_info': False
        })
    }

# Configure Streamlit page
st.set_page_config(
    page_title="ResumePard - AI Resume Matcher",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .candidate-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #28a745;
    }
    .poor-match {
        border-left-color: #dc3545 !important;
    }
    .fair-match {
        border-left-color: #ffc107 !important;
    }
    .good-match {
        border-left-color: #17a2b8 !important;
    }
    .excellent-match {
        border-left-color: #28a745 !important;
    }
    .stProgress .st-bo {
        background-color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_jd' not in st.session_state:
    st.session_state.processed_jd = None
if 'parsed_resumes' not in st.session_state:
    st.session_state.parsed_resumes = []
if 'ranking_results' not in st.session_state:
    st.session_state.ranking_results = None
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = None

def create_temp_directory():
    """Create a temporary directory for file processing."""
    if st.session_state.temp_dir is None:
        st.session_state.temp_dir = tempfile.mkdtemp()
    return st.session_state.temp_dir

def cleanup_temp_directory():
    """Clean up temporary directory."""
    if st.session_state.temp_dir and os.path.exists(st.session_state.temp_dir):
        shutil.rmtree(st.session_state.temp_dir)
        st.session_state.temp_dir = None

def display_jd_analysis(jd_data):
    """Display job description analysis results."""
    if not jd_data or not jd_data.get('success'):
        st.error("Failed to process job description")
        return
    
    data = jd_data['data']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Required Skills", len(data.get('required_skills', [])))
    with col2:
        st.metric("Preferred Skills", len(data.get('preferred_skills', [])))
    with col3:
        exp_reqs = data.get('experience_requirements', {}).get('years_required', [])
        min_years = min([req.get('min_years', 0) for req in exp_reqs]) if exp_reqs else 0
        st.metric("Min Experience", f"{min_years} years")
    with col4:
        st.metric("Priority Level", data.get('priority_requirements', {}).get('high', 0))
    
    # Display skills in expandable sections
    with st.expander("📋 Required Skills", expanded=True):
        if data.get('required_skills'):
            st.write(", ".join(data['required_skills']))
        else:
            st.info("No specific required skills identified")
    
    with st.expander("⭐ Preferred Skills"):
        if data.get('preferred_skills'):
            st.write(", ".join(data['preferred_skills']))
        else:
            st.info("No preferred skills identified")
    
    with st.expander("🎓 Education & Experience Requirements"):
        edu_reqs = data.get('education_requirements', {})
        if edu_reqs.get('degree_requirements'):
            st.write("**Education:** " + ", ".join(edu_reqs['degree_requirements']))
        
        exp_reqs = data.get('experience_requirements', {})
        if exp_reqs.get('years_required'):
            st.write("**Experience Requirements:**")
            for req in exp_reqs['years_required']:
                min_years = req.get('min_years', 0)
                max_years = req.get('max_years', 'N/A')
                req_type = req.get('type', 'general')
                st.write(f"- {req_type.title()}: {min_years}-{max_years} years")

def display_candidate_card(candidate, rank):
    """Display individual candidate card with styling based on match level."""
    # Use safe data handling
    safe_candidate = safe_candidate_data(candidate)
    
    match_level = safe_candidate['match_level']
    score = safe_candidate['final_ranking_score']
    
    # Determine card class based on match level
    if match_level == "Excellent Match":
        card_class = "excellent-match"
    elif match_level == "Good Match":
        card_class = "good-match"
    elif match_level == "Fair Match" or match_level == "Moderate Match":
        card_class = "fair-match"
    else:
        card_class = "poor-match"
    
    with st.container():
        st.markdown(f"""
        <div class="candidate-card {card_class}">
            <h4>#{rank} {safe_candidate['candidate_name']}</h4>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>Score: {score:.1f}%</strong> ({match_level})
                </div>
                <div style="text-align: right; font-size: 0.9em; color: #666;">
                    📄 {safe_candidate['file_name']}<br>
                    📧 {safe_candidate['email']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Detailed analysis in expandable section
        with st.expander(f"🔍 Detailed Analysis - {safe_candidate['candidate_name']}"):
            # Use safe data from the safe candidate object
            skill_analysis = safe_candidate['skill_analysis']
            experience_analysis = safe_candidate['experience_analysis']
            education_analysis = safe_candidate['education_analysis']
            project_analysis = safe_candidate['project_analysis']
            additional_scores = safe_candidate['additional_scores']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Scores Breakdown")
                st.write(f"**Required Skills Match:** {safe_get(skill_analysis, 'required_score', default=0)*100:.1f}%")
                st.write(f"**Preferred Skills Match:** {safe_get(skill_analysis, 'preferred_score', default=0)*100:.1f}%")
                
                st.write(f"**Experience Match:** {'✅' if safe_get(experience_analysis, 'meets_year_requirement', default=False) else '❌'}")
                st.write(f"**Education Match:** {'✅' if safe_get(education_analysis, 'degree_match', default=False) else '❌'}")
                
                # Additional scores
                if additional_scores:
                    st.write("**Additional Metrics:**")
                    st.write(f"- Skill Diversity: {safe_get(additional_scores, 'skill_diversity', default=0)*100:.1f}%")
                    st.write(f"- Experience Quality: {safe_get(additional_scores, 'experience_quality', default=0)*100:.1f}%")
                    st.write(f"- Education Level: {safe_get(additional_scores, 'education_level', default=0)*100:.1f}%")
                    st.write(f"- Project Relevance: {safe_get(additional_scores, 'project_relevance', default=0)*100:.1f}%")
            
            with col2:
                st.subheader("💪 Strengths & Gaps")
                
                # Required skills matches
                required_matches = safe_get(skill_analysis, 'required_matches', default=[])
                if required_matches:
                    st.write("**✅ Required Skills Found:**")
                    st.success(", ".join(required_matches[:5]))
                
                # Preferred skills matches  
                preferred_matches = safe_get(skill_analysis, 'preferred_matches', default=[])
                if preferred_matches:
                    st.write("**⭐ Preferred Skills Found:**")
                    st.info(", ".join(preferred_matches[:5]))
                
                # Missing required skills
                missing_required = safe_get(skill_analysis, 'missing_required', default=[])
                if missing_required:
                    st.write("**❌ Missing Required Skills:**")
                    st.error(", ".join(missing_required[:5]))
                
                # Technology experience
                tech_matches = safe_get(experience_analysis, 'technology_matches', default=[])
                if tech_matches:
                    st.write("**🔧 Technology Experience:**")
                    st.success(", ".join(tech_matches[:3]))
            
            # Recommendations
            recommendations = safe_candidate['recommendations']
            if recommendations:
                st.subheader("💡 Recommendations")
                for rec in recommendations[:3]:
                    st.write(f"• {rec}")
            
            # Project analysis
            skill_mentions = safe_get(project_analysis, 'skill_mentions', default=[])
            if skill_mentions:
                st.subheader("🚀 Project Skills")
                st.write("Skills mentioned in projects:")
                st.info(", ".join(skill_mentions[:5]))
            
            # Contact information
            if safe_candidate['phone'] != 'No phone provided' or safe_candidate['linkedin'] != 'No LinkedIn provided':
                st.subheader("📞 Contact Information")
                if safe_candidate['phone'] != 'No phone provided':
                    st.write(f"📱 {safe_candidate['phone']}")
                if safe_candidate['linkedin'] != 'No LinkedIn provided':
                    st.write(f"🔗 {safe_candidate['linkedin']}")

def create_ranking_visualizations(results):
    """Create interactive visualizations for ranking results."""
    if not results or not results.get('candidates'):
        st.info("📊 No data available for visualization")
        return
    
    candidates = results['candidates']
    
    # Prepare data for visualization with safe navigation
    visualization_data = []
    for c in candidates:
        # Safe navigation for nested data - use direct fields from candidate ranking
        skill_analysis = c.get('skill_analysis', {})
        
        required_matches = []
        missing_required = []
        
        if skill_analysis and isinstance(skill_analysis, dict):
            required_matches = skill_analysis.get('required_matches', [])
            missing_required = skill_analysis.get('missing_required', [])
            
        # Ensure lists are actually lists
        if not isinstance(required_matches, list):
            required_matches = []
        if not isinstance(missing_required, list):
            missing_required = []
            
        visualization_data.append({
            'Name': c.get('candidate_name', 'Unknown')[:20],
            'Score': c.get('final_ranking_score', 0),
            'Match Level': c.get('match_level', 'Poor Match'),
            'File': c.get('file_name', 'Unknown'),
            'Required Skills': len(required_matches),
            'Missing Skills': len(missing_required)
        })
    
    df = pd.DataFrame(visualization_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Score distribution bar chart
        fig_bar = px.bar(
            df.head(10), 
            x='Name', 
            y='Score',
            color='Match Level',
            title="🏆 Top 10 Candidates by Score",
            color_discrete_map={
                'Excellent Match': '#28a745',
                'Good Match': '#17a2b8', 
                'Moderate Match': '#ffc107',
                'Fair Match': '#fd7e14',
                'Poor Match': '#dc3545'
            }
        )
        fig_bar.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col2:
        # Match level distribution pie chart
        match_dist = df['Match Level'].value_counts()
        fig_pie = px.pie(
            values=match_dist.values,
            names=match_dist.index,
            title="📊 Match Level Distribution",
            color_discrete_map={
                'Excellent Match': '#28a745',
                'Good Match': '#17a2b8',
                'Moderate Match': '#ffc107', 
                'Fair Match': '#fd7e14',
                'Poor Match': '#dc3545'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Skills analysis
    if len(candidates) > 0:
        st.subheader("🎯 Skills Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            fig_skills = px.scatter(
                df, 
                x='Required Skills', 
                y='Score',
                color='Match Level',
                title="Skills vs Score Correlation",
                hover_data=['Name', 'File']
            )
            st.plotly_chart(fig_skills, use_container_width=True)
        
        with col2:
            # Top skills gap analysis
            all_missing = []
            for c in candidates:
                skill_analysis = c.get('skill_analysis', {})
                if skill_analysis and isinstance(skill_analysis, dict):
                    missing = skill_analysis.get('missing_required', [])
                    if isinstance(missing, list):
                        all_missing.extend(missing)
            
            if all_missing:
                missing_counts = pd.Series(all_missing).value_counts().head(10)
                fig_gaps = px.bar(
                    x=missing_counts.values,
                    y=missing_counts.index,
                    orientation='h',
                    title="🔍 Most Common Skill Gaps",
                    labels={'x': 'Number of Candidates Missing', 'y': 'Skills'}
                )
                st.plotly_chart(fig_gaps, use_container_width=True)
            else:
                st.info("📊 No skill gap data available")

def main():
    """Main Streamlit application."""
    
    def _calculate_basic_score(resume_data, jd_data):
        """Calculate a basic score when advanced matching fails."""
        score = 0
        
        # Score based on skills
        resume_skills = [skill.lower() for skill in resume_data.get('skills', [])]
        required_skills = [skill.lower() for skill in jd_data.get('required_skills', [])]
        preferred_skills = [skill.lower() for skill in jd_data.get('preferred_skills', [])]
        
        # Required skills matching (50% weight)
        if required_skills:
            required_matches = len([skill for skill in required_skills if skill in resume_skills])
            score += (required_matches / len(required_skills)) * 50
        
        # Preferred skills matching (20% weight)
        if preferred_skills:
            preferred_matches = len([skill for skill in preferred_skills if skill in resume_skills])
            score += (preferred_matches / len(preferred_skills)) * 20
        
        # Basic scoring for having any content (30% weight)
        if resume_data.get('name'):
            score += 5
        if resume_data.get('contact_info', {}).get('email'):
            score += 5
        if resume_data.get('experience'):
            score += 10
        if resume_data.get('education'):
            score += 5
        if resume_data.get('skills'):
            score += 5
        
        return round(min(score, 100), 1)
    
    def _get_match_level(score):
        """Determine match level based on score."""
        if score >= 80:
            return "Excellent Match"
        elif score >= 60:
            return "Good Match" 
        elif score >= 40:
            return "Moderate Match"
        elif score >= 20:
            return "Fair Match"
        else:
            return "Poor Match"
    
    def _create_basic_analysis(resume_data, jd_data, score):
        """Create basic analysis when advanced matching fails."""
        resume_skills = [skill.lower() for skill in resume_data.get('skills', [])]
        required_skills = [skill.lower() for skill in jd_data.get('required_skills', [])]
        preferred_skills = [skill.lower() for skill in jd_data.get('preferred_skills', [])]
        
        required_matches = [skill for skill in required_skills if skill in resume_skills]
        preferred_matches = [skill for skill in preferred_skills if skill in resume_skills]
        missing_required = [skill for skill in required_skills if skill not in resume_skills]
        
        return {
            'overall_score': score,
            'match_level': _get_match_level(score),
            'skill_analysis': {
                'required_score': len(required_matches) / len(required_skills) if required_skills else 0,
                'preferred_score': len(preferred_matches) / len(preferred_skills) if preferred_skills else 0,
                'required_matches': required_matches,
                'preferred_matches': preferred_matches,
                'missing_required': missing_required
            },
            'experience_analysis': {
                'meets_year_requirement': len(resume_data.get('experience', [])) > 0
            },
            'education_analysis': {
                'degree_match': len(resume_data.get('education', [])) > 0
            },
            'project_analysis': {
                'relevant_projects': len(resume_data.get('projects', []))
            },
            'recommendations': [
                "Basic scoring used - advanced analysis not available"
            ]
        }
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🚀 ResumePard - AI-Powered Resume Matcher</h1>
        <p>Upload job descriptions and resumes to find the perfect candidate matches using advanced NLP</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Scoring weights
        st.subheader("🎯 Scoring Weights")
        skills_weight = st.slider("Skills Weight", 0.0, 1.0, 0.4, 0.1)
        experience_weight = st.slider("Experience Weight", 0.0, 1.0, 0.3, 0.1)
        education_weight = st.slider("Education Weight", 0.0, 1.0, 0.2, 0.1)
        projects_weight = st.slider("Projects Weight", 0.0, 1.0, 0.1, 0.1)
        
        # Filtering options
        st.subheader("🔍 Filtering")
        min_score_threshold = st.slider("Minimum Score Threshold", 0, 100, 0, 5)
        max_candidates_display = st.slider("Max Candidates to Display", 5, 50, 10, 5)
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            save_results = st.checkbox("Save Results to Files", True)
            show_detailed_analysis = st.checkbox("Show Detailed Analysis", True)
            auto_refresh = st.checkbox("Auto-refresh Results", False)
        
        # Clear session button
        if st.button("🗑️ Clear All Data"):
            st.session_state.processed_jd = None
            st.session_state.parsed_resumes = []
            st.session_state.ranking_results = None
            cleanup_temp_directory()
            st.success("All data cleared!")
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Job Description", "📄 Resume Upload", "🏆 Ranking Results", "📊 Analytics"])
    
    with tab1:
        st.header("1️⃣ Job Description Analysis")
        
        # Job description input methods
        jd_input_method = st.radio(
            "How would you like to provide the Job Description?",
            ("📝 Paste Text", "📁 Upload File"),
            horizontal=True
        )
        
        jd_text = ""
        
        if jd_input_method == "📝 Paste Text":
            jd_text = st.text_area(
                "Paste Job Description here:",
                height=300,
                placeholder="Senior Python Developer required for cloud-based applications...\n\nRequired Skills:\n- Python (5+ years)\n- Django/Flask\n- AWS/Cloud platforms\n- SQL databases\n\nPreferred Skills:\n- Docker\n- Kubernetes\n- React\n\nExperience: 5+ years in software development..."
            )
        
        elif jd_input_method == "📁 Upload File":
            jd_file = st.file_uploader(
                "Upload Job Description File",
                type=["txt", "pdf", "docx"],
                help="Supported formats: TXT, PDF, DOCX"
            )
            
            if jd_file:
                temp_dir = create_temp_directory()
                jd_temp_path = os.path.join(temp_dir, jd_file.name)
                
                with open(jd_temp_path, "wb") as f:
                    f.write(jd_file.getbuffer())
                
                with st.spinner("Extracting text from uploaded file..."):
                    jd_text = extract_text(jd_temp_path)
                
                if jd_text:
                    st.success(f"✅ Successfully extracted text from {jd_file.name}")
                    with st.expander("📄 Extracted Text Preview"):
                        st.text(jd_text[:500] + "..." if len(jd_text) > 500 else jd_text)
                else:
                    st.error("❌ Could not extract text from the uploaded file")
        
        # Process job description
        if jd_text:
            if st.button("🔍 Analyze Job Description", type="primary"):
                with st.spinner("Analyzing job description..."):
                    jd_result = parse_job_description(jd_text)
                    st.session_state.processed_jd = jd_result
                
                if jd_result.get('success'):
                    st.success("✅ Job description analyzed successfully!")
                    display_jd_analysis(jd_result)
                else:
                    st.error(f"❌ Failed to analyze job description: {jd_result.get('error')}")
        
        # Display existing JD analysis
        elif st.session_state.processed_jd:
            st.info("📋 Using previously analyzed job description")
            display_jd_analysis(st.session_state.processed_jd)
    
    with tab2:
        st.header("2️⃣ Resume Upload & Processing")
        
        # Resume upload
        uploaded_resumes = st.file_uploader(
            "Choose resume files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="You can upload multiple resume files. Supported formats: PDF, DOCX, TXT"
        )
        
        if uploaded_resumes:
            st.info(f"📁 {len(uploaded_resumes)} file(s) selected for processing")
            
            if st.button("🚀 Process Resumes", type="primary"):
                temp_dir = create_temp_directory()
                parsed_resumes = []
                
                # Create progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, resume_file in enumerate(uploaded_resumes):
                    status_text.text(f"Processing {resume_file.name}...")
                    
                    # Save file temporarily
                    temp_resume_path = os.path.join(temp_dir, resume_file.name)
                    with open(temp_resume_path, "wb") as f:
                        f.write(resume_file.getbuffer())
                    
                    # Parse resume
                    try:
                        parsed_data = parse_resume(temp_resume_path)
                        parsed_data['file_name'] = resume_file.name
                        parsed_data['upload_time'] = datetime.now().isoformat()
                        parsed_resumes.append(parsed_data)
                    except Exception as e:
                        st.error(f"❌ Failed to process {resume_file.name}: {str(e)}")
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(uploaded_resumes))
                
                status_text.text("✅ Processing complete!")
                st.session_state.parsed_resumes = parsed_resumes
                st.success(f"🎉 Successfully processed {len(parsed_resumes)} out of {len(uploaded_resumes)} resumes!")
        
        # Display processed resumes summary
        if st.session_state.parsed_resumes:
            st.subheader("📋 Processed Resumes Summary")
            
            # Create summary dataframe
            summary_data = []
            for resume in st.session_state.parsed_resumes:
                summary_data.append({
                    'File Name': resume.get('file_name', 'Unknown'),
                    'Candidate Name': resume.get('name', 'Not extracted'),
                    'Email': resume.get('contact_info', {}).get('email', 'Not found'),
                    'Skills Count': len(resume.get('skills', [])),
                    'Experience Count': len(resume.get('experience', [])),
                    'Education Count': len(resume.get('education', []))
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
            
            # Download processed data
            if st.button("💾 Download Processed Resume Data"):
                json_data = json.dumps(st.session_state.parsed_resumes, indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"processed_resumes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
    
    with tab3:
        st.header("3️⃣ Candidate Ranking & Matching")
        
        if st.session_state.processed_jd and st.session_state.parsed_resumes:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.success(f"✅ Ready to rank {len(st.session_state.parsed_resumes)} candidates")
            
            with col2:
                if st.button("🏆 Start Ranking", type="primary", use_container_width=True):
                    with st.spinner("Ranking candidates... This may take a moment."):
                        try:
                            # Progress tracking
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            # Get JD data
                            jd_data = st.session_state.processed_jd['data']
                            
                            status_text.text("📋 Preparing job description...")
                            
                            # Create JD text from structured data
                            jd_text_parts = []
                            jd_text_parts.append("REQUIRED SKILLS:")
                            if jd_data.get('required_skills'):
                                for skill in jd_data['required_skills']:
                                    jd_text_parts.append(f"- {skill}")
                            
                            jd_text_parts.append("\nPREFERRED SKILLS:")
                            if jd_data.get('preferred_skills'):
                                for skill in jd_data['preferred_skills']:
                                    jd_text_parts.append(f"- {skill}")
                            
                            jd_text_parts.append("\nEXPERIENCE REQUIREMENTS:")
                            exp_reqs = jd_data.get('experience_requirements', {}).get('years_required', [])
                            for req in exp_reqs:
                                min_years = req.get('min_years', 0)
                                jd_text_parts.append(f"- Minimum {min_years} years experience")
                            
                            jd_text = "\n".join(jd_text_parts)
                            
                            # Direct ranking without file system
                            ranked_candidates = []
                            total_resumes = len(st.session_state.parsed_resumes)
                            
                            for i, resume_data in enumerate(st.session_state.parsed_resumes):
                                try:
                                    status_text.text(f"🔍 Analyzing candidate {i+1}/{total_resumes}: {resume_data.get('file_name', 'Unknown')}")
                                    progress_bar.progress((i + 1) / total_resumes)
                                    
                                    # Create temporary file for this resume
                                    temp_dir = create_temp_directory()
                                    temp_resume_path = os.path.join(temp_dir, f"temp_resume_{i}.json")
                                    
                                    with open(temp_resume_path, 'w', encoding='utf-8') as f:
                                        json.dump(resume_data, f, ensure_ascii=False, indent=2)
                                    
                                    # Try matching - if it fails, create basic candidate entry
                                    try:
                                        match_result = match_resume_to_jd(temp_resume_path, jd_text)
                                        
                                        if match_result.get('success'):
                                            candidate_data = match_result['match_result']
                                            final_score = candidate_data.get('overall_score', 0)
                                            match_level = candidate_data.get('match_level', 'Poor Match')
                                            detailed_analysis = candidate_data
                                        else:
                                            # Create basic scoring if matching fails
                                            final_score = _calculate_basic_score(resume_data, jd_data)
                                            match_level = _get_match_level(final_score)
                                            detailed_analysis = _create_basic_analysis(resume_data, jd_data, final_score)
                                    
                                    except Exception as match_error:
                                        st.warning(f"⚠️ Matching failed for {resume_data.get('file_name')}, using basic scoring")
                                        # Fallback to basic scoring
                                        final_score = _calculate_basic_score(resume_data, jd_data)
                                        match_level = _get_match_level(final_score)
                                        detailed_analysis = _create_basic_analysis(resume_data, jd_data, final_score)
                                    
                                    # Create candidate entry (always create one regardless of score)
                                    enhanced_candidate = {
                                        'rank': len(ranked_candidates) + 1,
                                        'file_name': resume_data.get('file_name', 'Unknown'),
                                        'candidate_name': resume_data.get('name', 'Unknown Candidate'),
                                        'email': resume_data.get('contact_info', {}).get('email', 'No email'),
                                        'phone': resume_data.get('contact_info', {}).get('phone', 'No phone provided'),
                                        'linkedin': resume_data.get('contact_info', {}).get('linkedin', 'No LinkedIn provided'),
                                        'final_ranking_score': final_score,
                                        'match_level': match_level,
                                        'detailed_analysis': detailed_analysis,
                                        'original_resume_data': resume_data
                                    }
                                    
                                    ranked_candidates.append(enhanced_candidate)
                                    
                                    # Clean up temp file
                                    if os.path.exists(temp_resume_path):
                                        os.remove(temp_resume_path)
                                        
                                except Exception as e:
                                    # Even if processing fails, create a minimal candidate entry
                                    st.warning(f"⚠️ Error processing {resume_data.get('file_name', 'Unknown')}: {str(e)}")
                                    minimal_candidate = {
                                        'rank': len(ranked_candidates) + 1,
                                        'file_name': resume_data.get('file_name', 'Unknown'),
                                        'candidate_name': resume_data.get('name', 'Unknown Candidate'),
                                        'email': resume_data.get('contact_info', {}).get('email', 'No email'),
                                        'phone': resume_data.get('contact_info', {}).get('phone', 'No phone provided'),
                                        'linkedin': resume_data.get('contact_info', {}).get('linkedin', 'No LinkedIn provided'),
                                        'final_ranking_score': 10.0,  # Minimal score
                                        'match_level': 'Processing Error',
                                        'detailed_analysis': {'error': str(e)},
                                        'original_resume_data': resume_data
                                    }
                                    ranked_candidates.append(minimal_candidate)
                            
                            status_text.text("📊 Finalizing rankings...")
                            
                            # Sort candidates by score
                            ranked_candidates.sort(key=lambda x: x['final_ranking_score'], reverse=True)
                            
                            # Update ranks after sorting
                            for i, candidate in enumerate(ranked_candidates):
                                candidate['rank'] = i + 1
                            
                            # Create results structure
                            results = {
                                'success': True,
                                'total_candidates': len(ranked_candidates),
                                'processing_errors': len(st.session_state.parsed_resumes) - len(ranked_candidates),
                                'candidates': ranked_candidates,
                                'job_description_summary': {
                                    'required_skills_count': len(jd_data.get('required_skills', [])),
                                    'preferred_skills_count': len(jd_data.get('preferred_skills', [])),
                                    'top_required_skills': jd_data.get('required_skills', [])[:5]
                                },
                                'ranking_analysis': {
                                    'candidate_pool_size': len(ranked_candidates),
                                    'score_statistics': {
                                        'highest_score': max([c['final_ranking_score'] for c in ranked_candidates]) if ranked_candidates else 0,
                                        'lowest_score': min([c['final_ranking_score'] for c in ranked_candidates]) if ranked_candidates else 0,
                                        'average_score': sum([c['final_ranking_score'] for c in ranked_candidates]) / len(ranked_candidates) if ranked_candidates else 0
                                    },
                                    'match_level_distribution': {}
                                }
                            }
                            
                            # Calculate match level distribution
                            match_levels = {}
                            for candidate in ranked_candidates:
                                level = candidate['match_level']
                                match_levels[level] = match_levels.get(level, 0) + 1
                            results['ranking_analysis']['match_level_distribution'] = match_levels
                            
                            st.session_state.ranking_results = results
                            
                            progress_bar.progress(1.0)
                            status_text.text("✅ Ranking completed!")
                            
                            if ranked_candidates:
                                st.success(f"🎉 Successfully ranked {len(ranked_candidates)} candidates!")
                            else:
                                st.error("❌ No candidates could be ranked. Please check your resume data.")
                                
                        except Exception as e:
                            st.error(f"❌ Ranking failed: {str(e)}")
                            st.error("Please try uploading resumes again or check the job description.")
            
            # Display ranking results
            if st.session_state.ranking_results and st.session_state.ranking_results.get('success'):
                results = st.session_state.ranking_results
                candidates = results.get('candidates', [])
                
                if candidates:
                    # Filter by minimum score
                    filtered_candidates = [c for c in candidates if c.get('final_ranking_score', 0) >= min_score_threshold]
                    display_candidates = filtered_candidates[:max_candidates_display]
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Candidates", len(candidates))
                    with col2:
                        st.metric("Above Threshold", len(filtered_candidates))
                    with col3:
                        avg_score = sum(c.get('final_ranking_score', 0) for c in candidates) / len(candidates)
                        st.metric("Average Score", f"{avg_score:.1f}%")
                    with col4:
                        top_score = max(c.get('final_ranking_score', 0) for c in candidates)
                        st.metric("Top Score", f"{top_score:.1f}%")
                    
                    st.markdown("---")
                    
                    # Display top candidates
                    st.subheader(f"🏆 Top {len(display_candidates)} Candidates")
                    
                    for i, candidate in enumerate(display_candidates, 1):
                        display_candidate_card(candidate, i)
                    
                    # Download results
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("💾 Download Ranking Results"):
                            results_json = json.dumps(results, indent=2)
                            st.download_button(
                                label="📥 Download JSON Results",
                                data=results_json,
                                file_name=f"ranking_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                    
                    with col2:
                        if st.button("📊 Generate Report"):
                            # Create a summary report
                            report = f"""
# Candidate Ranking Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total Candidates Processed: {len(candidates)}
- Candidates Above Threshold ({min_score_threshold}%): {len(filtered_candidates)}
- Average Score: {avg_score:.1f}%
- Highest Score: {top_score:.1f}%

## Top Candidates
"""
                            for i, candidate in enumerate(display_candidates[:5], 1):
                                report += f"""
{i}. **{candidate.get('candidate_name', 'Unknown')}**
   - Score: {candidate.get('final_ranking_score', 0):.1f}%
   - Match Level: {candidate.get('match_level', 'Unknown')}
   - Email: {candidate.get('email', 'Not provided')}
   - File: {candidate.get('file_name', 'Unknown')}
"""
                            
                            st.download_button(
                                label="📄 Download Report (Markdown)",
                                data=report,
                                file_name=f"ranking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown"
                            )
                
                else:
                    st.warning("⚠️ No candidates found meeting the criteria")
        
        else:
            missing_items = []
            if not st.session_state.processed_jd:
                missing_items.append("Job Description")
            if not st.session_state.parsed_resumes:
                missing_items.append("Resume files")
            
            st.info(f"📋 Please complete: {', '.join(missing_items)}")
    
    with tab4:
        st.header("4️⃣ Analytics & Insights")
        
        if st.session_state.ranking_results and st.session_state.ranking_results.get('success'):
            create_ranking_visualizations(st.session_state.ranking_results)
            
            # Additional analytics
            st.subheader("📈 Advanced Analytics")
            
            results = st.session_state.ranking_results
            candidates = results.get('candidates', [])
            
            if candidates:
                # Skills frequency analysis
                all_skills = []
                for candidate in candidates:
                    # Safe navigation with proper null checks - use direct skill_analysis field
                    skill_analysis = candidate.get('skill_analysis', {})
                    if skill_analysis and isinstance(skill_analysis, dict):
                        required_matches = skill_analysis.get('required_matches', [])
                        if isinstance(required_matches, list):
                            all_skills.extend(required_matches)
                
                if all_skills:
                    skills_df = pd.DataFrame({'Skill': all_skills})
                    skills_count = skills_df['Skill'].value_counts().head(15)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_skills_freq = px.bar(
                            x=skills_count.values,
                            y=skills_count.index,
                            orientation='h',
                            title="🔧 Most Common Skills in Pool",
                            labels={'x': 'Number of Candidates', 'y': 'Skills'}
                        )
                        st.plotly_chart(fig_skills_freq, use_container_width=True)
                    
                    with col2:
                        # Experience vs Score correlation
                        exp_scores = []
                        for candidate in candidates:
                            # Safe experience count calculation - use resume_summary
                            exp_count = 0
                            resume_summary = candidate.get('resume_summary', {})
                            if resume_summary and isinstance(resume_summary, dict):
                                exp_count = resume_summary.get('experience_entries', 0)
                            
                            score = candidate.get('final_ranking_score', 0)
                            exp_scores.append({'Experience_Count': exp_count, 'Score': score})
                        
                        if exp_scores:
                            exp_df = pd.DataFrame(exp_scores)
                            fig_exp = px.scatter(
                                exp_df,
                                x='Experience_Count',
                                y='Score',
                                title="💼 Experience vs Score",
                                labels={'Experience_Count': 'Number of Experience Entries', 'Score': 'Match Score (%)'}
                            )
                            st.plotly_chart(fig_exp, use_container_width=True)
                else:
                    st.info("📊 No skill data available for analysis")
                
                # Export analytics data
                if st.button("📊 Export Analytics Data"):
                    analytics_data = {
                        'timestamp': datetime.now().isoformat(),
                        'summary': {
                            'total_candidates': len(candidates),
                            'average_score': sum(c.get('final_ranking_score', 0) for c in candidates) / len(candidates),
                            'score_distribution': {
                                'excellent': len([c for c in candidates if c.get('match_level') == 'Excellent Match']),
                                'good': len([c for c in candidates if c.get('match_level') == 'Good Match']),
                                'moderate': len([c for c in candidates if c.get('match_level') == 'Moderate Match']),
                                'fair': len([c for c in candidates if c.get('match_level') == 'Fair Match']),
                                'poor': len([c for c in candidates if c.get('match_level') == 'Poor Match'])
                            }
                        },
                        'skills_analysis': skills_count.to_dict() if 'skills_count' in locals() else {},
                        'candidates': candidates
                    }
                    
                    analytics_json = json.dumps(analytics_data, indent=2)
                    st.download_button(
                        label="📥 Download Analytics (JSON)",
                        data=analytics_json,
                        file_name=f"analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        else:
            st.info("📊 Complete the ranking process to view analytics")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        🚀 <strong>ResumePard</strong> - AI-Powered Resume Matching System<br>
        Built with Streamlit • Powered by spaCy NLP • Made with ❤️
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Application error: {str(e)}")
        st.info("Please refresh the page and try again.")
    finally:
        # Cleanup on exit
        cleanup_temp_directory()
