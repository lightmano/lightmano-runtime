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

from uuid import UUID

import lightmano.managers.apimanager.apimanager as apimanager


# pylint: disable=W0223
class VNFStatsHandler(apimanager.APIHandler):
    """VNF statistics."""

    URLS = [r"/tenants/([a-z0-9-]*)/lightmano/v1/vnfstats/?",
            r"/tenants/([a-z0-9-]*)/lightmano/v1/vnfstats/([a-z0-9-]*)"]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, tenant, vnf_uuid=None):

        if vnf_uuid:
            vnf_uuid = UUID(vnf_uuid)

        return self.service.get_pod_stats(tenant, vnf_uuid)
