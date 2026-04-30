# Nexa CV – AI-Powered Resume Analyzer

## 🚀 Overview

Nexa CV is a web-based application that analyzes resumes using AI and provides actionable feedback to improve them. It evaluates ATS (Applicant Tracking System) compatibility, extracts key skills, and generates intelligent suggestions based on job descriptions.

This project demonstrates full-stack development using Flask along with AI integration.

---

## ✨ Features

* 📄 Resume Upload (PDF)
* 🤖 AI-based Resume Analysis
* 📊 ATS Score Calculation
* 🧠 Skill Extraction
* 🔐 User Authentication (Login/Register)
* 📁 Analysis History Tracking
* 📥 Downloadable PDF Report

---

## 🛠 Tech Stack

* **Backend:** Python, Flask
* **Frontend:** HTML, CSS, JavaScript
* **AI Integration:** OpenAI / Groq API
* **Other Libraries:**

  * `pdf parsing`
  * `dotenv`
  * `werkzeug`

---

## 📂 Project Structure

```
nexacv/
│
├── app.py
├── requirements.txt
├── Procfile
├── .env.example
│
├── templates/
├── static/
├── prompts/
├── data/
│
├── auth.py
├── ai_analyzer.py
├── ats_score.py
├── resume_parser.py
├── skill_extractor.py
├── report_generator.py
├── utils.py
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```
git clone https://github.com/yourusername/nexa-cv-project.git
cd nexa-cv-project
```

### 2. Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create a `.env` file and add:

```
OPENAI_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
```

---

## ▶️ Run the Application

```
python app.py
```

Visit:

```
http://127.0.0.1:5000
```

---

## 🌐 Deployment

This project is deployed using **Render**.

Key configurations:

* Build Command: `pip install -r requirements.txt`
* Start Command: `python app.py`
* Environment Variables configured in Render dashboard

---

## ⚠️ Notes

* The app uses file-based storage (`data/`) for simplicity
* Data persistence may not be permanent on cloud platforms
* API keys are not included for security reasons

---

## 📌 Future Improvements

* Database integration (PostgreSQL / MongoDB)
* Better UI/UX enhancements
* Real-time resume scoring feedback
* Multi-format resume support

---

## 👩‍💻 Author

Sneha B

---

## ⭐ Acknowledgements

* Flask Documentation
* OpenAI / Groq APIs
