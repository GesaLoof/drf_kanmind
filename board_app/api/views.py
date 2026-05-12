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
    """
    A simple health check endpoint to verify the API is running.
    Accessible without authentication.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Returns a simple message confirming the API is running."""
        return Response({"message": "running..."}, status=status.HTTP_200_OK)


class BoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing boards.

    Provides list, create, retrieve, update and delete actions.
    - Any authenticated user can list all boards and create new ones.
    - Only the board owner or a member can retrieve, update or delete a specific board.
    - Different serializers are used depending on the action to control
      which fields are included in the response.
    """

    def get_permissions(self):
        """
        Returns the appropriate permission classes based on the current action.
        - list/create: only requires authentication
        - all other actions: requires authentication AND board ownership/membership
        """
        if self.action == "list" or self.action == "create":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsBoardOwnerOrMember()]

    def get_serializer_class(self):
        """
        Returns the appropriate serializer class based on the current action.
        - retrieve: BoardDetailSerializer (includes nested members and tasks)
        - update/partial_update: BoardUpdateSerializer (includes owner_data and members_data)
        - all other actions: BoardSerializer (includes counts and owner_id)
        """
        if self.action == "retrieve":
            return BoardDetailSerializer
        if self.action in ["update", "partial_update"]:
            return BoardUpdateSerializer
        return BoardSerializer

    def get_object(self):
        """
        Retrieves a single board by primary key.
        Raises a 404 if the board does not exist.
        Raises a 403 if the user does not have permission to access it.
        This override ensures a clear 403 is returned instead of a misleading 404
        when the board exists but the user lacks permission.
        """
        try:
            obj = Board.objects.get(pk=self.kwargs["pk"])
        except Board.DoesNotExist:
            raise NotFound("No Board matches the given query.")

        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        """
        Returns the appropriate queryset based on the current action.
        - list: returns all boards (any authenticated user can see the board list)
        - all other actions: returns only boards where the user is the owner or a member
          .distinct() prevents duplicate results when a user is both owner and member
        """
        if self.action == "list":
            return Board.objects.all()
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def perform_create(self, serializer):
        """
        Sets the owner of the board to the currently authenticated user
        before saving. This prevents the client from setting the owner manually.
        """
        serializer.save(owner=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tasks.

    Provides list, create, retrieve, update and delete actions.
    - Any authenticated user can list all tasks.
    - Only board owners or members can retrieve, update or delete a specific task.
    - Only board owners or members can create a task for a given board.
    - Different serializers are used depending on the action.
    """

    def get_permissions(self):
        """
        Returns the appropriate permission classes based on the current action.
        - list: only requires authentication
        - all other actions: requires authentication AND board ownership/membership
        """
        if self.action == "list":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsTaskBoardOwnerOrMember()]

    def get_serializer_class(self):
        """
        Returns the appropriate serializer class based on the current action.
        - retrieve: TaskDetailSerializer (includes nested assignee and reviewer data)
        - update/partial_update: TaskUpdateSerializer (handles write fields for assignee/reviewer)
        - all other actions: TaskSerializer (standard task representation)
        """
        if self.action == "retrieve":
            return TaskDetailSerializer
        if self.action in ["update", "partial_update"]:
            return TaskUpdateSerializer
        return TaskSerializer

    def get_object(self):
        """
        Retrieves a single task by primary key.
        Raises a 404 if the task does not exist.
        Raises a 403 if the user does not have permission to access it.
        """
        try:
            obj = Task.objects.get(pk=self.kwargs["pk"])
        except Task.DoesNotExist:
            raise NotFound("No Task matches the given query.")

        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        """Returns all tasks. Access control is handled by get_permissions and get_object."""
        return Task.objects.all()

    def perform_create(self, serializer):
        """
        Validates that the currently authenticated user is a member or owner
        of the board the task is being created for before saving.
        Raises a 403 if the user is not a board member or owner.
        """
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
        """
        Handles PATCH requests for partial task updates.
        Overrides the default partial_update to return a full detailed response
        using TaskDetailSerializer after saving, instead of just the updated fields.
        refresh_from_db() ensures the instance has the latest data from the database
        before serializing, particularly important for related fields like assignee
        and reviewer.
        """
        instance = self.get_object()
        serializer = TaskUpdateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Refresh to ensure related objects are properly loaded
            instance.refresh_from_db()
            response_serializer = TaskDetailSerializer(
                instance, context={"request": request}
            )
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmailCheckView(generics.RetrieveAPIView):
    """
    Checks whether a user with the given email address exists in the database.
    The email is passed as a query parameter: /api/email-check/?email=x@x.com
    Returns the user's data if found, or a 404 if not found.
    Returns a 400 if the email query parameter is missing.
    """

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
        """
        Validates that the email query parameter is present before
        attempting to retrieve the user.
        """
        if not request.query_params.get("email"):
            return Response(
                {"message": "Email query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self.retrieve(request, *args, **kwargs)


class AssignedToMeView(generics.ListAPIView):
    """
    Returns all tasks where the currently authenticated user is the assignee.
    Useful for a personal task dashboard view.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Filters tasks by the currently authenticated user as assignee."""
        user = self.request.user
        return Task.objects.filter(assignee=user)


class ReviewingView(generics.ListAPIView):
    """
    Returns all tasks where the currently authenticated user is the reviewer.
    Useful for showing tasks that require the user's review.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """Filters tasks by the currently authenticated user as reviewer."""
        user = self.request.user
        return Task.objects.filter(reviewer=user)


class CommentListCreateView(generics.ListCreateAPIView):
    """
    Lists all comments for a specific task and allows creating new ones.
    The task is identified by its primary key in the URL.
    Returns a 404 if the task does not exist.
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Returns all comments for the task identified by the pk in the URL.
        Raises a 404 if the task does not exist.
        """
        task_id = self.kwargs["pk"]
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")
        return Comment.objects.filter(task=task)

    def perform_create(self, serializer):
        """
        Sets the author to the currently authenticated user and links
        the comment to the task identified by the pk in the URL before saving.
        Raises a 404 if the task does not exist.
        """
        task_id = self.kwargs["pk"]
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")
        serializer.save(author=self.request.user, task=task)
