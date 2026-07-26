import os
import re
import time
import traceback
from google import genai
from google.genai import types
from google.genai.errors import APIError

def get_gemini_client():
    """
    Retrieves and instantiates the Gemini client with a 60-second timeout.
    Raises ValueError if GEMINI_API_KEY is missing.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please set it in your .env file.")
    # Set timeout to 60 seconds (60,000 milliseconds)
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=60000))

def _call_gemini_with_retry(system_prompt, user_message, max_attempts=3, delay=2):
    """
    Calls the Gemini API using Client.models.generate_content.
    If the request fails due to connection or API errors, it retries up to 2 more times (3 attempts total)
    with a 2-second delay. It logs the exact error message and prints the full exception traceback.
    """
    for attempt in range(max_attempts):
        try:
            client = get_gemini_client()
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=user_message,
                config={"system_instruction": system_prompt}
            )
            return response.text
        except (ConnectionError, TimeoutError, APIError, Exception) as e:
            # Print exact error message and traceback as requested
            print(f"\n[AI Service Connection/API Error] Attempt {attempt + 1}/{max_attempts} failed.")
            print(f"Error Message: {str(e)}")
            traceback.print_exc()
            
            if attempt < max_attempts - 1:
                print(f"Retrying in {delay} seconds...\n")
                time.sleep(delay)
            else:
                print("All retry attempts failed. Raising the exception.")
                raise e

def generate_questions(title, description, tech_stack, domain):
    """
    Calls Gemini to generate viva questions based on project metadata, categorized and ordered.
    Parses the response into a list of dictionaries with 'text' and 'category' keys.
    """
    system_prompt = (
        "You are a strict but fair external FYP/thesis viva examiner with deep "
        "expertise across computer science and IT domains. You will be given a "
        "student's project details: title, description, domain, and technology "
        "stack.\n\n"
        "Generate viva questions organized into these categories, IN THIS ORDER. "
        "Only include a category if it is genuinely relevant to the project "
        "(e.g., skip Hardware if the project is purely a web/mobile app with no "
        "embedded systems, IoT, or physical device component):\n\n"
        "1. PROJECT CONCEPT & MOTIVATION (2-3 questions): the problem being solved, "
        "who it's for, why this idea, what makes it different from existing "
        "solutions.\n\n"
        "2. SOFTWARE ARCHITECTURE & DESIGN (2-4 questions): overall system design, "
        "how components/modules interact, design pattern choices, database "
        "schema decisions.\n\n"
        "3. TECHNOLOGY STACK & TOOLS (2-4 questions): why specific languages, "
        "frameworks, libraries, or APIs were chosen over alternatives, and how "
        "they integrate with each other.\n\n"
        "4. DIAGRAMS & SYSTEM FLOW (1-3 questions): questions probing understanding "
        "of the project's data flow, sequence of operations, or system "
        "architecture as it would appear in a DFD/ERD/sequence diagram — even if "
        "no diagram is attached, ask about the underlying flow/logic.\n\n"
        "5. HARDWARE / DEPLOYMENT ENVIRONMENT (0-2 questions, ONLY if relevant): "
        "include only if the project involves physical devices, sensors, "
        "embedded systems, IoT, or specific deployment infrastructure worth "
        "probing (e.g., server setup, edge devices). Skip entirely for standard "
        "web/mobile/software-only projects.\n\n"
        "6. CRITICAL EVALUATION (2-3 questions): limitations, edge cases, "
        "scalability, security concerns, and possible future improvements.\n\n"
        "Total question count should scale with project complexity — simple "
        "projects: 8-10 questions total, complex/multi-component projects: 12-16 "
        "questions total. Do not force categories to have questions if there is "
        "nothing genuinely relevant to ask.\n\n"
        "CRITICAL FORMATTING RULES:\n"
        "- Each question must be ONE short, direct sentence — like a real examiner "
        "asks out loud.\n"
        "- No long multi-clause setups, no combining multiple questions into one.\n"
        "- Every question must reference specific details from the project "
        "(its actual tech stack, actual features) — never generic/generic-sounding "
        "questions.\n"
        "- NEVER ask what a technology/tool/concept IS or means (e.g., never ask "
        "'What is Whisper?' or 'What does JWT stand for?'). The student already "
        "knows these definitions. Instead, ask about their SPECIFIC DECISIONS, "
        "IMPLEMENTATION CHOICES, and REASONING, such as:\n"
        "  * Why they chose THIS specific tool over alternatives for THEIR use case\n"
        "  * How THIS specific tool integrates with the other parts of THEIR system\n"
        "  * What problems they faced implementing THIS specific feature and how they "
        "solved it\n"
        "  * What would break or change if they removed/swapped a specific component\n"
        "  * How their specific design handles a specific edge case or failure scenario\n"
        "Every question must assume the student already knows the basic definition "
        "and instead probe their depth of understanding of how and why they built "
        "what they built. Bad question: 'What is Vosk used for?' Good question: "
        "'Why did you choose Vosk for real-time captioning instead of just using "
        "Whisper for everything, given Whisper is already in your stack?'\n\n"
        "Output format: group questions under bold category headers exactly like "
        "this:\n\n"
        "**Project Concept & Motivation**\n"
        "1. [question]\n"
        "2. [question]\n\n"
        "**Software Architecture & Design**\n"
        "1. [question]\n"
        "...\n\n"
        "(continue this pattern for each relevant category, skipping any that don't "
        "apply)\n\n"
        "Output ONLY this structured list, no extra commentary before or after."
    )
    
    user_message = (
        f"Project Title: {title}\n"
        f"Description: {description}\n"
        f"Tech Stack: {tech_stack}\n"
        f"Domain: {domain}"
    )
    
    response_text = _call_gemini_with_retry(system_prompt, user_message)
    return parse_questions_list(response_text)

def evaluate_answer(project_context, question_text, student_answer):
    """
    Calls Gemini to evaluate the student's answer.
    Parses the response into a dictionary containing good, missing, improve, and rating.
    """
    system_prompt = (
        "You are a strict but fair external FYP/thesis viva examiner evaluating a "
        "student's spoken answer to a viva question. Given the project context, the "
        "question asked, and the student's answer, provide feedback in this exact "
        "format:\n"
        "GOOD: [what was good or correct in the answer, one sentence]\n"
        "MISSING: [what was missing, vague, or incorrect, one to two sentences]\n"
        "IMPROVE: [one specific concrete way to strengthen the answer]\n"
        "RATING: [exactly one of: Weak / Needs Work / Solid]\n"
        "Be constructive but honest — never inflate the rating. Keep total response "
        "under 120 words."
    )
    
    user_message = (
        f"=== PROJECT CONTEXT ===\n{project_context}\n\n"
        f"=== QUESTION ===\n{question_text}\n\n"
        f"=== STUDENT ANSWER ===\n{student_answer}"
    )
    
    response_text = _call_gemini_with_retry(system_prompt, user_message)
    return parse_feedback(response_text)

def parse_questions_list(text):
    """
    Utility to parse questions grouped under category headers.
    Returns a list of dicts: [{'text': question_text, 'category': category_name}]
    """
    lines = text.strip().split('\n')
    questions = []
    current_category = "General"
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for category header like **Project Concept & Motivation** or **Project Concept & Motivation
        if line.startswith('**'):
            current_category = line.replace('**', '').strip()
            continue
            
        # Check if line starts with a number like 1., 2. etc
        if re.match(r'^\d+[\.\)\-\s]+', line):
            cleaned = re.sub(r'^\d+[\.\)\-\s]+', '', line).strip()
            if cleaned:
                questions.append({
                    'text': cleaned,
                    'category': current_category
                })
        elif not line.startswith('*') and len(line) > 10:
            # Fallback for unnumbered lines
            questions.append({
                'text': line,
                'category': current_category
            })
            
    return questions

def parse_feedback(text):
    """
    Utility to extract GOOD, MISSING, IMPROVE, and RATING from Claude's formatted response.
    """
    result = {
        'good': '',
        'missing': '',
        'improve': '',
        'rating': 'Needs Work'
    }
    
    # Regex patterns looking for prefix tags (case-insensitive)
    patterns = {
        'good': r'GOOD:\s*(.*?)(?=(?:MISSING|IMPROVE|RATING):|$)',
        'missing': r'MISSING:\s*(.*?)(?=(?:GOOD|IMPROVE|RATING):|$)',
        'improve': r'IMPROVE:\s*(.*?)(?=(?:GOOD|MISSING|RATING):|$)',
        'rating': r'RATING:\s*(.*?)(?=(?:GOOD|MISSING|IMPROVE):|$)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if key == 'rating':
                val_lower = val.lower()
                if 'solid' in val_lower:
                    result['rating'] = 'Solid'
                elif 'weak' in val_lower:
                    result['rating'] = 'Weak'
                else:
                    result['rating'] = 'Needs Work'
            else:
                result[key] = val
                
    # Fallback if parsing fails to find the markers
    if not result['good'] and not result['missing'] and not result['improve']:
        result['missing'] = text.strip()
        result['rating'] = 'Needs Work'
        
    return result
