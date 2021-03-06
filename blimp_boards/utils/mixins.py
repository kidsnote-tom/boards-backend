from django.forms.models import model_to_dict

from rest_framework import status
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from rest_framework.response import Response

from .response import ErrorResponse


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

        return ErrorResponse(serializer.errors)


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

        return ErrorResponse(serializer.errors)


class BulkCreateModelMixin(CreateModelMixin):
    """
    From https://github.com/miki725/django-rest-framework-bulk

    Either create a single or many model instances in bulk by using the
    Serializer's ``many=True`` ability from Django REST >= 2.2.5.

    This mixin uses the same method to create model instances
    as ``CreateModelMixin`` because both non-bulk and bulk
    requests will use ``POST`` request method.
    """

    def create(self, request, *args, **kwargs):
        bulk = isinstance(request.DATA, list)

        if not bulk:
            return super(BulkCreateModelMixin, self).create(
                request, *args, **kwargs)

        serializer = self.get_serializer(data=request.DATA, many=True)

        if serializer.is_valid():
            [self.pre_save(obj) for obj in serializer.object]
            self.object = serializer.save(force_insert=True)
            [self.post_save(obj) for obj in self.object]
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return ErrorResponse(serializer.errors)


class ModelDiffMixin(object):
    """
    A model mixin that tracks model fields' values and provide some useful api
    to know what fields have been changed.
    """

    def __init__(self, *args, **kwargs):
        super(ModelDiffMixin, self).__init__(*args, **kwargs)
        self.__initial = self._dict

    @property
    def diff(self):
        d1 = self.__initial
        d2 = self._dict
        diffs = [(k, (v, d2[k])) for k, v in d1.items() if v != d2[k]]
        return dict(diffs)

    @property
    def has_changed(self):
        return bool(self.diff)

    @property
    def changed_fields(self):
        return self.diff.keys()

    def get_field_diff(self, field_name):
        """
        Returns a diff for field if it's changed and None otherwise.
        """
        return self.diff.get(field_name, None)

    def has_field_changed(self, field_name):
        """
        Returns `True` if field has changed.
        """
        return field_name in self.changed_fields

    def save(self, *args, **kwargs):
        """
        Saves model and set initial state.
        """
        super(ModelDiffMixin, self).save(*args, **kwargs)
        self.__initial = self._dict

    @property
    def _dict(self):
        fields = [field.name for field in self._meta.fields]
        return model_to_dict(self, fields=fields)
