"""
Quick fix for NoneType errors in ResumePard app
"""

# Add this function to app.py to handle None data gracefully
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
    return {
        'rank': safe_get(candidate, 'rank', default=0),
        'file_name': safe_get(candidate, 'file_name', default='Unknown'),
        'candidate_name': safe_get(candidate, 'candidate_name', default='Unknown Candidate'),
        'email': safe_get(candidate, 'email', default='No email provided'),
        'phone': safe_get(candidate, 'phone', default='No phone provided'),
        'linkedin': safe_get(candidate, 'linkedin', default='No LinkedIn provided'),
        'final_ranking_score': safe_get(candidate, 'final_ranking_score', default=0.0),
        'match_level': safe_get(candidate, 'match_level', default='Unknown'),
        'skill_analysis': safe_get(candidate, 'skill_analysis', default={}),
        'experience_analysis': safe_get(candidate, 'experience_analysis', default={}),
        'education_analysis': safe_get(candidate, 'education_analysis', default={}),
        'project_analysis': safe_get(candidate, 'project_analysis', default={}),
        'additional_scores': safe_get(candidate, 'additional_scores', default={}),
        'recommendations': safe_get(candidate, 'recommendations', default=[]),
        'resume_summary': safe_get(candidate, 'resume_summary', default={
            'total_skills': 0,
            'top_skills': [],
            'experience_entries': 0,
            'education_entries': 0,
            'project_entries': 0,
            'has_contact_info': False
        })
    }
