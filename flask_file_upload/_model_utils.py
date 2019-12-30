"""
    Behaviours required by Model class _so we can keep SqlAlchemy Model
    free of methods & other members.
"""
from typing import List, Any, Dict, Tuple, ClassVar, Callable
import inspect

from .column import Column


class _ModelUtils:

    keys: Tuple[str] = ("file_name", "file_type", "mime_type")

    @staticmethod
    def create_keys(keys: Tuple[str], filename: str, fn: Callable = None) -> Dict[str, None]:
        """
        Adds the SqlAlchemy Column object with key & name kwargs defined to the returned dict
        :param keys:
        :param filename:
        :param fn: Generates a SqlAlchemy Column with key & name kwargs set
        :return:
        """
        col_dict = {}
        for k in keys:
            key = f"{filename}__{k}"
            col_dict[key] = fn(key, key)
        return col_dict

    @staticmethod
    def get_primary_key(model):
        """
        This will always target the first primary key in
        the list (in case there are multiple being used)
        :param model:
        :return str:
        """
        try:
            return model.__mapper__.primary_key[0].name
        except AttributeError as err:
            raise AttributeError("[FLASK_FILE_UPLOADS_ERROR] You must pass a model instance"
                                 f"to the save_file method. Full error: {err}"
                                 )

    @staticmethod
    def get_table_name(model: Any) -> str:
        """
        Set on class initiation
        :return: None
        """
        return model.__tablename__

    @staticmethod
    def get_id_value(model) -> int:
        """
        :param model:
        :return:
        """
        return getattr(model, _ModelUtils.get_primary_key(model), None)

    @staticmethod
    def columns_dict(file_name: str, db) -> Dict[str, Any]:
        """
        We must define the SqlAlchemy Column object with key & name kwargs
        otherwise sqlAlchemy will define these incorrectly if they are set to None
        :param file_name:
        :param db:
        :return Dict[str, Any]:
        """
        def create_col(key, name): return db.Column(db.String,  key=key, name=name)
        return _ModelUtils.create_keys(
            _ModelUtils.keys,
            file_name,
            create_col
        )

    @staticmethod
    def set_columns(wrapped: ClassVar, new_cols: Tuple[Dict[str, Any]]) -> None:
        """
        Sets related file data to a SqlAlchemy Model
        :return:
        """
        for col_dict in new_cols:
            for k, v in col_dict.items():
                setattr(wrapped, k, v)

    @staticmethod
    def remove_unused_cols(wrapped: ClassVar,  filenames: Tuple[str]) -> None:
        """
        Removes the original named attributes
        (this could be a good place to store
         metadata in a dict for example...)
        :return:
        """
        for col_name in filenames:
            delattr(wrapped, col_name)

    @staticmethod
    def get_attr_from_model(wrapped: ClassVar, new_cols: List, file_names: List) -> Any:
        """
        Adds values to new_cols & file_names so as not to
        change the size of the dict at runtime
        :return None:
        """
        for attr, value in wrapped.__dict__.items():
            if isinstance(value, Column):
                new_cols.append(_ModelUtils.columns_dict(attr, value.db))
                file_names.append(str(attr))
        return new_cols, file_names

    @staticmethod
    def add_postfix(filename: str, postfix: str) -> str:
        """
        :param filename:
        :param postfix:
        :return str:
        """
        return f"{filename}__{postfix}"

    @staticmethod
    def get_by_postfix(model: ClassVar, filename: str, postfix: str) -> str:
        """
        :param model:
        :param filename:
        :param postfix:
        :return str:
        """
        return getattr(model, _ModelUtils.add_postfix(filename, postfix))

    @staticmethod
    def set_static_methods(static_cls: Any, klass: Any) -> None:
        """
        Function to set static methods as until a class is instantiated
        static methods are not callable.
        :param static_cls:
        :param cls:
        :return: None
        """
        for attr in dir(klass):
            for cls in inspect.getmro(klass):
                if inspect.isroutine(getattr(klass, attr)):
                    if attr in cls.__dict__:
                        bound_value = cls.__dict__[attr]
                        if isinstance(bound_value, staticmethod):
                            static_method_name = bound_value.__func__.__name__
                            static_method = cls.__dict__[attr].__func__
                            setattr(static_cls, static_method_name, static_method)
