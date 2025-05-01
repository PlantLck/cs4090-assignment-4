import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import os
import sys
import json
from typing import Dict, List, Optional

# Add the project root to Python path if not already there
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.tasks import (
    load_tasks,
    save_tasks,
    filter_tasks_by_priority,
    filter_tasks_by_category,
    create_task,
    generate_unique_id,
    validate_task,
)
import subprocess

# Constants for category management
CATEGORIES_FILE = "categories.json"
DEFAULT_CATEGORIES = ["Work", "Personal", "School", "Other"]

# Color mapping for priorities
PRIORITY_COLORS = {"High": "red", "Medium": "orange", "Low": "green"}


def load_categories():
    """
    Load categories from file or return default categories.
    
    Returns:
        list: List of category strings
    """
    try:
        with open(CATEGORIES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT_CATEGORIES.copy()


def save_categories(categories):
    """
    Save categories to file.
    
    Args:
        categories (list): List of category strings
    """
    try:
        with open(CATEGORIES_FILE, "w") as f:
            json.dump(categories, f, indent=2)
    except IOError as e:
        st.error(f"Error saving categories: {e}")


def get_categories() -> List[str]:
    """
    Get list of available task categories.
    
    Returns:
        list: List of category strings
    """
    if "categories" not in st.session_state:
        st.session_state["categories"] = load_categories()
    return st.session_state["categories"]


def add_category(new_category: str) -> None:
    """
    Add a new category to the list of available categories.
    
    Args:
        new_category (str): New category name to add
    """
    if "categories" not in st.session_state:
        st.session_state["categories"] = load_categories()
    
    if new_category and new_category not in st.session_state["categories"]:
        st.session_state["categories"].append(new_category)
        save_categories(st.session_state["categories"])


def manage_categories():
    """
    Manage task categories.
    
    Returns:
        list: Updated list of categories
    """
    categories = load_categories()

    # Add new category
    new_category = st.text_input("Add New Category")
    if st.button("Add Category") and new_category:
        if new_category not in categories:
            categories.append(new_category)
            save_categories(categories)
            st.success(f"Added new category: {new_category}")

    return categories


def get_priority_color(priority: str) -> str:
    """
    Get color based on task priority.
    
    Args:
        priority (str): Task priority (High, Medium, Low)
        
    Returns:
        str: Color string for the priority
    """
    colors = {
        "High": "red",
        "Medium": "orange",
        "Low": "green",
    }
    return colors.get(priority, "black")  # Black for unknown priority


def filter_tasks(tasks, show_completed=False, category=None, priority=None):
    """
    Filter tasks based on completion status, category, and priority.

    Args:
        tasks (list): List of tasks to filter
        show_completed (bool): Whether to show completed tasks
        category (str): Category to filter by
        priority (str): Priority to filter by

    Returns:
        list: Filtered list of tasks
    """
    filtered_tasks = tasks

    # Filter by completion status
    if not show_completed:
        filtered_tasks = [
            task for task in filtered_tasks if not task.get("completed", False)
        ]

    # Filter by category
    if category and category != "All":
        filtered_tasks = [
            task for task in filtered_tasks if task.get("category") == category
        ]

    # Filter by priority
    if priority and priority != "All":
        filtered_tasks = [
            task for task in filtered_tasks if task.get("priority") == priority
        ]

    return filtered_tasks


def display_tasks_with_colors(tasks):
    """
    Display tasks with color coding based on priority.
    
    Args:
        tasks (list): List of task dictionaries to display
    """
    if not tasks:
        st.info("No tasks to display.")
        return

    for i, task in enumerate(tasks):
        with st.container():
            cols = st.columns([2, 2, 1])

            # Column 1: Task title and completion status
            with cols[0]:
                completed = st.checkbox(
                    task.get("title", ""),
                    value=task.get("completed", False),
                    key=f"task_{i}_completed",
                )
                if completed != task.get("completed", False):
                    task["completed"] = completed
                    st.rerun()

            # Column 2: Task details
            with cols[1]:
                priority_color = get_priority_color(task.get("priority", "Low"))
                st.markdown(f"_{task.get('description', '')}_")
                st.markdown(f"**Category:** {task.get('category', '')}")
                st.markdown(
                    f"**Priority:** <span style='color: {priority_color}'>{task.get('priority', '')}</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Due Date:** {task.get('due_date', '')}")

            # Column 3: Action buttons
            with cols[2]:
                if st.button("Edit", key=f"edit_{i}"):
                    st.session_state.editing_task = task
                    st.rerun()
                if st.button("Delete", key=f"delete_{i}"):
                    tasks.remove(task)
                    st.rerun()

            st.markdown("---")  # Add a separator between tasks


def get_due_date_notifications(tasks: List[Dict]) -> List[str]:
    """
    Generate notifications for tasks based on due dates.
    
    Args:
        tasks (list): List of task dictionaries
        
    Returns:
        list: List of notification strings
    """
    notifications = []
    today = datetime.now().date()

    for task in tasks:
        if task.get("completed", False):
            continue

        due_date = task.get("due_date")
        if not due_date:
            continue

        try:
            due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        except ValueError:
            continue

        days_until_due = (due_date - today).days

        if days_until_due < 0:
            notifications.append(
                f"⚠️ Task '{task.get('title', '')}' is overdue by {abs(days_until_due)} days!"
            )
        elif days_until_due == 0:
            notifications.append(f"📅 Task '{task.get('title', '')}' is due today!")
        elif days_until_due <= 3:
            if days_until_due == 1:
                notifications.append(f"⏰ Task '{task.get('title', '')}' is due in {days_until_due} day.")
            else:
                notifications.append(f"⏰ Task '{task.get('title', '')}' is due in {days_until_due} days.")

    return notifications


def display_notifications(tasks):
    """
    Display task notifications.
    
    Args:
        tasks (list): List of task dictionaries
    """
    notifications = get_due_date_notifications(tasks)
    if notifications:
        st.markdown("### 🔔 Notifications")
        for notification in notifications:
            st.markdown(notification)


def run_tests():
    """
    Run pytest and return test results and coverage.
    
    Returns:
        dict: Dictionary containing test results, coverage, and success status
    """
    try:
        # Set up environment with project root in PYTHONPATH
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = os.environ.copy()
        env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
        
        # Run pytest with coverage
        result = subprocess.run(
            ["python", "-m", "pytest", "--cov=src", "tests/"],
            capture_output=True,
            text=True,
            env=env,
        )

        # Split output into test results and coverage
        output = result.stdout + result.stderr
        lines = output.split("\n")

        # Find where coverage report starts
        coverage_start = -1
        for i, line in enumerate(lines):
            if "TOTAL" in line:
                coverage_start = i
                break

        # Extract test results and coverage
        test_results = (
            "\n".join(lines[:coverage_start]) if coverage_start > 0 else output
        )
        coverage = lines[coverage_start] if coverage_start >= 0 else None

        # Format coverage line if it exists
        if coverage:
            coverage = coverage.replace("TOTAL", "TOTAL ")

        return {
            "test_results": test_results,
            "coverage": coverage,
            "success": result.returncode == 0,
        }
    except Exception as e:
        return {
            "test_results": f"Test execution failed: {str(e)}",
            "coverage": None,
            "success": False,
        }


def run_bdd_tests():
    """
    Run BDD tests and return the results.
    
    Returns:
        str: BDD test results output
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    try:
        result = subprocess.run(
            ["pytest", "tests/test_bdd.py", "-v"],
            capture_output=True,
            text=True,
            env=env,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_output = e.output if e.output else "BDD test execution failed"
        return f"{error_output}"


def run_property_tests():
    """
    Run property-based tests and return the results.
    
    Returns:
        str: Property test results output
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")

    try:
        result = subprocess.run(
            ["pytest", "tests/test_property.py", "-v"],
            capture_output=True,
            text=True,
            env=env,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        error_output = e.output if e.output else "Property test execution failed"
        return f"{error_output}"


def task_creation_form(editing_task=None):
    """
    Create a form for adding or editing tasks.
    
    Args:
        editing_task (dict, optional): Task to edit, if in editing mode
        
    Returns:
        dict: Task dictionary if submitted, None otherwise
    """
    with st.form("task_form"):
        st.subheader("✏️ Task Form")

        # Get existing values if editing
        title = editing_task.get("title", "") if editing_task else ""
        description = editing_task.get("description", "") if editing_task else ""
        category = editing_task.get("category", "Work") if editing_task else "Work"
        priority = editing_task.get("priority", "Medium") if editing_task else "Medium"
        
        try:
            due_date_str = editing_task.get("due_date", datetime.now().strftime("%Y-%m-%d")) if editing_task else datetime.now().strftime("%Y-%m-%d")
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            due_date = datetime.now().date()

        # Form fields
        title = st.text_input("Title*", value=title, placeholder="Enter task title")
        description = st.text_area(
            "Description", value=description, placeholder="Enter task description"
        )
        
        # Use dynamically loaded categories
        categories = get_categories()
        category_index = categories.index(category) if category in categories else 0
        category = st.selectbox(
            "Category",
            categories,
            index=category_index,
        )
        
        priority = st.selectbox(
            "Priority",
            ["High", "Medium", "Low"],
            index=["High", "Medium", "Low"].index(priority),
        )
        due_date = st.date_input("Due Date", value=due_date)

        # Submit button
        submitted = st.form_submit_button("Submit")

        if submitted and title:
            task = {
                "title": title,
                "description": description,
                "category": category,
                "priority": priority,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "completed": editing_task.get("completed", False) if editing_task else False,
                "id": editing_task.get("id") if editing_task else None,
                "created_at": editing_task.get("created_at") if editing_task else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            return task
        return None


def check_overdue_tasks(tasks: List[Dict]) -> None:
    """
    Check for overdue tasks and display notifications.
    
    Args:
        tasks (list): List of task dictionaries
    """
    today = datetime.now().date()

    for task in tasks:
        if task.get("completed", False):
            continue

        try:
            due_date = datetime.strptime(task.get("due_date", ""), "%Y-%m-%d").date()
            days_until_due = (due_date - today).days

            if days_until_due < 0:
                st.error(
                    f"⚠️ Task '{task['title']}' is overdue by {abs(days_until_due)} days!"
                )
            elif days_until_due == 0:
                st.warning(f"⏰ Task '{task['title']}' is due today!")
            elif days_until_due <= 3:
                st.info(f"📅 Task '{task['title']}' is due in {days_until_due} days.")
        except (ValueError, TypeError):
            # Skip tasks with invalid dates
            continue


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Task Manager", layout="wide")
    st.title("📋 Task Manager")

    # Initialize session state
    if "tasks" not in st.session_state:
        st.session_state.tasks = load_tasks()

    # Task creation/editing form
    st.header("📝 Tasks")
    
    if "editing_task" in st.session_state:
        edited_task = task_creation_form(st.session_state.editing_task)
        if edited_task:
            # Find and update the existing task
            for i, task in enumerate(st.session_state.tasks):
                if task.get("id") == edited_task.get("id"):
                    st.session_state.tasks[i] = edited_task
                    break
            # Clear editing state
            del st.session_state.editing_task
            # Save tasks
            save_tasks(st.session_state.tasks)
            st.success("Task updated successfully!")
            st.rerun()
    else:
        new_task = task_creation_form()
        if new_task:
            # Assign unique ID for new task
            new_task["id"] = generate_unique_id(st.session_state.tasks)
            st.session_state.tasks.append(new_task)
            # Save tasks
            save_tasks(st.session_state.tasks)
            st.success("Task added successfully!")
            st.rerun()

    # Task filtering
    filter_cols = st.columns([1, 1, 1])
    with filter_cols[0]:
        categories = ["All"] + get_categories()
        category_filter = st.selectbox(
            "Filter by Category", categories, key="category_filter"
        )
    with filter_cols[1]:
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All", "High", "Medium", "Low"],
            key="priority_filter",
        )
    with filter_cols[2]:
        show_completed = st.checkbox("Show Completed Tasks", value=False)

    # Filter tasks
    filtered_tasks = filter_tasks(
        st.session_state.tasks,
        show_completed,
        category_filter if category_filter != "All" else None,
        priority_filter if priority_filter != "All" else None,
    )

    # Display notifications
    display_notifications(filtered_tasks)

    # Display tasks
    display_tasks_with_colors(filtered_tasks)

    # Category management
    with st.expander("Manage Categories"):
        manage_categories()

    # Testing section
    st.markdown("---")
    st.subheader("🧪 Testing")

    # Create three rows of test buttons
    test_row1 = st.columns(2)
    test_row2 = st.columns(2)
    test_row3 = st.columns(2)

    with test_row1[0]:
        if st.button("Run All Tests"):
            with st.spinner("Running tests..."):
                result = run_tests()
                
                if result["success"]:
                    st.success("Tests completed successfully!")
                else:
                    st.error("Some tests failed.")
                
                st.code(result["test_results"])
                
                if result["coverage"]:
                    st.markdown(f"**Coverage Summary:** `{result['coverage']}`")

    with test_row1[1]:
        if st.button("Run BDD Tests"):
            with st.spinner("Running BDD tests..."):
                result = run_bdd_tests()
                st.code(result)

    with test_row2[0]:
        if st.button("Run Coverage Report"):
            with st.spinner("Generating coverage report..."):
                # Set up environment with project root in PYTHONPATH
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                env = os.environ.copy()
                env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
                
                # Run coverage report with branch coverage
                result = subprocess.run(
                    [
                        "python", 
                        "-m", 
                        "pytest", 
                        "--cov=src", 
                        "--cov-branch", 
                        "--cov-report=term-missing", 
                        "tests/"
                    ],
                    capture_output=True,
                    text=True,
                    env=env,
                )
                st.code(result.stdout + result.stderr)

    with test_row2[1]:
        if st.button("Generate HTML Report"):
            with st.spinner("Generating HTML report..."):
                # Set up environment with project root in PYTHONPATH
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                env = os.environ.copy()
                env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
                
                # Generate HTML coverage report
                result = subprocess.run(
                    ["python", "-m", "pytest", "--cov=src", "--cov-report=html", "tests/"],
                    capture_output=True,
                    text=True,
                    env=env,
                )

                # Get the absolute path to the HTML report
                html_report = os.path.abspath("htmlcov/index.html")

                # Display success message and path
                st.success("HTML coverage report generated!")
                st.markdown(f"Report generated at: `{html_report}`")

                # Try to open the report in the default browser
                try:
                    import webbrowser
                    webbrowser.open(f"file://{html_report}")
                    st.info("Report opened in your default browser")
                except:
                    st.warning(
                        "Could not automatically open the report. Please open it manually."
                    )

    with test_row3[0]:
        if st.button("Run Parameterized Tests"):
            with st.spinner("Running parameterized tests..."):
                # Set up environment with project root in PYTHONPATH
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                env = os.environ.copy()
                env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
                
                # Run tests with -v to show individual parameter cases
                result = subprocess.run(
                    [
                        "python", 
                        "-m", 
                        "pytest", 
                        "-v", 
                        "tests/test_advanced.py::test_get_priority_color_parametrized", 
                        "tests/test_advanced.py::test_filter_tasks_by_priority_parametrized",
                        "tests/test_advanced.py::test_filter_tasks_by_category_parametrized",
                        "tests/test_advanced.py::test_task_due_date_parametrized",
                        "tests/test_advanced.py::test_validate_task_parametrized"
                    ],
                    capture_output=True,
                    text=True,
                    env=env,
                )
                st.code(result.stdout + result.stderr)

    with test_row3[1]:
        if st.button("Run Property Tests"):
            with st.spinner("Running property-based tests..."):
                result = run_property_tests()
                st.code(result)


if __name__ == "__main__":
    main()