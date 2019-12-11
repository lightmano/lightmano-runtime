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

"""VNF handler."""

from uuid import uuid4, UUID

import lightmano.managers.apimanager.apimanager as apimanager


# pylint: disable=W0223
class VNFInstancesHandler(apimanager.APIHandler):
    """VNF handler."""

    URLS = [r"/tenants/([a-z0-9-]*)/lightmano/v1/vnfinstances/?",
            r"/tenants/([a-z0-9-]*)/lightmano/v1/vnfinstances/([a-z0-9-]*)"]

    @apimanager.validate(min_args=1, max_args=2)
    def get(self, tenant, vnf_uuid=None):

        if vnf_uuid:
            return self.service.vnfs[vnf_uuid]

        return [vnf for vnf in self.service.vnfs if vnf.tenant == tenant]

    @apimanager.validate(returncode=201, min_args=1, max_args=2)
    def post(self, tenant, vnf_uuid_str=None, **request_data):

        if vnf_uuid_str:
            vnf_uuid = UUID(vnf_uuid_str)
        else:
            vnf_uuid = uuid4()

        self.service.create_vnf(vnf_uuid, **{'tenant': tenant, **request_data})

    @apimanager.validate(returncode=204, min_args=1, max_args=2)
    def delete(self, tenant, vnf_uuid_str=None):

        if vnf_uuid_str:
            vnf_uuid = UUID(vnf_uuid_str)
        else:
            vnf_uuid = None

        self.service.delete_vnf(vnf_uuid, tenant)
