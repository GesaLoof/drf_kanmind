from rest_framework import viewsets, permissions, status, authentication, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, NotFound
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from board_app.models import Task, Comment

from board_app.models import Board
from .serializers import (
    BoardSerializer,
    BoardDetailSerializer,
    BoardUpdateSerializer,
    MemberSerializer,
    TaskSerializer,
    TaskDetailSerializer,
    TaskUpdateSerializer,
    CommentSerializer,
)
from board_app.permissions import IsBoardOwnerOrMember, IsTaskBoardOwnerOrMember


class TestApiView(APIView):
    """Health check endpoint, accessible without authentication."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Returns a simple message confirming the API is running."""
        return Response({"message": "running..."}, status=status.HTTP_200_OK)


class BoardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing boards with list, create, retrieve, update, and delete actions."""

    def get_permissions(self):
        """Sets permissions based on the action (list/create vs others)."""
        if self.action == "list" or self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsBoardOwnerOrMember()]

    def get_serializer_class(self):
        """Returns the serializer class based on the action."""
        if self.action == "retrieve":
            return BoardDetailSerializer
        if self.action in ["update", "partial_update"]:
            return BoardUpdateSerializer
        return BoardSerializer

    def get_object(self):
        """Retrieves a board by primary key, raising 404 or 403 as needed."""
        try:
            obj = Board.objects.get(pk=self.kwargs["pk"])
        except Board.DoesNotExist:
            raise NotFound("No Board matches the given query.")

        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        """Returns boards based on the action (all or user-specific)."""
        if self.action == "list":
            return Board.objects.all()
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        """Sets the board owner to the authenticated user."""
        serializer.save(owner=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tasks with list, create, retrieve, update, and delete actions."""

    def get_permissions(self):
        """Sets permissions based on the action (list vs others)."""
        if self.action == "list":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsTaskBoardOwnerOrMember()]

    def get_serializer_class(self):
        """Returns the serializer class based on the action."""
        if self.action == "retrieve":
            return TaskDetailSerializer
        if self.action in ["update", "partial_update"]:
            return TaskUpdateSerializer
        return TaskSerializer

    def get_object(self):
        """Retrieves a task by primary key, raising 404 or 403 as needed."""
        try:
            obj = Task.objects.get(pk=self.kwargs["pk"])
        except Task.DoesNotExist:
            raise NotFound("No Task matches the given query.")

        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        """Returns all tasks."""
        return Task.objects.all()

    def perform_create(self, serializer):
        """Validates board membership before creating a task."""
        board_id = serializer.validated_data.get("board").id
        board = Board.objects.get(pk=board_id)

        if (
            self.request.user != board.owner
            and self.request.user not in board.members.all()
        ):
            raise PermissionDenied(
                "You must be a member of the board to create a task."
            )

        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        """Handles PATCH requests and returns a detailed response."""
        instance = self.get_object()
        serializer = TaskUpdateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            instance.refresh_from_db()
            response_serializer = TaskDetailSerializer(
                instance, context={"request": request}
            )
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailCheckView(generics.RetrieveAPIView):
    """Checks if a user with the given email exists via query parameters."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MemberSerializer
    queryset = User.objects.all()

    def get_object(self):
        """Looks up a user by email from the query parameters."""
        email = self.request.query_params.get("email")
        obj = get_object_or_404(self.get_queryset(), email=email)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        """Validates the email query parameter before retrieving the user."""
        if not request.query_params.get("email"):
            return Response(
                {"message": "Email query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self.retrieve(request, *args, **kwargs)


class AssignedToMeView(generics.ListAPIView):
    """Lists tasks assigned to the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Filters tasks by the currently authenticated user as assignee."""
        user = self.request.user
        return Task.objects.filter(assignee=user)


class ReviewingView(generics.ListAPIView):
    """Lists tasks where the user is the reviewer."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Filters tasks by the currently authenticated user as reviewer."""
        user = self.request.user
        return Task.objects.filter(reviewer=user)


class CommentListCreateView(generics.ListCreateAPIView):
    """Lists and creates comments for a specific task."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsTaskBoardOwnerOrMember]

    def get_queryset(self):
        """Returns comments for the task identified by the pk in the URL."""
        task_id = self.kwargs["task_pk"]
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")
        return Comment.objects.filter(task=task)

    def perform_create(self, serializer):
        """Links the comment to the task and sets the author."""
        task_id = self.kwargs["task_pk"]
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")
        serializer.save(author=self.request.user, task=task)

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsTaskBoardOwnerOrMember]

    def get_object(self):
        task_pk = self.kwargs["task_pk"]
        pk = self.kwargs["pk"]
        try:
            comment = Comment.objects.get(pk=pk, task_id=task_pk)
        except Comment.DoesNotExist:
            raise NotFound("Comment not found.")
        return comment