# =============================================================================
# app.py — Flask Web Application (MVC Controller)
# Smart Study Planner | SE Spring 2026
# =============================================================================
# DESIGN PATTERN: MVC (Model-View-Controller)
#   - Model      → models.py  (database, data logic)
#   - View       → templates/ (HTML pages)
#   - Controller → THIS FILE  (handles requests, connects M and V)
# =============================================================================

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import date
from models import TaskModel, ProgressModel
from scheduler import SchedulerContext, AIScheduler, SimpleScheduler, compare_schedulers

app = Flask(__name__)
app.secret_key = "study_planner_secret_2026"   # Needed for flash messages

# Instantiate models (they use the Singleton DB internally)
task_model     = TaskModel()
progress_model = ProgressModel()

# Instantiate scheduler context (uses AIScheduler by default)
scheduler_ctx  = SchedulerContext()

# =============================================================================
# Route 1: Home / Dashboard
# =============================================================================

@app.route("/")
def index():
    """Show all tasks and a quick summary."""
    tasks   = task_model.get_all_tasks()
    summary = progress_model.get_summary()
    today   = date.today()

    # Flag overdue tasks
    for task in tasks:
        task["is_overdue"] = task["deadline"] < today

    return render_template("index.html", tasks=tasks, summary=summary, today=today)


# =============================================================================
# Route 2: Add a New Task
# =============================================================================

@app.route("/add", methods=["GET", "POST"])
def add_task():
    """Display and process the Add Task form."""

    if request.method == "POST":
        subject     = request.form.get("subject", "").strip()
        deadline    = request.form.get("deadline")
        difficulty  = int(request.form.get("difficulty", 3))
        importance  = int(request.form.get("importance", 3))
        study_hours = float(request.form.get("study_hours", 5))

        # Basic validation
        if not subject or not deadline:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("add_task"))

        deadline_date = date.fromisoformat(deadline)
        if deadline_date <= date.today():
            flash("Deadline must be a future date.", "warning")
            return redirect(url_for("add_task"))

        task_model.add_task(subject, deadline_date, difficulty, importance, study_hours)
        flash(f'Task "{subject}" added successfully!', "success")
        return redirect(url_for("index"))

    return render_template("add_task.html")


# =============================================================================
# Route 3: Generate Schedule
# =============================================================================

@app.route("/schedule", methods=["GET", "POST"])
def schedule():
    """Generate and display the AI-optimized study schedule."""

    tasks             = task_model.get_all_tasks()
    schedule_data     = None
    available_hours   = 4.0   # Default daily hours
    algorithm_used    = "AI Scheduler"

    if request.method == "POST":
        available_hours = float(request.form.get("available_hours", 4.0))
        algo            = request.form.get("algorithm", "ai")

        # Strategy Pattern in action — swap algorithm based on user choice
        if algo == "simple":
            scheduler_ctx.set_strategy(SimpleScheduler())
            algorithm_used = "Simple Scheduler (FIFO)"
        else:
            scheduler_ctx.set_strategy(AIScheduler())
            algorithm_used = "AI Scheduler (Heuristic + Greedy EDF)"

        raw_schedule = scheduler_ctx.run(tasks, available_hours)

        # Sort the schedule by date for display
        schedule_data = {
            str(k): v
            for k, v in sorted(raw_schedule.items())
        }

    return render_template(
        "schedule.html",
        tasks          = tasks,
        schedule       = schedule_data,
        available_hours= available_hours,
        algorithm_used = algorithm_used,
    )


# =============================================================================
# Route 4: Performance Comparison Page
# =============================================================================

@app.route("/compare")
def compare():
    """
    Run both schedulers and show a side-by-side comparison.
    This is the 'Performance Comparison' section for rubric marks.
    """
    tasks = task_model.get_all_tasks()

    if not tasks:
        flash("Add some tasks first to see the comparison.", "info")
        return redirect(url_for("index"))

    available_hours = float(request.args.get("hours", 4.0))
    results = compare_schedulers(tasks, available_hours)

    return render_template("compare.html", results=results, hours=available_hours)


# =============================================================================
# Route 5: Mark Session as Complete
# =============================================================================

@app.route("/complete", methods=["POST"])
def mark_complete():
    subject      = request.form.get("subject")
    session_date = request.form.get("date")
    hours        = float(request.form.get("hours", 1.0))

    progress_model.mark_complete(subject, session_date, hours)
    flash(f'Session for "{subject}" marked as complete! ✅', "success")
    return redirect(url_for("schedule"), code=302)


# =============================================================================
# Route 6: Delete Task
# =============================================================================

@app.route("/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    task = task_model.get_task(task_id)
    if task:
        task_model.delete_task(task_id)
        flash(f'Task "{task["subject"]}" deleted.', "info")
    return redirect(url_for("index"))


# =============================================================================
# Route 7: Progress Tracker
# =============================================================================

@app.route("/progress")
def progress():
    completed = progress_model.get_completed()
    summary   = progress_model.get_summary()
    return render_template("progress.html", completed=completed, summary=summary)

# =============================================================================
# Route 8: Analytics / Visual Dashboard
# =============================================================================

@app.route("/analytics")
def analytics():
    """
    Prepares data for 3 Chart.js visualizations:
    1. Bar chart  — daily workload (hours per day from AI schedule)
    2. Pie chart  — completion breakdown
    3. Line chart — urgency forecast (priority score per task over time)
    """
    tasks           = task_model.get_all_tasks()
    completed       = progress_model.get_completed()
    summary         = progress_model.get_summary()

    # --- Chart 1: Daily Workload ---
    # Run the AI scheduler to get the schedule, then sum hours per day
    raw_schedule = {}
    if tasks:
        raw_schedule = SchedulerContext().run(tasks, 4.0)

    workload_labels = []
    workload_data   = []
    for day in sorted(raw_schedule.keys()):
        workload_labels.append(str(day))
        workload_data.append(sum(s["hours"] for s in raw_schedule[day]))

    # --- Chart 2: Completion Pie ---
    completed_subjects = {r["subject"] for r in completed}
    all_subjects       = {t["subject"] for t in tasks}
    done_count         = len(completed_subjects & all_subjects)
    pending_count      = len(all_subjects) - done_count

    # --- Chart 3: Urgency Forecast ---
    # Sort tasks by deadline, show their priority score
    ai_sched = AIScheduler()
    urgency_labels = []
    urgency_data   = []
    for task in sorted(tasks, key=lambda t: t["deadline"]):
        score = ai_sched.calculate_priority_score(task)
        urgency_labels.append(task["subject"])
        urgency_data.append(round(score * 100, 1))   # Convert to percentage

    return render_template(
        "analytics.html",
        workload_labels  = workload_labels,
        workload_data    = workload_data,
        done_count       = done_count,
        pending_count    = pending_count,
        urgency_labels   = urgency_labels,
        urgency_data     = urgency_data,
        summary          = summary,
        total_tasks      = len(tasks),
    )
# =============================================================================
# Route 9: Pomodoro Timer
# =============================================================================

@app.route("/pomodoro")
def pomodoro():
    tasks = task_model.get_all_tasks()
    return render_template("pomodoro.html", tasks=tasks)

@app.route("/pomodoro/log", methods=["POST"])
def log_pomodoro():
    subject = request.form.get("subject")
    hours   = float(request.form.get("hours", 0.42))  # 25 min = 0.42h
    today   = date.today()
    progress_model.mark_complete(subject, today, hours)
    return {"status": "logged"}, 200

# =============================================================================
# Route 10: Adaptive Reschedule
# =============================================================================

@app.route("/reschedule")
def reschedule():
    tasks     = task_model.get_all_tasks()
    completed = progress_model.get_completed()

    if not tasks:
        flash("Add some tasks first before rescheduling.", "info")
        return redirect(url_for("index"))

    available_hours = float(request.args.get("hours", 4.0))

    from scheduler import adaptive_reschedule
    result = adaptive_reschedule(tasks, completed, available_hours)

    # Format schedule dates as strings for template
    formatted_schedule = {
        str(k): v for k, v in result["new_schedule"].items()
    }

    return render_template(
        "reschedule.html",
        schedule        = formatted_schedule,
        changes         = result["changes"],
        warnings        = result["warnings"],
        available_hours = available_hours,
    )
# =============================================================================
# Run the app
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True)