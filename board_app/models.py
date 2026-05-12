from django.db import models
from django.contrib.auth.models import User


class Board(models.Model):
    """
    Represents a Kanban board.
    A board has one owner and multiple members, and contains tasks.
    """

    title = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_boards"
    )
    members = models.ManyToManyField(User, related_name="boards", blank=True)

    def __str__(self):
        return f"{self.title}"


class Task(models.Model):
    """
    Represents a task on a board.
    A task belongs to one board and can have an assignee and a reviewer.
    Deleting a board cascades to its tasks. Deleting a user sets assignee/reviewer to null.
    """

    STATUS_CHOICES = [
        ("to-do", "To Do"),
        ("in-progress", "In Progress"),
        ("review", "Review"),
        ("done", "Done"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="to-do")
    priority = models.CharField(
        max_length=50, choices=PRIORITY_CHOICES, default="medium"
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_tasks",
    )
    due_date = models.DateField(null=True, blank=True)


class Comment(models.Model):
    """
    Represents a comment on a task.
    A comment belongs to one task and one author.
    Deleting a task or author cascades to their comments.
    """

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author} on {self.task}"
