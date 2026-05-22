"""Controller cv/get — CV completo (todas las colecciones)."""

from controllers.cv._base import CvControllerBase


class Get(CvControllerBase):
    """Devuelve el CV completo filtrado por niche y locale."""

    service_name = 'get_full_cv'
