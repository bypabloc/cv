"""Controller cv/skills — categorias de skills filtradas por niche."""

from controllers.cv._base import CvControllerBase


class Skills(CvControllerBase):
    """Devuelve la lista de categorias de skills."""

    service_name = 'list_skill_categories'
