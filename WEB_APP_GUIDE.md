# ResumePard Web Application - User Guide

## 🚀 Quick Start Guide

### 1. Starting the Application

**Option A: Using the Batch File (Recommended)**
```bash
Double-click on start_app.bat
```

**Option B: Using Command Line**
```bash
# Activate virtual environment
resume_parser_env\Scripts\activate

# Start the application
streamlit run app.py
```

### 2. Accessing the Application
- Open your web browser
- Navigate to: `http://localhost:8501`
- The ResumePard interface will load automatically

### 3. Using the Application

#### Step 1: Job Description Analysis 📋
1. Go to the "📋 Job Description" tab
2. Choose input method:
   - **Paste Text**: Copy and paste job description
   - **Upload File**: Upload TXT, PDF, or DOCX file
3. Click "🔍 Analyze Job Description"
4. Review extracted requirements and skills

#### Step 2: Resume Upload 📄
1. Go to the "📄 Resume Upload" tab
2. Click "Choose resume files" 
3. Select multiple PDF, DOCX, or TXT resume files
4. Click "🚀 Process Resumes"
5. Wait for processing to complete

#### Step 3: Candidate Ranking 🏆
1. Go to the "🏆 Ranking Results" tab
2. Verify job description and resumes are processed
3. Click "🏆 Start Ranking"
4. View ranked candidates with scores and analysis

#### Step 4: Analytics & Insights 📊
1. Go to the "📊 Analytics" tab
2. View interactive charts and visualizations
3. Analyze candidate pool statistics
4. Download analytics data

### 4. Features Overview

#### 🎯 Advanced Scoring System
- **Skills Matching**: Weighted scoring for required vs preferred skills
- **Experience Analysis**: Years of experience vs job requirements
- **Education Matching**: Degree and qualification alignment
- **Project Relevance**: Portfolio and project evaluation

#### 📊 Interactive Visualizations
- Candidate score distribution charts
- Skills gap analysis
- Match level pie charts
- Experience correlation graphs

#### 🔧 Customizable Settings (Sidebar)
- **Scoring Weights**: Adjust importance of skills, experience, education
- **Filtering Options**: Set minimum score thresholds
- **Display Limits**: Control number of candidates shown
- **Advanced Options**: Save results, detailed analysis toggle

#### 💾 Export & Download Options
- JSON format results
- Markdown reports
- Analytics data export
- Processed resume data

### 5. Sample Data for Testing

#### Sample Job Description:
```
Senior Python Developer - Remote Position

We are seeking an experienced Senior Python Developer to join our team.

Required Skills:
- 5+ years of Python development experience
- Strong experience with Django or Flask frameworks
- Proficiency in SQL databases (PostgreSQL, MySQL)
- RESTful API design and development
- Git version control
- AWS cloud services
- Agile/Scrum methodology

Preferred Skills:
- MongoDB or NoSQL databases
- Docker containerization
- React.js frontend experience
- Machine Learning libraries
- Kubernetes orchestration
- CI/CD pipeline experience

Experience Requirements:
- Minimum 5 years of software development
- Leadership or mentoring experience preferred

Education:
- Bachelor's degree in Computer Science or related field
- OR equivalent professional experience
```

#### Sample Resumes:
- Use the `resume_sarah_johnson.txt` (high match)
- Use the `resume_mike_chen.txt` (moderate match)
- Use the `dummy.pdf` (existing sample)

### 6. Troubleshooting

#### Common Issues:

**🔴 Application won't start**
- Ensure virtual environment is activated
- Check if port 8501 is available
- Verify Streamlit installation: `python -c "import streamlit"`

**🔴 File upload fails**
- Check file size (max 200MB)
- Ensure supported format (PDF, DOCX, TXT)
- Try refreshing the page

**🔴 Processing errors**
- Verify spaCy model is installed: `python -m spacy download en_core_web_sm`
- Check if files are corrupted
- Clear browser cache

**🔴 Ranking fails**
- Ensure both JD and resumes are processed
- Check for sufficient memory
- Try with fewer resume files

#### Getting Help:
1. Check the browser console for errors (F12)
2. Review the terminal output for Python errors
3. Try refreshing the page
4. Restart the application

### 7. Performance Tips

#### For Large Batches:
- Process 20-30 resumes at a time for optimal performance
- Use higher-end hardware for 50+ resumes
- Close other applications to free memory

#### For Better Results:
- Use well-formatted job descriptions with clear requirements
- Ensure resume files are not corrupted
- Use consistent file naming conventions

### 8. Advanced Usage

#### API Integration:
The backend modules can be used programmatically:
```python
from main_matcher import ResumePardMatcher

matcher = ResumePardMatcher()
results = matcher.rank_multiple_candidates(
    "resumes_folder/", 
    "job_description.txt", 
    "output_folder/"
)
```

#### Batch Processing:
For command-line batch operations:
```bash
python main_matcher.py rank resumes/ jd.txt --output results/ --min-score 50
```

### 9. System Requirements

#### Minimum:
- Python 3.9+
- 4GB RAM
- 2GB free disk space
- Modern web browser

#### Recommended:
- Python 3.9+
- 8GB RAM
- 5GB free disk space
- Chrome/Firefox latest version

### 10. Security Notes

- Files are processed locally on your machine
- No data is sent to external servers
- Temporary files are automatically cleaned up
- Resume data is not permanently stored unless exported

---

## 🎉 You're Ready to Use ResumePard!

The application provides a complete solution for:
- ✅ Automated resume parsing
- ✅ Intelligent job matching
- ✅ Candidate ranking and analysis
- ✅ Interactive visualizations
- ✅ Comprehensive reporting

Happy recruiting! 🚀
