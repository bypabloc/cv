"""@module shared.lambda_kit.base_settings — config por variables de entorno.

`BaseSettings` carga cada campo anotado desde la variable de entorno
homonima en MAYUSCULAS. Soporta validadores custom con el patron
`load_<campo>`.

Era identico en los 4 Lambdas del backend; se unifico aca. Cada Lambda
define su `AppConfig(BaseSettings)` con los campos que necesita.
"""

from __future__ import annotations

from json import dumps as json_dumps
from os import environ as os_environ
from typing import Any, get_origin


def _is_str_annotation(field_type: Any) -> bool:
    """True si la anotacion del campo es `str`.

    Acepta tanto el tipo `str` como su forma string `'str'`: con
    `from __future__ import annotations` activo en el modulo que define
    el `AppConfig`, las anotaciones llegan como strings (PEP 563).
    """
    return field_type is str or field_type == 'str'


def _is_list_annotation(field_type: Any) -> bool:
    """True si la anotacion del campo es una `list[...]`.

    Acepta el origen `list` y las formas string (`'list[str]'`, `'list'`)
    para el caso de anotaciones diferidas.
    """
    if get_origin(field_type) is list:
        return True
    return isinstance(field_type, str) and field_type.startswith('list')


class BaseSettings:
    """Clase base para la configuracion de un Lambda.

    Carga cada campo anotado desde la variable de entorno homonima en
    MAYUSCULAS. Soporta validadores custom con el patron `load_<campo>`.
    """

    def __init__(self) -> None:
        self._load_env_variables()

    def _load_env_variables(self) -> None:
        """Carga variables de entorno como atributos de la instancia.

        Primero la carga automatica; luego los validadores `load_<campo>`.
        """
        for field_name, field_type in self.__annotations__.items():
            env_value = os_environ.get(field_name.upper())

            if env_value is not None:
                if _is_str_annotation(field_type):
                    setattr(self, field_name, env_value)
                elif _is_list_annotation(field_type):
                    setattr(self, field_name, env_value.split(', '))
            elif hasattr(self, field_name):
                # Mantener el valor por defecto declarado en la clase.
                setattr(self, field_name, getattr(self, field_name))

        self._apply_custom_validators()

    def _apply_custom_validators(self) -> None:
        """Aplica validadores custom definidos como `load_<campo>`."""
        for method_name in dir(self):
            if not method_name.startswith('load_'):
                continue
            method = getattr(self, method_name)
            if not callable(method):
                continue
            field_name = method_name[5:]
            if hasattr(self, field_name):
                current_value = getattr(self, field_name)
                setattr(self, field_name, method(current_value))

    def is_valid(self) -> bool:
        """Verifica que todos los campos anotados tengan valor no vacio.

        Returns
        -------
        bool
            True si la configuracion esta completa.
        """
        for field_name in self.__annotations__:
            if not hasattr(self, field_name):
                return False
            value = getattr(self, field_name)
            if value is None:
                return False
            if isinstance(value, str) and value.strip() == '':
                return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Devuelve la configuracion como dict serializable.

        Returns
        -------
        dict[str, Any]
            Configuracion sin atributos privados.
        """
        return {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

    def to_json(self) -> str:
        """Devuelve la configuracion como string JSON.

        Returns
        -------
        str
            Configuracion en formato JSON.
        """
        return json_dumps(self.to_dict())
