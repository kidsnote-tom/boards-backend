from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import action

from ..utils.viewsets import ModelViewSet, CreateListRetrieveViewSet
from .models import Board, BoardCollaborator, BoardCollaboratorRequest
from .serializers import (BoardSerializer, BoardCollaboratorSerializer,
                          BoardCollaboratorRequestSerializer)
from .permissions import (BoardPermission, BoardCollaboratorPermission,
                          BoardCollaboratorRequestPermission)


class BoardViewSet(ModelViewSet):
    model = Board
    serializer_class = BoardSerializer
    permission_classes = (BoardPermission, )

    def get_queryset(self):
        user = self.request.user
        return user.boards


class BoardCollaboratorViewSet(ModelViewSet):
    model = BoardCollaborator
    serializer_class = BoardCollaboratorSerializer
    permission_classes = (BoardCollaboratorPermission, )
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('board', )

    def get_queryset(self):
        user = self.request.user
        return BoardCollaborator.objects.filter(board__in=user.boards)


class BoardCollaboratorRequestViewSet(CreateListRetrieveViewSet):
    model = BoardCollaboratorRequest
    serializer_class = BoardCollaboratorRequestSerializer
    permission_classes = (BoardCollaboratorRequestPermission, )

    def get_queryset(self):
        user = self.request.user
        return BoardCollaboratorRequest.objects.filter(
            board__account__in=user.accounts)

    def initialize_request(self, request, *args, **kwargs):
        """
        Disable authentication and permissions for `create` action.
        """
        request_method = request.method.lower()

        if self.action_map.get(request_method) == 'create':
            self.authentication_classes = ()
            self.permission_classes = ()

        return super(BoardCollaboratorRequestViewSet,
                     self).initialize_request(request, *args, **kwargs)

    @action(methods=['PUT'])
    def accept(self, request, pk=None):
        object = self.get_object()
        serializer = self.get_serializer(object)

        object.accept()

        return Response(serializer.data)

    @action(methods=['PUT'])
    def reject(self, request, pk=None):
        object = self.get_object()
        serializer = self.get_serializer(object)

        object.reject()

        return Response(serializer.data)

    def post_save(self, obj, created=False):
        if created:
            obj.notify_account_owner()