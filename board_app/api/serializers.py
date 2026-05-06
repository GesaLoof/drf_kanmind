from rest_framework import serializers
from board_app.models import Board, Task, Comment
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound


class BoardSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
        write_only = True
    )

    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count', 'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id', 'members']
        

    def get_member_count(self, obj):
        return obj.members.count()

    def get_ticket_count(self, obj):
        return 0  # replace with actual logic when you have a Ticket model

    def get_tasks_to_do_count(self, obj):
        return 0  # replace with actual logic when you have a Task model

    def get_tasks_high_prio_count(self, obj):
        return 0  # replace with actual logic when you have a Task model
    

class MemberSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(source='profile.fullname')
    
    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']



class TaskSerializer(serializers.ModelSerializer):
    assignee = MemberSerializer(read_only=True)
    reviewer = MemberSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='assignee', allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source='reviewer', allow_null=True
    )
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'board', 'title', 'description', 'status', 
                  'priority', 'assignee', 'assignee_id', 'reviewer',
                  'reviewer_id', 'due_date', 'comments_count']

    def get_comments_count(self, obj):
        return 0  # replace with actual logic when you have a Comment model
    
    def validate_board(self, value):
        try:
            board = Board.objects.get(pk=value.id)
            return board
        except Board.DoesNotExist:
            raise NotFound("Board not found.")
    

class BoardDetailSerializer(serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = MemberSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']


class BoardUpdateSerializer(serializers.ModelSerializer):
    owner_data = MemberSerializer(source='owner', read_only=True)
    members_data = MemberSerializer(source='members', many=True, read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        write_only=True
    )

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_data', 'members_data', 'members']

class TaskDetailSerializer(serializers.ModelSerializer):
    reviewer_id = MemberSerializer(read_only=True)
    assignee_id =  MemberSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'board', 'title', 'description', 'status', 'priority', 'assignee_id', 'reviewer_id', 'due_date', 'comments_count']

    def get_reviewer_id(self, obj):
        return obj.reviewer.id if obj.reviewer else None

    def get_assignee_id(self, obj):
        return obj.assignee.id if obj.assignee else None

    def get_comments_count(self, obj):
        return 0
    

class TaskUpdateSerializer(serializers.ModelSerializer):
    assignee = MemberSerializer(read_only=True)
    reviewer = MemberSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='assignee',
        allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='reviewer',
        allow_null=True
    )
    class Meta:
        model = Task
        fields = ['id', 'board', 'title', 'description', 'status', 'priority', 'assignee_id', 'assignee', 'reviewer_id', 'reviewer', 'due_date']


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at']
        read_only_fields = ['author', 'created_at', 'task']

    def get_author(self, obj):
        try:
            return obj.author.profile.fullname
        except:
            return None