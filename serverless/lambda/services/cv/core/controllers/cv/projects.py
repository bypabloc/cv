"""Controller cv/projects — proyectos filtrados por niche."""

from controllers.cv._base import CvControllerBase


class Projects(CvControllerBase):
    """Devuelve la lista de proyectos."""

    service_name = 'list_projects'
