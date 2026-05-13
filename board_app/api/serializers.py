from rest_framework import serializers
from board_app.models import Board, Task, Comment
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound


class BoardSerializer(serializers.ModelSerializer):
    """
    Serializer for board list and create actions.
    Counts are calculated dynamically, members are write-only.
    """

    member_count = serializers.SerializerMethodField()
    ticket_count = serializers.SerializerMethodField()
    tasks_to_do_count = serializers.SerializerMethodField()
    tasks_high_prio_count = serializers.SerializerMethodField()
    owner_id = serializers.IntegerField(source="owner.id", read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, required=False, write_only=True
    )

    class Meta:
        model = Board
        fields = [
            "id",
            "title",
            "member_count",
            "ticket_count",
            "tasks_to_do_count",
            "tasks_high_prio_count",
            "owner_id",
            "members",
        ]

    def get_ticket_count(self, obj):
        # total number of tasks on this board
        return obj.tasks.count()

    def get_tasks_to_do_count(self, obj):
        return obj.tasks.filter(status="to-do").count()

    def get_tasks_high_prio_count(self, obj):
        return obj.tasks.filter(priority="high").count()
    
    def get_member_count(self, obj):
        return obj.members.count()


class MemberSerializer(serializers.ModelSerializer):
    """Serializes a user with their profile fullname. Used for nested member representations."""

    fullname = serializers.CharField(source="profile.fullname")

    class Meta:
        model = User
        fields = ["id", "email", "fullname"]


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task list and create actions.
    Accepts assignee_id and reviewer_id as IDs for writing,
    returns full nested user data for reading.
    """

    assignee = MemberSerializer(read_only=True)
    reviewer = MemberSerializer(read_only=True)
    # write-only fields that map to the assignee/reviewer FK via source
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="assignee", allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="reviewer", allow_null=True
    )
    comments_count = serializers.SerializerMethodField()
    board = serializers.IntegerField(write_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "assignee_id",
            "reviewer",
            "reviewer_id",
            "due_date",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()

    def validate_board(self, value):
        """Raises 404 if the given board ID does not exist."""
        try:
            return Board.objects.get(pk=value)
        except Board.DoesNotExist:
            raise NotFound("Board not found.")


class BoardDetailSerializer(serializers.ModelSerializer):
    """Serializer for board detail (retrieve) action. Returns nested members and tasks."""

    owner_id = serializers.IntegerField(source="owner.id", read_only=True)
    members = MemberSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ["id", "title", "owner_id", "members", "tasks"]


class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for board update (PATCH/PUT) actions.
    Accepts member IDs for writing, returns full member data in response.
    """

    owner_data = MemberSerializer(source="owner", read_only=True)
    members_data = MemberSerializer(source="members", many=True, read_only=True)
    members = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), many=True, write_only=True
    )

    class Meta:
        model = Board
        fields = ["id", "title", "owner_data", "members_data", "members"]


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer for task retrieve action. Returns nested assignee and reviewer data."""
    
    assignee = MemberSerializer(read_only=True)
    reviewer = MemberSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "reviewer",
            "due_date",
            "comments_count",
        ]

    def get_comments_count(self, obj):
        return obj.comments.count()


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for task update (PATCH/PUT) actions.
    Accepts assignee_id and reviewer_id as IDs for writing,
    returns full nested user data in response.
    """

    assignee = MemberSerializer(read_only=True)
    reviewer = MemberSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="assignee", allow_null=True
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="reviewer", allow_null=True
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "board",
            "title",
            "description",
            "status",
            "priority",
            "assignee_id",
            "assignee",
            "reviewer_id",
            "reviewer",
            "due_date",
        ]


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments. Author is set server-side and returned as a fullname string."""

    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "author", "content", "created_at"]
        read_only_fields = ["author", "created_at", "task"]

    def get_author(self, obj):
        """Returns the author's fullname, or None if their profile doesn't exist."""
        try:
            return obj.author.profile.fullname
        except:
            return None
