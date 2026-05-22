"""Controller cv/awards — premios filtrados por niche."""

from controllers.cv._base import CvControllerBase


class Awards(CvControllerBase):
    """Devuelve la lista de premios."""

    service_name = 'list_awards'
