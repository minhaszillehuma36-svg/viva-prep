# 🎓 Viva Prep AI

**An AI-powered viva/thesis defense practice tool for final-year IT/CS students.**

## 🧩 The Problem

Every final-year student has to face a **viva voce (oral defense)** for their FYP or thesis — and most students walk in with little idea of what an examiner will actually ask about *their specific project*. Generic study guides don't help because every FYP is different: different tech stack, different architecture, different design decisions.

**Viva Prep AI** solves this by acting as a personal AI examiner: you describe your project, and it generates realistic, project-specific viva questions — then evaluates your answers the way a real examiner would, pointing out what's missing and how to improve.

**Who it's for:** Final-year university students (IT, CS, Software Engineering, and related fields) preparing for their FYP/thesis viva defense.

---

## 🔗 Live App

👉 **[https://viva-prep-production.up.railway.app](https://viva-prep-production.up.railway.app)**

---

## ✨ Features

- **User authentication** — secure signup/login with hashed passwords and session management
- **Project profiles** — save multiple FYP/thesis projects with title, domain, tech stack, and description
- **AI-generated viva questions** — automatically generates 8–16 questions tailored to your specific project, organized into categories:
  - Project Concept & Motivation
  - Software Architecture & Design
  - Technology Stack & Tools
  - Diagrams & System Flow
  - Hardware/Deployment (when relevant)
  - Critical Evaluation
- **Category filter tabs** — instantly filter questions by category without reloading the page
- **Practice answering** — type your answer to any question directly in the app
- **AI examiner feedback** — get instant, structured feedback on each answer:
  - What you got right
  - What was missing or vague
  - How to improve your answer
  - A readiness rating: **Weak / Needs Work / Solid**
- **Persistent history** — all your projects, questions, and answers are saved so you can revisit and keep practicing

---

## 🤖 The AI Feature

The core of this app is an **AI Examiner** built on Google's Gemini API, with two custom-engineered prompts:

### 1. Question Generation

The AI is instructed to act as a strict-but-fair external examiner and generate questions that are:
- **Specific to the student's actual project** (not generic definitions)
- **Never definitional** — e.g., it will never ask "What is Whisper?"; instead it asks about *decisions*, *trade-offs*, and *implementation choices*
- Organized into a fixed set of categories (concept, architecture, tech stack, diagrams/flow, hardware if relevant, critical evaluation)
- Scaled in number to the project's complexity (simple projects get fewer questions, complex ones get more)

**Core system prompt (question generation):**
```
You are a strict but fair external FYP/thesis viva examiner with deep 
expertise across computer science and IT domains. You will be given a 
student's project details: title, description, domain, and technology 
stack.

Generate viva questions organized into categories: Project Concept & 
Motivation, Software Architecture & Design, Technology Stack & Tools, 
Diagrams & System Flow, Hardware/Deployment Environment (only if relevant), 
and Critical Evaluation.

NEVER ask what a technology/tool/concept IS or means. The student already 
knows these definitions. Instead, ask about their SPECIFIC DECISIONS, 
IMPLEMENTATION CHOICES, and REASONING — why they chose a specific tool 
over alternatives, how components integrate, what problems they faced, 
and how their design handles edge cases or failure scenarios.

Each question must be ONE short, direct sentence referencing specific 
details from the student's actual project.
```

### 2. Answer Evaluation

The AI evaluates the student's typed answer against the question and project context, returning structured, honest feedback.

**Core system prompt (answer evaluation):**
```
You are a strict but fair external FYP/thesis viva examiner evaluating a 
student's answer to a viva question. Given the project context, the 
question asked, and the student's answer, provide feedback in this format:

GOOD: [what was good or correct in the answer]
MISSING: [what was missing, vague, or incorrect]
IMPROVE: [one specific way to strengthen the answer]
RATING: [exactly one of: Weak / Needs Work / Solid]

Be constructive but honest — never inflate the rating.
```

---

## 🛠️ Tools, Services & Models Used

| Category | Tool/Service |
|---|---|
| Backend framework | Flask (Python) |
| Database | SQLite + Flask-SQLAlchemy |
| Authentication | Session-based auth with Werkzeug password hashing |
| AI model | Google Gemini (`gemini-flash-latest`) via `google-genai` SDK |
| Frontend | Bootstrap 5, vanilla JavaScript, custom CSS |
| Deployment | Railway (via GitHub integration) |
| Production server | Gunicorn |
| Dev environment | Antigravity IDE |
| Version control | Git + GitHub |

---

## 📸 Screenshots

**Dashboard — project overview**
![Dashboard](Screenshot%202026-07-27%20154525.png)

**Viva Practice Session — categorized questions with filter tabs**
![Viva Session](Screenshot%202026-07-27%20154548.png)

**AI Examiner Feedback**
![AI Feedback](Screenshot%202026-07-27%20154605.png)

---

## 🚀 How to Run Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/minhaszillehuma36-svg/viva-prep.git
   cd viva-prep
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root (use `.env.example` as a template):
   ```
   SECRET_KEY=your-secret-key
   GEMINI_API_KEY=your-gemini-api-key
   ```
   Get a free Gemini API key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

4. **Run the app**
   ```bash
   python app.py
   ```

5. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

---

## 📁 Project Structure

```
viva-prep/
├── app.py                 # Flask routes and app logic
├── models.py               # Database models (User, Project, Question, Answer)
├── ai_service.py            # Gemini API integration (question generation + evaluation)
├── config.py                # App configuration
├── requirements.txt
├── Procfile                 # Deployment config for Railway/Gunicorn
├── templates/               # HTML templates (Bootstrap 5)
└── static/css/               # Custom styling
```

---

Built as a final project to solve a real problem I'm personally facing as a final-year student preparing for my own FYP viva defense.
