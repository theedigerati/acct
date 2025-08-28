from collections import OrderedDict
from django.utils.module_loading import import_string
from rest_framework.relations import (
    PrimaryKeyRelatedField,
    SlugRelatedField,
    MANY_RELATION_KWARGS,
    ManyRelatedField as DRFManyRelatedField,
)


class ReadSourceMixin:
    """
    The mixin modifies the `get_attribute` method by
    assigning the value of the `source` attribute to the
    `read_source` attribute if the latter is set.

    To avoid interfering with write operations,
    the `bind` method has not been overridden.
    """

    class ManyRelatedField(DRFManyRelatedField):
        def get_attribute(self, instance):
            if self.child_relation.read_source:
                self.source = self.child_relation.read_source
                self.bind(self.field_name, self.parent)

            return super().get_attribute(instance)

    def __init__(self, **kwargs):
        self.read_source = kwargs.pop("read_source", None)
        super().__init__(**kwargs)

    @classmethod
    def many_init(cls, *args, **kwargs):
        if not kwargs.get("read_source", None):
            return super().many_init(*args, **kwargs)

        list_kwargs = {"child_relation": cls(*args, **kwargs)}
        for key in kwargs:
            if key in MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]

        return cls.ManyRelatedField(**list_kwargs)

    def get_attribute(self, instance):
        if self.read_source:
            self.source = self.read_source
            self.bind(self.field_name, self.parent)

        return super().get_attribute(instance)


class Related_To_ObjectFieldMixin(ReadSourceMixin):
    def __init__(self, **kwargs):
        self.object_serializer = kwargs.pop("object_serializer", None)
        self.object_serializer_kwargs = kwargs.pop("object_serializer_kwargs", {})
        assert self.object_serializer is not None, (
            self.__class__.__name__ + " must provide a `object_serializer` argument"
        )
        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        """
        Ovverride default PrimaryKeyRelatedField behavior
        Return full object instead of sending pk only object.
        """
        return False

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([(item.pk, self.display_value(item)) for item in queryset])

    def to_representation(self, data):
        if isinstance(self.object_serializer, str):
            self.object_serializer = import_string(self.object_serializer)

        return self.object_serializer(
            data, context=self.context, **self.object_serializer_kwargs
        ).data


class PrimaryKey_To_ObjectField(Related_To_ObjectFieldMixin, PrimaryKeyRelatedField):
    """
    Override PrimaryKeyRelatedField to represent serializer
    data instead of a pk field of the object.
    """

    pass


class Slug_To_ObjectField(Related_To_ObjectFieldMixin, SlugRelatedField):
    """
    Override SlugRelatedField to represent serializer
    data instead of a slug field of the object.
    """

    pass
