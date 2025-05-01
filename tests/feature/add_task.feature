Feature: Task Management
  As a user of the To-Do application
  I want to manage my tasks effectively
  So that I can keep track of my work and responsibilities

  Scenario: Adding a new task
    Given I have an empty task list
    When I add a new task with title "New Test Task"
    Then the task list should contain "1" tasks

  Scenario: Completing a task
    Given I have a task with title "Test Task" and due date "2023-01-01"
    When I mark the task as completed
    Then the task should be marked as completed

  Scenario: Task priority colors
    Given I have a task with priority "High"
    Then the task should be displayed with "red" color

  Scenario: Task due date status
    Given I have a task with title "Overdue Task" and due date "2023-01-01"
    Then the task should be in the "overdue" section

  Scenario: Category management
    Given I have an empty task list
    When I add a new category "Project Work"
    Then the category list should contain "Project Work"

