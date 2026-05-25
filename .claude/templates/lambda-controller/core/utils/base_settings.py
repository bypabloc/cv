"""
Clase base de configuracion: carga variables de entorno como atributos.

:Authors:
    - <Autor>

:Created:
    - YYYY-MM-DD
"""

from json import dumps as json_dumps
from os import environ as os_environ
from typing import Any
from typing import get_origin


class BaseSettings:
    """
    Clase base para la configuracion del servicio.

    Carga cada campo anotado desde la variable de entorno homonima en
    MAYUSCULAS. Soporta validadores custom con el patron load_<campo>.

    :Authors:
        - <Autor>

    :Created:
        - YYYY-MM-DD
    """

    def __init__(self) -> None:
        self._load_env_variables()

    def _load_env_variables(self) -> None:
        """
        Carga variables de entorno como atributos de la instancia.

        Primero la carga automatica; luego los validadores load_<campo>.

        :Authors:
            - <Autor>

        :Created:
            - YYYY-MM-DD
        """
        for field_name, field_type in self.__annotations__.items():
            env_value = os_environ.get(field_name.upper())

            if env_value is not None:
                if field_type is str:
                    setattr(self, field_name, env_value)
                elif get_origin(field_type) is list:
                    setattr(self, field_name, env_value.split(', '))
            elif hasattr(self, field_name):
                # Mantener el valor por defecto declarado en la clase
                setattr(self, field_name, getattr(self, field_name))

        self._apply_custom_validators()

    def _apply_custom_validators(self) -> None:
        """
        Aplica validadores custom definidos como load_<campo>.

        :Authors:
            - <Autor>

        :Created:
            - YYYY-MM-DD
        """
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
        """
        Verifica que todos los campos anotados tengan valor no vacio.

        Returns
        -------
        bool
            True si la configuracion esta completa.

        :Authors:
            - <Autor>

        :Created:
            - YYYY-MM-DD
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
        """
        Devuelve la configuracion como dict serializable.

        Returns
        -------
        dict[str, Any]
            Configuracion sin atributos privados.

        :Authors:
            - <Autor>

        :Created:
            - YYYY-MM-DD
        """
        return {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

    def to_json(self) -> str:
        """
        Devuelve la configuracion como string JSON.

        Returns
        -------
        str
            Configuracion en formato JSON.

        :Authors:
            - <Autor>

        :Created:
            - YYYY-MM-DD
        """
        return json_dumps(self.to_dict())
