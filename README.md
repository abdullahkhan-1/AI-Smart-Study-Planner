# Smart Study Planner 📚
**AI-Based Study Scheduling System | SE + AI Spring 2026**
FAST NUCES, Karachi — CS Department

## Group Members
| Roll No     | Name          | Role                        |
|-------------|---------------|-----------------------------|
| 23k-0525    | Abdullah Khan | Project Lead + AI Logic     |
| 23k-0878    | Ammar Khan    | Frontend                    |
| 23K-0692    | Hasnain Kazmi | SRS Report                  |

---

## About
An AI-powered web application that generates optimized study schedules using
heuristic priority scoring, Greedy EDF scheduling, and Machine Learning.

---

## Features
| Feature                     |
|-----------------------------|
| AI Scheduler (Heuristic + Greedy EDF) | 
| Simple FIFO Scheduler (baseline)      |
| Performance Comparison (AI vs Simple) |
| ML Study Time Predictor (Linear Regression) |
| NLP Deadline Parser         | 
| Visual Analytics Dashboard  | 
| Pomodoro Timer              | 
| Adaptive Rescheduling       | 

---

## Design Patterns Used
| Pattern          | Where                          |
|------------------|--------------------------------|
| Strategy Pattern | scheduler.py — swappable algorithms |
| Singleton Pattern| models.py — one DB connection  |
| MVC Pattern      | app.py + templates/ + models.py|

---

## Tech Stack
| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python + Flask                    |
| Database | PostgreSQL (hosted on Supabase)   |
| ML       | scikit-learn (Linear Regression)  |
| NLP      | dateparser + custom patterns      |
| Frontend | HTML + CSS + Chart.js             |

---

## Setup Instructions

### 1. Clone the repository
```
git clone https://github.com/YOUR_USERNAME/smart-study-planner.git
cd smart-study-planner
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Create a `.env` file
Create a file called `.env` in the project root:
```
DATABASE_URL=postgresql://postgres.xxxx:PASSWORD@host:5432/postgres
```
Get this connection string from the Supabase dashboard → Direct connection.

### 4. Run the app
```
python app.py
```

### 5. Open in browser
```
http://127.0.0.1:5000
```

---

## Project Structure
```
smart-study-planner/
├── app.py           ← Flask web app (MVC Controller)
├── scheduler.py     ← AI scheduling engine (Strategy Pattern)
├── models.py        ← PostgreSQL database layer (Singleton Pattern)
├── ml_predictor.py  ← scikit-learn ML model
├── nlp_parser.py    ← Natural language deadline parser
├── requirements.txt ← Python dependencies
├── .env             ← Database credentials (NOT committed to GitHub)
├── .gitignore       ← Excludes .env and cache files
└── templates/       ← HTML pages (MVC View)
    ├── base.html
    ├── index.html
    ├── add_task.html
    ├── schedule.html
    ├── compare.html
    ├── analytics.html
    ├── pomodoro.html
    ├── reschedule.html
    ├── predict.html
    └── progress.html
```

---

## ⚠️ Important Note for Teammates
The `.env` file is NOT on GitHub (intentionally — it contains the database password).
Each group member must create their own `.env` file manually using the
connection string shared privately by the group leader.
