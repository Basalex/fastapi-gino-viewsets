from . import mixins

__all__ = ['ViewSet', 'ReadOnlyViewSet']


class ViewSet(
    mixins.BaseListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.UpdatePartialModelMixin,
    mixins.DeleteModelMixin,
    mixins.BaseModelMixin,
):
    pass


class ReadOnlyViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.BaseModelMixin,
):
    pass
