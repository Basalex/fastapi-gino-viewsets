
FastApi Gino ViewSets
===========================

Inspired by Django Rest Framework

| Python 3.7+


| **Install**: ``pip install fastapi-gino-viewsets``

**Github**: https://github.com/basalex/fastapi_gino_viewsets

Examples of usage:
~~~~~~~~~~~~~~~~~~

Create your model and migrate database

.. code:: python

    class User(db.Model):
        __tablename__ = 'users'
        id = db.Column(db.Integer(), primary_key=True)
        username = db.Column(db.String(255), nullable=False, unique=True)
        email = db.Column(db.EmailType, nullable=False, unique=True)
        age = db.Column(db.Integer(), nullable=True)

Then, you would want to use MainRouter class

.. code:: python

    from fastapi_gino_viewsets import MainRouter
    from fastapi_gino_viewsets import Viewset

    router = MainRouter()

    @router.add_view('/user')
    class UserViewSet(ViewSet):
        model = User

| That's it! Now all methods -> get[+list+filters], post, patch, put, deletes are available and ready for use


Available Mixin and ViewSet classes
-----------------------------------

* **AggregationMixin** - Requires output_schema ->  **retrieve_aggregated_data**
    * get_query[sync, async] - required to be manually implemented
    * filter_query - override to change filters behaviour
* **ListMixin** - Used when you want to get a list of objects, main method -> **retrieve_list** methods
    * base_list_schema -> override base class for output schema
    * retrieve_list - it's not recommended to be overridden, probably you just don't need to use the mixin
    * get_query[sync, async] - override to change default behaviour
    * filter_query - override to change filters behaviour
    * sort_query - override to change sort behaviour
    * total - override to change total count calculation
    * paginate - override to change paginate behaviour
    * prepare_data_hook - override for manipulating data after query execution
* **RetrieveModelMixin** - Get single object by id -> **retrieve** method
* **UpdateModelMixin** - Update using PUT http -> **update** method
* **UpdateModelMixin** - Update using PATCH http -> **update_partial** method
* **DeleteModelMixin** - Delete object by id -> **delete** method
* **ReadOnlyViewset** - Provides  **retrieve** and  **retrieve_list** methods
* **Viewset** - Prodiveds all methods from all mixins, but AggregationMixin
