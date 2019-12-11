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

"""VNF."""

from tempfile import NamedTemporaryFile


class VNF:

    def __init__(self, uuid, **params):

        self.uuid = uuid
        self.tenant = params["tenant"]
        self.name = params["name"]
        self.vnf_manifest = params["vnf_manifest"]
        self.params = params["params"]

        self._desc_file = None

    def get_k8s_desc_file(self):

        if not self._desc_file:
            desc_file = open("k8s/vnf_manifests/%s.yaml" % self.vnf_manifest)
            desc = desc_file.read()
            desc_file.close()
            for param_name, param_value in \
                    {**self.params , "name": self.name}.items():
                desc = desc.replace("-%s-" % param_name.upper(),
                                    str(param_value))

            desc_file = NamedTemporaryFile(mode='w')
            desc_file.write(desc)
            desc_file.flush()

            self._desc_file = desc_file

        return self._desc_file

    def to_dict(self):

        out = {
            'uuid': self.uuid,
            'tenant': self.tenant,
            'name': self.name,
            'vnf_manifest': self.vnf_manifest,
            'params': self.params
        }

        return out
