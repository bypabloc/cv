"""Controller cv/references — referencias filtradas por niche."""

from controllers.cv._base import CvControllerBase


class References(CvControllerBase):
    """Devuelve la lista de referencias."""

    service_name = 'list_references'
