import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.app import (
    get_priority_color,
    display_tasks_with_colors,
    get_due_date_notifications,
    manage_categories
)
from src.tasks import (
    create_task,
    load_tasks,
    save_tasks
)

# Feature 1: Task Categories Management

@pytest.fixture
def mock_categories_file(tmp_path):
    """Fixture for categories file."""
    categories_file = tmp_path / "test_categories.json"
    return str(categories_file)

@pytest.fixture
def mock_categories():
    """Fixture for default categories."""
    return ["Work", "Personal", "School", "Other"]

def test_manage_categories_adds_new_category(monkeypatch):
    """Test that manage_categories adds a new category when requested."""
    # Mock streamlit components
    mock_st = MagicMock()
    mock_st.text_input.return_value = "NewCategory"
    mock_st.button.return_value = True
    monkeypatch.setattr("src.app.st", mock_st)
    
    # Call the function
    categories = manage_categories()
    
    # Verify new category was added
    assert "NewCategory" in categories
    mock_st.text_input.assert_called_once()
    mock_st.button.assert_called_once()

def test_manage_categories_prevents_duplicate_categories(monkeypatch):
    """Test that manage_categories prevents duplicate categories."""
    # Mock streamlit components
    mock_st = MagicMock()
    mock_st.text_input.return_value = "Work"  # Existing category
    mock_st.button.return_value = True
    monkeypatch.setattr("src.app.st", mock_st)
    
    # Call the function
    categories = manage_categories()
    
    # Verify no duplicates
    assert categories.count("Work") == 1
    mock_st.text_input.assert_called_once()
    mock_st.button.assert_called_once()

def test_manage_categories_with_empty_input(monkeypatch):
    """Test that manage_categories handles empty input."""
    # Mock streamlit components
    mock_st = MagicMock()
    mock_st.text_input.return_value = ""  # Empty input
    mock_st.button.return_value = True
    monkeypatch.setattr("src.app.st", mock_st)
    
    # Call the function
    initial_categories = ["Work", "Personal", "School", "Other"]
    categories = manage_categories()
    
    # Verify no changes
    assert set(categories) == set(initial_categories)
    mock_st.text_input.assert_called_once()
    mock_st.button.assert_called_once()

# Feature 2: Task Priority Color Coding

def test_get_priority_color_returns_correct_colors():
    """Test that get_priority_color returns the correct color for each priority."""
    assert get_priority_color("High") == "red"
    assert get_priority_color("Medium") == "orange"
    assert get_priority_color("Low") == "green"
    assert get_priority_color("Invalid") == "black"  # Default for unknown

def test_display_tasks_with_colors_applies_correct_colors(monkeypatch):
    """Test that display_tasks_with_colors applies correct colors to tasks."""
    # Mock streamlit components
    mock_st = MagicMock()
    mock_container = MagicMock()
    mock_columns = [MagicMock(), MagicMock(), MagicMock()]
    
    mock_st.container.return_value.__enter__.return_value = mock_container
    mock_st.columns.return_value = mock_columns
    mock_st.checkbox.return_value = False
    mock_st.button.side_effect = [False, False]  # Edit and Delete buttons
    
    monkeypatch.setattr("src.app.st", mock_st)
    
    # Create test tasks with different priorities
    tasks = [
        {
            "title": "High Priority Task",
            "description": "Description",
            "category": "Work",
            "priority": "High",
            "due_date": "2023-01-01",
            "completed": False,
        },
        {
            "title": "Medium Priority Task",
            "description": "Description",
            "category": "Personal",
            "priority": "Medium",
            "due_date": "2023-01-02",
            "completed": False,
        },
        {
            "title": "Low Priority Task",
            "description": "Description",
            "category": "School",
            "priority": "Low",
            "due_date": "2023-01-03",
            "completed": False,
        },
    ]
    
    # Call the display function
    display_tasks_with_colors(tasks)
    
    # Verify markdown calls for each priority color
    mock_st.markdown.assert_any_call(
        "**Priority:** <span style='color: red'>High</span>",
        unsafe_allow_html=True
    )
    mock_st.markdown.assert_any_call(
        "**Priority:** <span style='color: orange'>Medium</span>",
        unsafe_allow_html=True
    )
    mock_st.markdown.assert_any_call(
        "**Priority:** <span style='color: green'>Low</span>",
        unsafe_allow_html=True
    )

def test_display_tasks_with_colors_handles_empty_list(monkeypatch):
    """Test that display_tasks_with_colors handles empty task list."""
    # Mock streamlit components
    mock_st = MagicMock()
    monkeypatch.setattr("src.app.st", mock_st)
    
    # Call with empty list
    display_tasks_with_colors([])
    
    # Verify info message
    mock_st.info.assert_called_once_with("No tasks to display.")

# Feature 3: Task Due Date Notifications

def test_get_due_date_notifications_returns_correct_notifications():
    """Test that get_due_date_notifications returns correct notifications."""
    today = datetime.now().date()
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    
    tasks = [
        {
            "title": "Overdue Task",
            "due_date": yesterday,
            "completed": False,
        },
        {
            "title": "Due Today Task",
            "due_date": today_str,
            "completed": False,
        },
        {
            "title": "Due Tomorrow Task",
            "due_date": tomorrow,
            "completed": False,
        },
        {
            "title": "Due Next Week Task",
            "due_date": next_week,
            "completed": False,
        },
        {
            "title": "Completed Overdue Task",
            "due_date": yesterday,
            "completed": True,
        },
    ]
    
    notifications = get_due_date_notifications(tasks)
    
    # Should have 3 notifications (overdue, today, tomorrow)
    assert len(notifications) == 3
    
    # Verify notification content
    assert any("overdue" in n.lower() for n in notifications)
    assert any("due today" in n.lower() for n in notifications)
    assert any("due in 1 day" in n.lower() for n in notifications)
    
    # Should not include completed tasks or tasks due more than 3 days away
    assert not any("Completed Overdue Task" in n for n in notifications)
    assert not any("Due Next Week Task" in n for n in notifications)

def test_get_due_date_notifications_handles_invalid_dates():
    """Test that get_due_date_notifications handles invalid date formats."""
    tasks = [
        {
            "title": "Invalid Date Task",
            "due_date": "invalid-date",
            "completed": False,
        },
    ]
    
    notifications = get_due_date_notifications(tasks)
    
    # Should handle invalid date without errors
    assert len(notifications) == 0

def test_get_due_date_notifications_handles_missing_dates():
    """Test that get_due_date_notifications handles missing due dates."""
    tasks = [
        {
            "title": "No Due Date Task",
            "completed": False,
        },
    ]
    
    notifications = get_due_date_notifications(tasks)
    
    # Should handle missing due_date without errors
    assert len(notifications) == 0