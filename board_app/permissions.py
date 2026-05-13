from rest_framework.permissions import BasePermission, SAFE_METHODS
from board_app.models import Board, Task


class IsBoardOwnerOrMember(BasePermission):
    def has_permission(self, request, view):
        """Checks board membership for list/create actions using pk from the URL."""
        board_pk = view.kwargs.get("pk")
        if not board_pk:
            return True
        try:
            board = Board.objects.get(pk=board_pk)
            return request.user == board.owner or request.user in board.members.all()
        except Board.DoesNotExist:
            return True

    def has_object_permission(self, request, view, obj):
        if (request.user == obj.owner) or (request.user in obj.members.all()):
            return True
        return False


class IsTaskBoardOwnerOrMember(BasePermission):
    def has_permission(self, request, view):
        """Checks board membership using task_pk from the URL."""
        task_pk = view.kwargs.get("task_pk") or view.kwargs.get("pk")
        if not task_pk:
            return True
        try:
            task = Task.objects.get(pk=task_pk)
            board = task.board
            return request.user == board.owner or request.user in board.members.all()
        except Task.DoesNotExist:
            return True

    def has_object_permission(self, request, view, obj):
        board = obj.board
        if request.user == board.owner:
            return True
        if request.method in SAFE_METHODS:
            return request.user in board.members.all()
        return False