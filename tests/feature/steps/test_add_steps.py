from pytest_bdd import scenarios, given, when, then, parsers
import pytest
from datetime import datetime, timedelta
from src.tasks import (
    create_task, 
    load_tasks, 
    save_tasks, 
    generate_unique_id
)

# Load scenarios from feature files
scenarios('../add_task.feature')

# Fixtures
@pytest.fixture
def context():
    """Fixture to share data between steps."""
    return {}

@pytest.fixture
def tasks_file(tmp_path):
    """Provide a temporary tasks file path."""
    return str(tmp_path / "test_tasks.json")

@pytest.fixture
def categories_file(tmp_path):
    """Provide a temporary categories file path."""
    return str(tmp_path / "test_categories.json")

# Given steps
@given("I have an empty task list")
def empty_task_list(context, tasks_file, monkeypatch):
    """Create an empty task list."""
    context["tasks"] = []
    save_tasks(context["tasks"], tasks_file)
    
    # Monkey patch load_tasks and save_tasks to use our temp file
    monkeypatch.setattr("src.tasks.load_tasks", lambda file_path=None: load_tasks(tasks_file))
    monkeypatch.setattr("src.tasks.save_tasks", lambda tasks, file_path=None: save_tasks(tasks, tasks_file))

@given(parsers.parse('I have a task with title "{title}" and due date "{due_date}"'))
def task_with_title_and_due_date(context, title, due_date, tasks_file, monkeypatch):
    """Create a task with specified title and due date."""
    task = create_task(
        title=title,
        description="Test description",
        priority="Medium",
        category="Work",
        due_date=due_date
    )
    task["id"] = 1
    context["tasks"] = [task]
    save_tasks(context["tasks"], tasks_file)
    
    # Monkey patch load_tasks and save_tasks to use our temp file
    monkeypatch.setattr("src.tasks.load_tasks", lambda file_path=None: load_tasks(tasks_file))
    monkeypatch.setattr("src.tasks.save_tasks", lambda tasks, file_path=None: save_tasks(tasks, tasks_file))

@given(parsers.parse('I have a task with priority "{priority}"'))
def task_with_priority(context, priority, tasks_file, monkeypatch):
    """Create a task with specified priority."""
    task = create_task(
        title="Test Task",
        description="Test description",
        priority=priority,
        category="Work",
        due_date=datetime.now().strftime("%Y-%m-%d")
    )
    task["id"] = 1
    context["tasks"] = [task]
    save_tasks(context["tasks"], tasks_file)
    
    # Monkey patch load_tasks and save_tasks to use our temp file
    monkeypatch.setattr("src.tasks.load_tasks", lambda file_path=None: load_tasks(tasks_file))
    monkeypatch.setattr("src.tasks.save_tasks", lambda tasks, file_path=None: save_tasks(tasks, tasks_file))

# When steps
@when(parsers.parse('I add a new task with title "{title}"'))
def add_new_task(context, title, tasks_file):
    """Add a new task with specified title."""
    task = create_task(
        title=title,
        description="Test description",
        priority="Medium",
        category="Work",
        due_date=datetime.now().strftime("%Y-%m-%d")
    )
    task["id"] = generate_unique_id(context["tasks"])
    context["tasks"].append(task)
    save_tasks(context["tasks"], tasks_file)

@when("I mark the task as completed")
def mark_task_completed(context, tasks_file):
    """Mark the first task as completed."""
    context["tasks"][0]["completed"] = True
    save_tasks(context["tasks"], tasks_file)

@when(parsers.parse('I add a new category "{category}"'))
def add_new_category(context, category, categories_file, monkeypatch):
    """Add a new category."""
    # Load existing categories or create default list
    try:
        with open(categories_file, 'r') as f:
            import json
            categories = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        categories = ["Work", "Personal", "School", "Other"]
    
    # Add the new category if it doesn't exist
    if category not in categories:
        categories.append(category)
    
    # Save categories
    with open(categories_file, 'w') as f:
        json.dump(categories, f)
    
    context["categories"] = categories

# Then steps
@then(parsers.parse('the task list should contain "{count}" tasks'))
def verify_task_count(context, count, tasks_file):
    """Verify the task list contains the expected number of tasks."""
    tasks = load_tasks(tasks_file)
    assert len(tasks) == int(count)

@then("the task should be marked as completed")
def verify_task_completed(context, tasks_file):
    """Verify the first task is marked as completed."""
    tasks = load_tasks(tasks_file)
    assert tasks[0]["completed"] is True

@then(parsers.parse('the task should be displayed with "{color}" color'))
def verify_task_color(context, color):
    """Verify the task would be displayed with the expected color."""
    from src.app import get_priority_color
    
    tasks = context["tasks"]
    priority = tasks[0]["priority"]
    actual_color = get_priority_color(priority)
    assert actual_color == color

@then(parsers.parse('the task should be in the "{status}" section'))
def verify_task_status(context, status):
    """Verify the task has the expected status based on due date."""
    task = context["tasks"][0]
    today = datetime.now().date()
    task_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
    
    if status == "overdue":
        assert task_date < today
    elif status == "today":
        assert task_date == today
    elif status == "upcoming":
        assert task_date > today and task_date <= today + timedelta(days=3)
    elif status == "future":
        assert task_date > today + timedelta(days=3)

@then(parsers.parse('the category list should contain "{category}"'))
def verify_category_exists(context, category):
    """Verify the category list contains the expected category."""
    assert "categories" in context
    assert category in context["categories"]