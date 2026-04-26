# Smart Study Planner 📚
**AI-Based Study Scheduling System | SE Spring 2026**
FAST NUCES, Karachi — CS Department

## Group Members
| Roll No | Name |
|---|---|
| 23k-0525 | Abdullah Khan |
| 23k-0878 | Ammar Khan |
| 23K-0692 | Hasnain Kazmi |

## About
An AI-powered web application that generates optimized study schedules using:
- **Heuristic Priority Scoring** (deadline urgency + difficulty + importance)
- **Greedy EDF Scheduling Algorithm**
- **Performance comparison** vs simple FIFO scheduling

## Design Patterns Used
- **Strategy Pattern** — Swappable scheduling algorithms (AIScheduler / SimpleScheduler)
- **Singleton Pattern** — Single shared database connection
- **MVC Pattern** — Flask (Controller) + Templates (View) + Models (Model)

## Setup Instructions

### 1. Install Python
Download from https://python.org — make sure to check "Add to PATH"

### 2. Open terminal in this folder
Right-click the project folder → "Open in Terminal"

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Run the app
```
python app.py
```

### 5. Open in browser
Go to: http://127.0.0.1:5000

## Project Structure
```
smart-study-planner/
├── app.py          ← Flask web app (Controller)
├── scheduler.py    ← AI scheduling engine
├── models.py       ← Database layer (Model)
├── templates/      ← HTML pages (View)
└── requirements.txt
```