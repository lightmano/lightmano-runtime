#!/usr/bin/env python3
#
# Copyright (c) 2019 Giovanni Baggio
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

"""VNF Stats."""


import lightmano.managers.apimanager.apimanager as apimanager


# pylint: disable=W0223
class NodeStatsHandler(apimanager.APIHandler):
    """Node statistics."""

    URLS = [r"/lightmano/v1/nodestats/?",
            r"/lightmano/v1/nodestats/([a-z0-9-]*)"]

    @apimanager.validate(min_args=0, max_args=1)
    def get(self, node_name=None):

        return self.service.get_node_stats(node_name)
