from fastapi import APIRouter

from .utils import camel_to_snake_case

__all__ = ['MainRouter']


class MainRouter(APIRouter):

    @classmethod
    def _build_single_obj_path(cls, base_path, name='id', annotation=str):
        return f'{base_path}/{{{name}:{annotation.__name__}}}'

    def add_view(self, base_path: str = '', tags: list = None, **kwargs):
        def wrapper(view):
            nonlocal base_path, tags
            if not base_path:
                tag = camel_to_snake_case(view.model.__name__)
                base_path = '/' + tag
                if tags is None:
                    tags = [tag]

            name = getattr(view, 'key_name', 'id')
            annotation = getattr(view, 'key_type', int)
            path = self._build_single_obj_path(base_path, name, annotation)

            if hasattr(view, 'retrieve_list'):
                params = view.params.get('retrieve_list') or {}
                method = self.get(path=base_path, response_model=view.list_schema, tags=tags, **kwargs, **params)
                method(view.retrieve_list)

            if hasattr(view, 'retrieve'):
                params = view.params.get('retrieve') or {}
                method = self.get(path=path, response_model=view.output_schema, tags=tags, **kwargs, **params)
                method(view.retrieve)

            if hasattr(view, 'retrieve_single_object_data'):
                params = view.params.get('retrieve_single_object_data') or {}
                method = self.get(path=base_path, response_model=view.output_schema, tags=tags, **kwargs, **params)
                method(view.retrieve_single_object_data)

            if hasattr(view, 'create'):
                params = view.params.get('create') or {}
                method = self.post(path=base_path, response_model=view.output_schema, tags=tags, **kwargs, **params)
                method(view.create)

            if hasattr(view, 'update'):
                params = view.params.get('update') or {}
                view.update.__annotations__['request'] = view.get_put_schema()
                method = self.put(path=path, response_model=view.output_schema, tags=tags, **kwargs, **params)
                method(view.update)

            if hasattr(view, 'update_partial'):
                params = view.params.get('update_partial') or {}
                view.update_partial.__annotations__['request'] = view.get_patch_schema()
                method = self.patch(path=path, response_model=view.output_schema, tags=tags, **kwargs, **params)
                method(view.update_partial)

            if hasattr(view, 'delete'):
                params = view.params.get('delete') or {}
                method = self.delete(path=path, response_model=view.get_delete_schema(), tags=tags, **kwargs, **params)
                method(view.delete)

            return view

        return wrapper


router = MainRouter()
