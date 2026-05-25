"""Controller cv/profile — profile + stats + textos bilingues."""

from controllers.cv._base import CvControllerBase


class Profile(CvControllerBase):
    """Devuelve el profile. No filtra por niche (singleton)."""

    service_name = 'get_profile'
    requires_niche = False
