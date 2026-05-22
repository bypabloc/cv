"""Controller cv/experiences — experiencias filtradas por niche."""

from controllers.cv._base import CvControllerBase


class Experiences(CvControllerBase):
    """Devuelve la lista de experiencias."""

    service_name = 'list_experiences'
