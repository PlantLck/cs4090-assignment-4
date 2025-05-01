# To-Do App Testing - Comprehensive Implementation Report

# Max Locke
Github link - https://github.com/PlantLck/cs4090-assignment-4
Streamlit link - https://maxlockeassignment4.streamlit.app/

## 1. Executive Summary

This report documents the comprehensive testing implementation for a Streamlit-based To-Do List application. The testing strategy encompassed multiple methodologies including unit testing, advanced pytest features, Test-Driven Development (TDD), Behavior-Driven Development (BDD), and Property-Based Testing. The implementation achieved over 90% code coverage and successfully identified and resolved five critical bugs. The TDD approach led to the development of three new features, while BDD ensured proper translation of user requirements into functional code. Property-based testing validated the application's robustness against a wide range of inputs.

## 2. Testing Methodology Overview

### 2.1 Project Scope

The project involved testing a Streamlit-based To-Do List application with features for:
- Creating, editing, and deleting tasks
- Setting priorities and due dates
- Categorizing and filtering tasks
- Marking tasks as complete

### 2.2 Testing Approaches

Five complementary testing approaches were implemented:

1. **Unit Testing**: Testing individual functions in isolation to verify basic functionality
2. **Advanced Pytest Features**: Utilizing fixtures, parameterization, and mocking
3. **Test-Driven Development (TDD)**: Writing tests before implementing features
4. **Behavior-Driven Development (BDD)**: Defining tests in natural language
5. **Property-Based Testing**: Testing invariants with randomly generated inputs

### 2.3 Test Framework and Tools

- **Testing Framework**: pytest with pytest-cov, pytest-mock, pytest-bdd
- **Coverage Analysis**: Coverage reporting with branch analysis
- **User Interface**: Streamlit with integrated test execution buttons
- **Property Testing**: Hypothesis library for generative testing

## 3. Unit Testing and Bug Resolution

### 3.1 Test Coverage Strategy

Unit testing focused on:
- Core functionality in tasks.py (validation, creation, filtering, search)
- User interface components in app.py
- Edge cases and error handling
- File operations and data persistence

Tests were organized into logical modules (test_basic.py, test_tasks.py, test_app.py) to ensure maintainability and comprehensive coverage.

### 3.2 Key Bug Findings and Resolutions

Five critical bugs were identified and fixed:

1. **JSONDecodeError Handling**  
   *Issue*: Load_tasks failed with corrupted JSON files  
   *Resolution*: Added exception handling for JSONDecodeError

2. **Missing Error Handling in save_tasks**  
   *Issue*: No handling for file write errors  
   *Resolution*: Added error handling for IOError with meaningful messages

3. **Date Comparison in get_overdue_tasks**  
   *Issue*: Dates compared as strings, leading to incorrect results  
   *Resolution*: Converted dates to datetime objects for accurate comparison

4. **Missing Input Validation in search_tasks**  
   *Issue*: Function crashed with None or empty queries  
   *Resolution*: Added input validation for search queries

5. **Streamlit Test Runner Path Issue**  
   *Issue*: Test runner couldn't find src module  
   *Resolution*: Added project root to PYTHONPATH in test environment

## 4. Advanced Testing Methodologies

### 4.1 Advanced Pytest Features

**Parameterized Tests**  
Implemented tests with multiple input variations:

```python
@pytest.mark.parametrize(
    "priority,expected_color", 
    [
        ("High", "red"),
        ("Medium", "orange"),
        ("Low", "green"),
        ("Invalid", "black"),
    ]
)
def test_get_priority_color_parametrized(priority, expected_color):
    assert get_priority_color(priority) == expected_color
```

**Fixtures and Mocking**  
Used fixtures for test data and mocking for UI components:

```python
@pytest.fixture
def mock_streamlit():
    with patch("src.app.st") as mock_st:
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_st.checkbox.return_value = False
        yield mock_st
```

### 4.2 Test-Driven Development (TDD)

Three features were developed using TDD:

1. **Task Categories Management**  
   - Tests for adding, validating, and storing categories
   - Implementation with proper validation and persistence

2. **Task Priority Color Coding**  
   - Tests for color assignment based on priority levels
   - Implementation with color mapping and display formatting

3. **Task Due Date Notifications**  
   - Tests for different notification types (overdue, today, upcoming)
   - Implementation with date comparison and notification generation

Each feature followed the TDD process:
1. Write failing tests
2. Implement minimal code to pass tests
3. Refactor for optimization and readability
4. Verify tests still pass

### 4.3 Behavior-Driven Development (BDD)

BDD implementation used Gherkin syntax to define expected behavior:

```gherkin
Feature: Task Management
  As a user of the To-Do application
  I want to manage my tasks effectively

  Scenario: Adding a new task
    Given I have an empty task list
    When I add a new task with title "New Test Task"
    Then the task list should contain "1" tasks
```

Step definitions connected features to implementation:

```python
@when(parsers.parse('I add a new task with title "{title}"'))
def add_new_task(context, title, tasks_file):
    task = create_task(
        title=title,
        description="Test description",
        priority="Medium",
        category="Work",
        due_date=datetime.now().strftime("%Y-%m-%d")
    )
    context["tasks"].append(task)
    save_tasks(context["tasks"], tasks_file)
```

Five key scenarios were implemented:
1. Adding a new task
2. Completing a task
3. Task priority colors
4. Task due date status
5. Category management

### 4.4 Property-Based Testing

Property-based testing used Hypothesis to generate test inputs:

```python
# Define strategies for task properties
task_titles = st.text(min_size=1, max_size=50)
task_priorities = st.sampled_from(["High", "Medium", "Low"])
valid_dates = st.dates().map(lambda d: d.strftime("%Y-%m-%d"))

@st.composite
def task_strategy(draw):
    return {
        "id": draw(st.integers(min_value=1, max_value=1000)),
        "title": draw(task_titles),
        "priority": draw(task_priorities),
        "due_date": draw(valid_dates),
        "completed": draw(st.booleans()),
    }

@given(tasks=task_lists, priority=task_priorities)
@settings(max_examples=20)
def test_filter_tasks_by_priority_property(tasks, priority):
    filtered_tasks = filter_tasks_by_priority(tasks, priority)
    
    # Property assertions
    assert all(task["priority"] == priority for task in filtered_tasks)
    assert len(filtered_tasks) == len([task for task in tasks 
                                      if task["priority"] == priority])
```

Key properties tested included:
- Task validation for arbitrary inputs
- Filtering functions' correctness for any task list
- Search functionality for any query
- ID generation uniqueness
- Overdue task detection accuracy

## 5. Streamlit Testing Interface

Six test buttons were implemented in the Streamlit interface:

1. **Run All Tests**: Executes the complete test suite
2. **Run BDD Tests**: Runs behavior-driven tests
3. **Run Coverage Report**: Generates detailed coverage information
4. **Generate HTML Report**: Creates an interactive HTML coverage report
5. **Run Parameterized Tests**: Executes tests with multiple input combinations
6. **Run Property Tests**: Executes property-based tests

Test results are displayed within the interface, including execution status, coverage percentage, and detailed output.

## 6. Results and Conclusions

### 6.1 Testing Achievements

- **Code Coverage**: Achieved >90% coverage of application code
- **Bug Resolution**: Identified and fixed 5 critical bugs
- **Feature Development**: Added 3 new features using TDD
- **User-Centric Testing**: Implemented BDD to align with user requirements
- **Robustness**: Validated application with property-based testing

### 6.2 Testing Benefits by Methodology

Each testing methodology provided unique benefits:

- **Unit Testing**: Ensured basic functionality correctness
- **Advanced Pytest Features**: Improved test efficiency and organization
- **Test-Driven Development**: Led to well-designed, thoroughly tested features
- **Behavior-Driven Development**: Aligned implementation with user requirements
- **Property-Based Testing**: Improved robustness against unexpected inputs

### 6.3 Test Suite Structure

```
todo_app/
├── src/
│   ├── app.py              # Streamlit UI
│   ├── tasks.py            # Core task logic
│   └── __init__.py         # Package initialization
├── tests/
│   ├── test_basic.py       # Basic unit tests
│   ├── test_tasks.py       # Task functionality tests
│   ├── test_app.py         # UI component tests
│   ├── test_advanced.py    # Advanced pytest features
│   ├── test_tdd.py         # TDD feature tests
│   ├── test_property.py    # Property-based tests
│   ├── test_bdd.py         # BDD implementation
│   └── feature/            # BDD feature files
│       ├── add_task.feature
│       └── steps/
│           └── test_add_steps.py
```

### 6.4 Recommendations for Future Improvements

1. **Continuous Integration**: Integrate testing into a CI/CD pipeline
2. **Performance Testing**: Add tests for large task lists
3. **Security Testing**: Add tests for input sanitization
4. **Accessibility Testing**: Ensure UI components meet accessibility standards

## 7. Summary

The comprehensive testing approach not only identified and fixed existing bugs but also improved overall code quality, ensuring the application functions correctly under a wide range of conditions. Through the implementation of multiple testing methodologies, the To-Do application achieved high reliability and maintainability.

The Streamlit integration allows for easy test execution, making the testing process accessible and visible. The combination of unit testing, TDD, BDD, and property-based testing provides a robust foundation for ongoing development and maintenance of the application.

By addressing both functional correctness and user requirements, the testing implementation ensures that the To-Do application provides a reliable and effective task management experience.
