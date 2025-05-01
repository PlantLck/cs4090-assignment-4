import pytest
import json
import os
from datetime import datetime, timedelta
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

# Sample task for testing
def create_sample_task():
    """Create a sample task for testing."""
    return {
        "id": 1,
        "title": "Test Task",
        "description": "Test Description",
        "priority": "Medium",
        "category": "Work",
        "due_date": datetime.now().strftime("%Y-%m-%d"),
        "completed": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def test_validate_task():
    """Test validate_task function."""
    # Valid task
    task = create_sample_task()
    assert validate_task(task) is True
    
    # Invalid task (empty title)
    task = create_sample_task()
    task["title"] = ""
    assert validate_task(task) is False
    
    # Invalid task (not a dictionary)
    assert validate_task("not a dictionary") is False
    
    # Invalid task (None)
    assert validate_task(None) is False
    
    # Task with missing properties
    task = {"title": "Missing Props"}
    assert validate_task(task) is True  # Should add default values
    assert "priority" in task
    assert "category" in task
    assert "due_date" in task

def test_create_task():
    """Test create_task function."""
    # Creating a valid task
    task = create_task(
        "Test Task",
        "Test Description",
        "Medium",
        "Work",
        datetime.now().strftime("%Y-%m-%d")
    )
    assert task["title"] == "Test Task"
    assert task["description"] == "Test Description"
    assert task["priority"] == "Medium"
    assert task["category"] == "Work"
    assert task["completed"] is False
    
    # Creating task with empty title
    with pytest.raises(ValueError):
        create_task("", "Empty Title", "Low", "Personal", "2023-01-01")
    
    # Creating task with invalid priority
    task = create_task(
        "Invalid Priority",
        "Description",
        "InvalidPriority",
        "Work",
        "2023-01-01"
    )
    assert task["priority"] == "Low"  # Should default to Low
    
    # Creating task with invalid date
    task = create_task(
        "Invalid Date",
        "Description",
        "Medium",
        "Work",
        "invalid-date"
    )
    # Should use today's date
    assert task["due_date"] == datetime.now().strftime("%Y-%m-%d")

def test_load_tasks(tmp_path):
    """Test load_tasks function."""
    # Create a temporary file with sample tasks
    file_path = tmp_path / "test_tasks.json"
    tasks = [create_sample_task()]
    with open(file_path, "w") as f:
        json.dump(tasks, f)
    
    # Load tasks from file
    loaded_tasks = load_tasks(str(file_path))
    assert loaded_tasks == tasks
    
    # Load from non-existent file
    non_existent = tmp_path / "non_existent.json"
    assert load_tasks(str(non_existent)) == []
    
    # Load from corrupt file
    corrupt_file = tmp_path / "corrupt.json"
    with open(corrupt_file, "w") as f:
        f.write("not valid json")
    assert load_tasks(str(corrupt_file)) == []

def test_save_tasks(tmp_path):
    """Test save_tasks function."""
    # Save tasks to file
    file_path = tmp_path / "save_test.json"
    tasks = [create_sample_task()]
    save_tasks(tasks, str(file_path))
    
    # Verify file was created and contains correct data
    assert file_path.exists()
    with open(file_path, "r") as f:
        loaded = json.load(f)
    assert loaded == tasks

def test_generate_unique_id():
    """Test generate_unique_id function."""
    # Empty task list
    assert generate_unique_id([]) == 1
    
    # Task list with IDs
    tasks = [
        {"id": 1, "title": "Task 1"},
        {"id": 2, "title": "Task 2"},
        {"id": 5, "title": "Task 5"},
    ]
    assert generate_unique_id(tasks) == 6  # Max ID + 1
    
    # Task list with some missing IDs
    tasks = [
        {"title": "No ID 1"},
        {"id": 10, "title": "Task 10"},
        {"title": "No ID 2"},
    ]
    assert generate_unique_id(tasks) == 11  # Max ID + 1

def test_filter_tasks_by_priority():
    """Test filter_tasks_by_priority function."""
    tasks = [
        {"id": 1, "title": "High Task", "priority": "High"},
        {"id": 2, "title": "Medium Task", "priority": "Medium"},
        {"id": 3, "title": "Low Task", "priority": "Low"},
        {"id": 4, "title": "Another High", "priority": "High"},
    ]
    
    # Filter high priority
    high_tasks = filter_tasks_by_priority(tasks, "High")
    assert len(high_tasks) == 2
    assert all(task["priority"] == "High" for task in high_tasks)
    
    # Filter medium priority
    medium_tasks = filter_tasks_by_priority(tasks, "Medium")
    assert len(medium_tasks) == 1
    assert medium_tasks[0]["priority"] == "Medium"
    
    # Filter non-existent priority
    none_tasks = filter_tasks_by_priority(tasks, "NonExistent")
    assert len(none_tasks) == 0

def test_filter_tasks_by_category():
    """Test filter_tasks_by_category function."""
    tasks = [
        {"id": 1, "title": "Work Task 1", "category": "Work"},
        {"id": 2, "title": "Personal Task", "category": "Personal"},
        {"id": 3, "title": "Work Task 2", "category": "Work"},
        {"id": 4, "title": "School Task", "category": "School"},
    ]
    
    # Filter work category
    work_tasks = filter_tasks_by_category(tasks, "Work")
    assert len(work_tasks) == 2
    assert all(task["category"] == "Work" for task in work_tasks)
    
    # Filter personal category
    personal_tasks = filter_tasks_by_category(tasks, "Personal")
    assert len(personal_tasks) == 1
    assert personal_tasks[0]["category"] == "Personal"
    
    # Filter non-existent category
    none_tasks = filter_tasks_by_category(tasks, "NonExistent")
    assert len(none_tasks) == 0

def test_filter_tasks_by_completion():
    """Test filter_tasks_by_completion function."""
    tasks = [
        {"id": 1, "title": "Completed Task 1", "completed": True},
        {"id": 2, "title": "Incomplete Task 1", "completed": False},
        {"id": 3, "title": "Completed Task 2", "completed": True},
        {"id": 4, "title": "Incomplete Task 2", "completed": False},
        {"id": 5, "title": "No Completion Status"},
    ]
    
    # Filter completed tasks
    completed = filter_tasks_by_completion(tasks, True)
    assert len(completed) == 2
    assert all(task["completed"] is True for task in completed)
    
    # Filter incomplete tasks
    incomplete = filter_tasks_by_completion(tasks, False)
    assert len(incomplete) == 3  # Including the one without status
    
    # Edge case: empty list
    assert filter_tasks_by_completion([], True) == []

def test_search_tasks():
    """Test search_tasks function."""
    tasks = [
        {"id": 1, "title": "Search Target", "description": "Find this task"},
        {"id": 2, "title": "Another Task", "description": "Not a target"},
        {"id": 3, "title": "Third Task", "description": "Contains search term"},
        {"id": 4, "title": "Fourth Task", "description": ""},
    ]
    
    # Search by title
    results = search_tasks(tasks, "Search")
    assert len(results) == 1
    assert results[0]["id"] == 1
    
    # Search by description
    results = search_tasks(tasks, "search term")
    assert len(results) == 1
    assert results[0]["id"] == 3
    
    # Search with no matches
    results = search_tasks(tasks, "no matches")
    assert len(results) == 0
    
    # Search with empty query
    results = search_tasks(tasks, "")
    assert len(results) == 0
    
    # Search with None query
    results = search_tasks(tasks, None)
    assert len(results) == 0

def test_get_overdue_tasks():
    """Test get_overdue_tasks function."""
    today = datetime.now().date()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    tasks = [
        {"id": 1, "title": "Overdue Incomplete", "due_date": yesterday, "completed": False},
        {"id": 2, "title": "Overdue Completed", "due_date": yesterday, "completed": True},
        {"id": 3, "title": "Future Incomplete", "due_date": tomorrow, "completed": False},
        {"id": 4, "title": "Future Completed", "due_date": tomorrow, "completed": True},
    ]
    
    # Get overdue tasks
    overdue = get_overdue_tasks(tasks)
    assert len(overdue) == 1
    assert overdue[0]["id"] == 1
    
    # Test with invalid date
    with pytest.raises(ValueError):
        invalid_tasks = [
            {"id": 1, "title": "Invalid Date", "due_date": "invalid-date", "completed": False}
        ]
        get_overdue_tasks(invalid_tasks)
    
    # Test with missing due_date
    with pytest.raises(ValueError):
        missing_date_tasks = [
            {"id": 1, "title": "Missing Date", "completed": False}
        ]
        get_overdue_tasks(missing_date_tasks)