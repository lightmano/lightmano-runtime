#!/usr/bin/env python3
#
# Copyright (c) 2019 Roberto Riggio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
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

"""Project Class."""

from pymodm import fields

from lightmano.managers.envmanager.env import Env
from lightmano.main import srv_or_die
from lightmano.core.serialize import serializable_dict


@serializable_dict
class Project(Env):
    """Project class.

    Attributes:
        owner: The username of the user that requested this pool
    """

    owner = fields.CharField(required=True)
    desc = fields.CharField(required=True)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Save pointer to ProjectManager
        self.manager = srv_or_die("projectsmanager")

    def to_dict(self):
        """Return JSON-serializable representation of the object."""

        output = super().to_dict()

        output['owner'] = self.owner

        output['desc'] = self.desc

        return output
