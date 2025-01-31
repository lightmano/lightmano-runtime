#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the license.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

"""Projects manager."""

from lightmano.main import srv_or_die
from lightmano.core.service import EService

from lightmano.managers.projectsmanager.project import Project

from lightmano.managers.projectsmanager.projectshandler import ProjectsHandler


class ProjectsManager(EService):
    """Projects manager."""

    HANDLERS = [ProjectsHandler]

    projects = {}
    accounts_manager = None

    def start(self):
        """Start projects manager."""

        super().start()

        self.accounts_manager = srv_or_die("accountsmanager")

        for project in Project.objects.all():
            self.projects[project.project_id] = project
            self.projects[project.project_id].start_services()

    def create(self, desc, project_id, owner):
        """Create new project."""

        if project_id in self.projects:
            raise ValueError("Project %s already defined" % project_id)

        if owner not in self.accounts_manager.accounts:
            raise KeyError("Username %s not found" % owner)

        project = Project(project_id=project_id, desc=desc, owner=owner)

        project.save()

        self.projects[project_id] = project

        self.projects[project_id].start_services()

        return self.projects[project_id]

    def update(self, project_id, desc):
        """Update project."""

        if project_id not in self.projects:
            raise KeyError("Project %s not found" % project_id)

        project = self.projects[project_id]

        try:

            project.desc = desc

            project.save()

        finally:

            project.refresh_from_db()

        return self.projects[project_id]

    def remove_all(self):
        """Remove all projects."""

        for project_id in list(self.projects):
            self.remove(project_id)

    def remove(self, project_id):
        """Remove project."""

        # Check if project exists
        if project_id not in self.projects:
            raise KeyError("Project %s not registered" % project_id)

        # Fetch project
        project = self.projects[project_id]

        # Stop running services
        self.projects[project_id].stop_services()

        # Delete project from datase and manager
        project.delete()
        del self.projects[project_id]


def launch(context, service_id):
    """ Initialize the module. """

    return ProjectsManager(context=context, service_id=service_id)
