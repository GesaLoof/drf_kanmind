from rest_framework import serializers
from board_app.models import Board


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ['id', 'title', 'member_count', 'ticket_count', 'tasks_to_do_count', \
                  'tasks_high_prio_count', 'owner_id']
        read_only_fields = ['id', 'owner_id']