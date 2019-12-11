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

"""Conf manager."""

import uuid

from lightmano.core.service import EService

from lightmano.managers.envmanager.envhandler import EnvHandler

from lightmano.managers.envmanager.env import Env


class EnvManager(EService):
    """Projects manager."""

    HANDLERS = [EnvHandler]

    env = None

    def start(self):
        """Start configuration manager."""

        super().start()

        if not Env.objects.all().count():
            Env(project_id=uuid.uuid4()).save()

        self.env = Env.objects.first()
        self.env.start_services()


def launch(context, service_id):
    """ Initialize the module. """

    return EnvManager(context=context, service_id=service_id)
