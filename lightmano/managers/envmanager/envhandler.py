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

"""Exposes a RESTful interface ."""

import lightmano.managers.apimanager.apimanager as apimanager


# pylint: disable=W0223
class EnvHandler(apimanager.APIHandler):
    """Access the system services."""

    URLS = [r"/api/v1/env/?"]

    @apimanager.validate(min_args=0, max_args=1)
    def get(self, *args, **kwargs):
        """Get environment

        Example URLs:

             GET /api/v1/env

            {
                "mpm.managers.envmanager.envmanager": {
                    "name": "mpm.managers.envmanager.envmanager",
                    "params": {
                        "service_id": "b7d872a2-fee1-442e-b6d9-f33e5ce9fca1",
                        "every": -1
                    }
                }
            }
        """

        return self.service.env
