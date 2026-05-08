from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated


class IsBoardOwnerOrMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        # owner and members can do anything
        if (request.user == obj.owner) or (request.user in obj.members.all()):
            return True
        else:
            return False


class IsTaskBoardOwnerOrMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        board = obj.board
        if request.user == board.owner:
            return True
        if request.method in SAFE_METHODS:
            return request.user in board.members.all()
        return False
