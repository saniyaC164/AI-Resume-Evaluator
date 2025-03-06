from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import PyPDF2
import docx
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def analyze_resume(text):
    """
    Analyze the resume text and provide feedback
    This is a simple rule-based analysis for demonstration
    In a real application, you would use more sophisticated NLP or AI models
    """
    # Convert to lowercase for easier analysis
    text_lower = text.lower()
    
    # Initialize scores and feedback
    score = 0
    strengths = []
    weaknesses = []
    suggestions = []
    
    # Check for contact information
    if re.search(r'[\w\.-]+@[\w\.-]+', text):  # Email
        score += 5
    else:
        weaknesses.append("Missing email address")
        suggestions.append("Add your email address for contact information")
    
    if re.search(r'\b(?:\+\d{1,3}[-\s]?)?$$?\d{3}$$?[-\s]?\d{3}[-\s]?\d{4}\b', text):  # Phone
        score += 5
    else:
        weaknesses.append("Missing phone number")
        suggestions.append("Add your phone number for contact information")
    
    # Check for LinkedIn profile
    if 'linkedin.com' in text_lower:
        score += 5
        strengths.append("Includes LinkedIn profile")
    else:
        suggestions.append("Add your LinkedIn profile to enhance networking opportunities")
    
    # Check for education section
    education_keywords = ['education', 'university', 'college', 'bachelor', 'master', 'phd', 'degree']
    if any(keyword in text_lower for keyword in education_keywords):
        score += 10
        strengths.append("Education section is present")
    else:
        weaknesses.append("Missing or unclear education section")
        suggestions.append("Add a clear education section with degrees and institutions")
    
    # Check for experience section
    experience_keywords = ['experience', 'work', 'job', 'position', 'employment']
    if any(keyword in text_lower for keyword in experience_keywords):
        score += 15
        strengths.append("Work experience section is present")
    else:
        weaknesses.append("Missing or unclear work experience section")
        suggestions.append("Add detailed work experience with responsibilities and achievements")
    
    # Check for skills section
    skills_keywords = ['skills', 'abilities', 'proficient', 'expertise']
    if any(keyword in text_lower for keyword in skills_keywords):
        score += 10
        strengths.append("Skills section is present")
    else:
        weaknesses.append("Missing or unclear skills section")
        suggestions.append("Add a dedicated skills section highlighting your technical and soft skills")
    
    # Check for action verbs
    action_verbs = ['achieved', 'implemented', 'developed', 'created', 'managed', 'led', 'designed', 'improved']
    action_verb_count = sum(1 for verb in action_verbs if verb in text_lower)
    if action_verb_count >= 5:
        score += 10
        strengths.append("Good use of action verbs to describe achievements")
    else:
        weaknesses.append("Limited use of action verbs")
        suggestions.append("Use more action verbs to describe your accomplishments")
    
    # Check for quantifiable achievements
    if re.search(r'\b\d+%\b', text) or re.search(r'\bincreased\b.*\b\d+\b', text_lower) or re.search(r'\bdecreased\b.*\b\d+\b', text_lower):
        score += 15
        strengths.append("Includes quantifiable achievements")
    else:
        weaknesses.append("Lacks quantifiable achievements")
        suggestions.append("Add metrics and numbers to demonstrate your impact")
    
    # Check resume length (rough estimate based on character count)
    if len(text) < 1500:
        weaknesses.append("Resume may be too short")
        suggestions.append("Expand your resume with more details about your experience and skills")
    elif len(text) > 6000:
        weaknesses.append("Resume may be too long")
        suggestions.append("Consider condensing your resume to focus on the most relevant information")
    else:
        score += 5
        strengths.append("Resume length appears appropriate")
    
    # Add general suggestions
    suggestions.append("Tailor your resume for each job application to match the job description")
    suggestions.append("Use a clean, professional format with consistent styling")
    
    # Ensure we have at least some strengths
    if not strengths:
        strengths.append("Resume provides basic information about your background")
    
    # Cap the score at 100
    score = min(score + 20, 100)  # Base score of 20 for submitting a resume
    
    return {
        "score": score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions
    }

@app.route('/api/evaluate-resume', methods=['POST'])
def evaluate_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['resume']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # Create a temporary file to save the uploaded resume
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            file.save(temp.name)
            file_path = temp.name
        
        try:
            # Extract text based on file type
            filename = secure_filename(file.filename)
            if filename.endswith('.pdf'):
                text = extract_text_from_pdf(file_path)
            elif filename.endswith('.docx'):
                text = extract_text_from_docx(file_path)
            else:
                return jsonify({"error": "Unsupported file format"}), 400
            
            # Analyze the resume
            analysis_results = analyze_resume(text)
            
            # Clean up the temporary file
            os.unlink(file_path)
            
            return jsonify(analysis_results)
        
        except Exception as e:
            # Clean up the temporary file in case of error
            if os.path.exists(file_path):
                os.unlink(file_path)
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file format"}), 400

if __name__ == '__main__':
    app.run(debug=True)