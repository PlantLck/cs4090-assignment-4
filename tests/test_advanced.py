import pytest
import json
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.tasks import (
    validate_task,
    create_task,
    filter_tasks_by_priority,
    filter_tasks_by_category,
    get_overdue_tasks
)
from src.app import (
    get_priority_color,
    display_tasks_with_colors,
    get_due_date_notifications
)

# Parameterized tests for task priorities
@pytest.mark.parametrize(
    "priority,expected_color", 
    [
        ("High", "red"),
        ("Medium", "orange"),
        ("Low", "green"),
        ("Invalid", "black"),
        (None, "black"),
    ]
)
def test_get_priority_color_parametrized(priority, expected_color):
    """Test priority color mapping for different priority values."""
    assert get_priority_color(priority) == expected_color

# Parameterized tests for task filtering
@pytest.mark.parametrize(
    "priority,expected_count", 
    [
        ("High", 1),
        ("Medium", 1),
        ("Low", 1),
        ("NonExistent", 0),
    ]
)
def test_filter_tasks_by_priority_parametrized(priority, expected_count):
    """Test filtering tasks by different priorities."""
    # Sample tasks with different priorities
    tasks = [
        {"id": 1, "title": "Task 1", "priority": "High"},
        {"id": 2, "title": "Task 2", "priority": "Medium"},
        {"id": 3, "title": "Task 3", "priority": "Low"},
    ]
    
    filtered_tasks = filter_tasks_by_priority(tasks, priority)
    assert len(filtered_tasks) == expected_count

# Parameterized tests for task categories
@pytest.mark.parametrize(
    "category,expected_count", 
    [
        ("Work", 2),
        ("Personal", 1),
        ("School", 0),
        ("NonExistent", 0),
    ]
)
def test_filter_tasks_by_category_parametrized(category, expected_count):
    """Test filtering tasks by different categories."""
    # Sample tasks with different categories
    tasks = [
        {"id": 1, "title": "Task 1", "category": "Work"},
        {"id": 2, "title": "Task 2", "category": "Personal"},
        {"id": 3, "title": "Task 3", "category": "Work"},
    ]
    
    filtered_tasks = filter_tasks_by_category(tasks, category)
    assert len(filtered_tasks) == expected_count

# Parameterized tests for task due dates
@pytest.mark.parametrize(
    "days_offset,expected_overdue", 
    [
        (-5, True),   # 5 days ago
        (-1, True),   # Yesterday
        (0, False),   # Today
        (1, False),   # Tomorrow
        (5, False),   # 5 days in future
    ]
)
def test_task_due_date_parametrized(days_offset, expected_overdue):
    """Test overdue task detection with different due dates."""
    today = datetime.now().date()
    due_date = (today + timedelta(days=days_offset)).strftime("%Y-%m-%d")
    
    # Create a task with the specified due date
    task = {
        "id": 1,
        "title": "Test Task",
        "description": "Test Description",
        "priority": "High",
        "category": "Work",
        "due_date": due_date,
        "completed": False,
    }
    
    # Get overdue tasks
    overdue_tasks = get_overdue_tasks([task])
    
    if expected_overdue:
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0]["id"] == 1
    else:
        assert len(overdue_tasks) == 0

# Fixture for mock notification tasks
@pytest.fixture
def notification_tasks():
    """Fixture for tasks with various due dates for testing notifications."""
    today = datetime.now().date()
    return [
        {
            "title": "Overdue Task",
            "due_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "completed": False,
        },
        {
            "title": "Due Today Task",
            "due_date": today.strftime("%Y-%m-%d"),
            "completed": False,
        },
        {
            "title": "Due Soon Task",
            "due_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "completed": False,
        },
        {
            "title": "Future Task",
            "due_date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "completed": False,
        },
        {
            "title": "Completed Overdue Task",
            "due_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
            "completed": True,
        },
    ]

# Test notifications with fixture
def test_get_due_date_notifications_with_fixture(notification_tasks):
    """Test notification generation with fixture data."""
    notifications = get_due_date_notifications(notification_tasks)
    
    # Should have 3 notifications (overdue, today, and due soon)
    assert len(notifications) == 3
    
    # Verify notification content
    assert any("overdue" in notification.lower() for notification in notifications)
    assert any("due today" in notification.lower() for notification in notifications)
    assert any("due in 2 days" in notification.lower() for notification in notifications)
    
    # Verify no notifications for future task or completed task
    assert not any("Future Task" in notification for notification in notifications)
    assert not any("Completed Overdue Task" in notification for notification in notifications)

# Test with mock streamlit
@pytest.fixture
def mock_streamlit():
    """Fixture for mocking streamlit components."""
    with patch("src.app.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_st.checkbox.return_value = False
        mock_st.button.return_value = False
        yield mock_st

# Test display tasks with mock
def test_display_tasks_with_colors_mock(mock_streamlit):
    """Test task display with streamlit mocking."""
    tasks = [
        {
            "id": 1,
            "title": "High Priority Task",
            "description": "Important task",
            "priority": "High",
            "category": "Work",
            "due_date": datetime.now().strftime("%Y-%m-%d"),
            "completed": False,
        },
        {
            "id": 2,
            "title": "Medium Priority Task",
            "description": "Medium importance",
            "priority": "Medium",
            "category": "Personal",
            "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "completed": False,
        },
    ]
    
    display_tasks_with_colors(tasks)
    
    # Verify checkbox calls
    mock_streamlit.checkbox.assert_any_call(
        "High Priority Task",
        value=False,
        key=f"task_0_completed"
    )
    
    # Verify markdown calls for priority colors
    mock_streamlit.markdown.assert_any_call(
        "**Priority:** <span style='color: red'>High</span>",
        unsafe_allow_html=True
    )
    mock_streamlit.markdown.assert_any_call(
        "**Priority:** <span style='color: orange'>Medium</span>",
        unsafe_allow_html=True
    )

# Test validate_task with different inputs
@pytest.mark.parametrize(
    "input_task,expected_valid", 
    [
        ({"title": "Valid Task"}, True),
        ({"title": ""}, False),
        ({"description": "No Title"}, False),
        ({"title": "Invalid Priority", "priority": "Urgent"}, True),  # Priority will be fixed to "Low"
        ({"title": "Invalid Date", "due_date": "invalid-date"}, True),  # Date will be fixed
        ({"title": "Complete", "completed": True}, True),
        (123, False),  # Not a dictionary
        (None, False),  # None input
    ]
)
def test_validate_task_parametrized(input_task, expected_valid):
    """Test task validation with different inputs."""
    if isinstance(input_task, dict):
        result = validate_task(input_task)
        assert result == expected_valid
        
        if result:
            # Verify all required properties are present
            assert all(key in input_task for key in [
                "id", "title", "description", "priority", 
                "category", "due_date", "completed", "created_at"
            ])
            
            # Verify priority is valid
            assert input_task["priority"] in ["High", "Medium", "Low"]
            
            # Verify due date is valid
            try:
                datetime.strptime(input_task["due_date"], "%Y-%m-%d")
            except ValueError:
                assert False, "Due date is not in valid format"
    else:
        assert validate_task(input_task) == expected_valid