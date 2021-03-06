from rest_framework import permissions

from ..accounts.models import AccountCollaborator
from .models import Board


class BoardPermission(permissions.BasePermission):
    def is_authenticated(self, request):
        return request.user and request.user.is_authenticated()

    def has_permission(self, request, view):
        """
        Returns `True` if the user is authenticated. If the user is
        not authenticated and view.action is `list` or is not safe.
        """
        is_authenticated = self.is_authenticated(request)
        is_safe = request.method in permissions.SAFE_METHODS

        if not is_authenticated and (view.action == 'list' or not is_safe):
            return False

        return True

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if user is a collaborator with the
        corresponding permission on this board, `False` otherwise.
        Returns `True` if permission is read and object is shared.
        Returns `False` if user is not authenticated.
        """
        permission = 'read'
        is_authenticated = self.is_authenticated(request)
        is_safe = request.method in permissions.SAFE_METHODS
        action = view.action

        if not is_safe:
            permission = 'write'

        if permission == 'read' and obj.is_shared:
            return True

        if not is_authenticated:
            return False

        if action in ['comments', 'leave']:
            permission = None

        return obj.is_user_collaborator(request.user, permission=permission)


class BoardCollaboratorPermission(permissions.BasePermission):
    def is_authenticated(self, request):
        return request.user and request.user.is_authenticated()

    def board_collaborator_has_permission(self, request, view, board_id):
        try:
            board = Board.objects.get(pk=board_id)
        except Board.DoesNotExist:
            return False

        permission = BoardPermission()
        has_board_permission = permission.has_object_permission(
            request, view, board)

        account_owner = AccountCollaborator.objects.filter(
            account_id=board.account_id,
            user=request.user,
            is_owner=True
        )

        return has_board_permission or account_owner.exists()

    def has_permission(self, request, view):
        """
        Returns `True` if the user is a board collaborator with
        write permissions trying to create. Returns `True` if
        user is the account owner.
        """
        is_authenticated = self.is_authenticated(request)
        is_safe = request.method in permissions.SAFE_METHODS
        action = view.action

        board = request.QUERY_PARAMS.get('board')

        if not is_authenticated and is_safe and action == 'list' and board:
            return True

        bulk = isinstance(request.DATA, list)

        if is_authenticated and request.method == 'POST':
            has_perm = None

            if not bulk:
                board_id = request.DATA.get('board')
                if board_id:
                    has_perm = self.board_collaborator_has_permission(
                        request, view, board_id)
            else:
                perms = []
                for item in request.DATA:
                    board_id = item.get('board')
                    if board_id:
                        perms.append(self.board_collaborator_has_permission(
                            request, view, board_id))
                has_perm = all(perms)

            if has_perm is not None:
                return has_perm

        if is_authenticated:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        """
        Returns `True` if user is a board collaborator with write permissions.
        Returns `True` if user is the board collaborator trying to delete.
        Returns `True if user is the account owner.
        """

        if request.method == 'DELETE':
            has_board_permission = request.user == obj.user
        else:
            permission = BoardPermission()
            has_board_permission = permission.has_object_permission(
                request, view, obj.board)

        account_owner = AccountCollaborator.objects.filter(
            account_id=obj.board.account_id,
            user=request.user,
            is_owner=True
        )

        return has_board_permission or account_owner.exists()


class BoardCollaboratorRequestPermission(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if user is a collaborator with the
        corresponding permission on this board, `False` otherwise.
        """
        return obj.board.account.is_user_collaborator(
            request.user, is_owner=True)
