import pytest
import json
import os
from datetime import datetime, timedelta
import random
import string
from hypothesis import given, strategies as st, settings, example
from src.tasks import (
    validate_task,
    create_task,
    load_tasks,
    save_tasks,
    generate_unique_id,
    filter_tasks_by_priority,
    filter_tasks_by_category,
    filter_tasks_by_completion,
    search_tasks,
    get_overdue_tasks,
)

# Define strategies for task properties
task_titles = st.text(min_size=1, max_size=50)
task_descriptions = st.text(max_size=200)
task_priorities = st.sampled_from(["High", "Medium", "Low"])
task_categories = st.sampled_from(["Work", "Personal", "School", "Other"])
task_completed = st.booleans()

# Strategy for valid ISO format dates (YYYY-MM-DD)
valid_dates = st.dates().map(lambda d: d.strftime("%Y-%m-%d"))

# Strategy for complete tasks
@st.composite
def task_strategy(draw):
    """Generate a random task with all required properties."""
    return {
        "id": draw(st.integers(min_value=1, max_value=1000)),
        "title": draw(task_titles),
        "description": draw(task_descriptions),
        "priority": draw(task_priorities),
        "category": draw(task_categories),
        "due_date": draw(valid_dates),
        "completed": draw(task_completed),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# Strategy for generating a list of tasks
task_lists = st.lists(task_strategy(), max_size=10)

@pytest.fixture
def temp_tasks_file(tmp_path):
    """Create a temporary file for tasks."""
    file_path = tmp_path / "test_tasks.json"
    return str(file_path)

@given(task=task_strategy())
@settings(max_examples=50)
def test_validate_task_property(task):
    """Test that validate_task properly validates any task."""
    # Validate the task
    is_valid = validate_task(task)
    
    # If the task has a title, it should be valid
    if task["title"]:
        assert is_valid is True
    else:
        assert is_valid is False

@given(
    title=task_titles,
    description=task_descriptions,
    priority=task_priorities,
    category=task_categories,
    due_date=valid_dates
)
@settings(max_examples=50)
def test_create_task_property(title, description, priority, category, due_date):
    """Test that create_task creates valid tasks with any valid inputs."""
    # Title can't be empty for create_task
    if not title:
        with pytest.raises(ValueError):
            create_task(title, description, priority, category, due_date)
    else:
        task = create_task(title, description, priority, category, due_date)
        
        # Verify task was created with correct properties
        assert task["title"] == title
        assert task["description"] == description
        assert task["priority"] == priority
        assert task["category"] == category
        assert task["due_date"] == due_date
        assert task["completed"] is False
        assert "created_at" in task

@given(tasks=task_lists)
@settings(max_examples=30)
def test_generate_unique_id_property(tasks):
    """Test that generate_unique_id always generates a unique ID."""
    if not tasks:
        # For empty list, should return 1
        assert generate_unique_id(tasks) == 1
    else:
        # Should be greater than the maximum ID in the list
        max_id = max(task.get("id", 0) for task in tasks)
        assert generate_unique_id(tasks) == max_id + 1

@given(tasks=task_lists, priority=task_priorities)
@settings(max_examples=20)
def test_filter_tasks_by_priority_property(tasks, priority):
    """Test that filter_tasks_by_priority correctly filters any task list by any priority."""
    filtered_tasks = filter_tasks_by_priority(tasks, priority)
    
    # All filtered tasks should have the specified priority
    assert all(task["priority"] == priority for task in filtered_tasks)
    
    # All tasks with the specified priority should be in the filtered list
    assert len(filtered_tasks) == len([task for task in tasks if task["priority"] == priority])

@given(tasks=task_lists, category=task_categories)
@settings(max_examples=20)
def test_filter_tasks_by_category_property(tasks, category):
    """Test that filter_tasks_by_category correctly filters any task list by any category."""
    filtered_tasks = filter_tasks_by_category(tasks, category)
    
    # All filtered tasks should have the specified category
    assert all(task["category"] == category for task in filtered_tasks)
    
    # All tasks with the specified category should be in the filtered list
    assert len(filtered_tasks) == len([task for task in tasks if task["category"] == category])

@given(tasks=task_lists, completed=task_completed)
@settings(max_examples=20)
def test_filter_tasks_by_completion_property(tasks, completed):
    """Test that filter_tasks_by_completion correctly filters any task list by completion status."""
    filtered_tasks = filter_tasks_by_completion(tasks, completed)
    
    # All filtered tasks should have the specified completion status
    assert all(task.get("completed", False) == completed for task in filtered_tasks)
    
    # All tasks with the specified completion status should be in the filtered list
    assert len(filtered_tasks) == len([task for task in tasks if task.get("completed", False) == completed])

@given(tasks=task_lists, query=task_titles)
@settings(max_examples=20)
def test_search_tasks_property(tasks, query):
    """Test that search_tasks correctly finds tasks containing the query in title or description."""
    if not query:
        # Empty query should return empty list
        assert search_tasks(tasks, query) == []
    else:
        # Modify some tasks to include the query
        for i, task in enumerate(tasks):
            if i % 3 == 0:  # Modify every third task
                task["title"] = f"{query} {task['title']}"
            elif i % 3 == 1:  # Modify every third task, offset by 1
                task["description"] = f"{query} {task['description']}"
        
        search_results = search_tasks(tasks, query)
        
        # All search results should contain the query in title or description
        assert all(
            query.lower() in task.get("title", "").lower() or 
            query.lower() in task.get("description", "").lower() 
            for task in search_results
        )
        
        # All tasks containing the query should be in the search results
        for task in tasks:
            if (query.lower() in task.get("title", "").lower() or 
                query.lower() in task.get("description", "").lower()):
                assert task in search_results

@given(tasks=task_lists)
@settings(max_examples=20)
def test_save_and_load_tasks_property(tasks, temp_tasks_file):
    """Test that saving and loading tasks preserves all task data."""
    # Save tasks to file
    save_tasks(tasks, temp_tasks_file)
    
    # Load tasks from file
    loaded_tasks = load_tasks(temp_tasks_file)
    
    # Loaded tasks should be identical to original tasks
    assert loaded_tasks == tasks

@given(tasks=task_lists)
@settings(max_examples=20)
def test_get_overdue_tasks_property(tasks):
    """Test that get_overdue_tasks correctly identifies overdue tasks."""
    # Modify tasks to set some as overdue
    today = datetime.now().date()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    for i, task in enumerate(tasks):
        task["completed"] = i % 2 == 0  # Every other task is completed
        task["due_date"] = yesterday if i % 3 == 0 else tomorrow  # Every third task is overdue
    
    # Get overdue tasks
    try:
        overdue_tasks = get_overdue_tasks(tasks)
        
        # All overdue tasks should have due_date before today and not be completed
        for task in overdue_tasks:
            task_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
            assert task_date < today
            assert task.get("completed", False) is False
        
        # All tasks that are overdue and not completed should be in the list
        expected_overdue = [
            task for task in tasks 
            if "due_date" in task and 
               datetime.strptime(task["due_date"], "%Y-%m-%d").date() < today and
               not task.get("completed", False)
        ]
        assert set(task["id"] for task in overdue_tasks) == set(task["id"] for task in expected_overdue)
    except ValueError:
        # If we get a ValueError, at least one task is missing due_date
        assert any("due_date" not in task for task in tasks)