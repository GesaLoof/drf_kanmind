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
from .serializers import BoardSerializer, BoardDetailSerializer, BoardUpdateSerializer, MemberSerializer, TaskSerializer,\
    TaskDetailSerializer, TaskUpdateSerializer, CommentSerializer
from board_app.permissions import IsBoardOwnerOrMember, IsTaskBoardOwnerOrMember

class TestApiView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({'message': 'running...'}, status=status.HTTP_200_OK)

class BoardViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == 'list' or self.action == 'create':
            return [IsAuthenticated()]       # any logged in user
        return [IsAuthenticated(), IsBoardOwnerOrMember()]  # owner or member only

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return BoardDetailSerializer
        if self.action in ['update', 'partial_update']:  # PUT and PATCH
            return BoardUpdateSerializer
        return BoardSerializer
    
    def get_object(self):
        try:
            obj = Board.objects.get(pk=self.kwargs['pk'])
        except Board.DoesNotExist:
            raise NotFound("No Board matches the given query.")
        
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        if self.action == 'list':
            return Board.objects.all()  # all boards for list
        user = self.request.user
        return Board.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct()  # only owned/member boards for detail

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)



class TaskViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated()]       # any logged in user
        return [IsAuthenticated(), IsTaskBoardOwnerOrMember()]  # owner or member only

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TaskDetailSerializer
        if self.action in ['update', 'partial_update']:  # PUT and PATCH
            return TaskUpdateSerializer
        return TaskSerializer
    
    def get_object(self):
        try:
            obj = Task.objects.get(pk=self.kwargs['pk'])
        except Task.DoesNotExist:
            raise NotFound("No Task matches the given query.")
        
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        return Task.objects.all()

    def perform_create(self, serializer):
        board_id = serializer.validated_data.get('board').id
        board = Board.objects.get(pk=board_id)
        
        if self.request.user != board.owner and self.request.user not in board.members.all():
            raise PermissionDenied("You must be a member of the board to create a task.")
        
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = TaskUpdateSerializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            instance.refresh_from_db()
            response_serializer = TaskDetailSerializer(instance, context={'request': request})
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmailCheckView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MemberSerializer
    queryset = User.objects.all()

    def get_object(self):
        email = self.request.query_params.get('email')
        obj = get_object_or_404(self.get_queryset(), email=email)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        if not request.query_params.get('email'):
            return Response(
                {'message': 'Email query parameter is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        return self.retrieve(request, *args, **kwargs)
    

class AssignedToMeView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(assignee=user)
    

class ReviewingView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(reviewer=user)
    

class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        task_id = self.kwargs['pk']
        try:
            task = Task.objects.get(pk=task_id)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")
        return Comment.objects.filter(task=task)

    def perform_create(self, serializer):
        task_id = self.kwargs['pk']
        task = Task.objects.get(pk=task_id)
        serializer.save(author=self.request.user, task=task)