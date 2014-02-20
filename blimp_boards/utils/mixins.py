from rest_framework import status
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.response import Response


class CreateModelMixin(CreateModelMixin):
    """
    Create a model instance.
    """
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.DATA,
                                         files=request.FILES)

        if serializer.is_valid():
            return super(CreateModelMixin, self).create(
                request, *args, **kwargs)

        return Response({
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UpdateModelMixin(UpdateModelMixin):
    """
    Update a model instance.
    """
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        self.object = self.get_object_or_none()

        serializer = self.get_serializer(self.object, data=request.DATA,
                                         files=request.FILES, partial=partial)

        if serializer.is_valid():
            return super(UpdateModelMixin, self).update(
                request, *args, **kwargs)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)