"""Controller cv/education — educacion filtrada por niche."""

from controllers.cv._base import CvControllerBase


class Education(CvControllerBase):
    """Devuelve la lista de educacion."""

    service_name = 'list_education'
