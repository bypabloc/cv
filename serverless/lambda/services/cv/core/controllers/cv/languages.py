"""Controller cv/languages — idiomas filtrados por niche."""

from controllers.cv._base import CvControllerBase


class Languages(CvControllerBase):
    """Devuelve la lista de idiomas."""

    service_name = 'list_languages'
