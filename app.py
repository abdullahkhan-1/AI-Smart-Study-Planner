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
# Run the app
# =============================================================================

if __name__ == "__main__":
    app.run(debug=True)