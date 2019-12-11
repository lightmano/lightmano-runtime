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

"""Kubernetes Manager."""


import yaml

from kubernetes import config

from kubernetes.client.api_client import ApiClient
from kubernetes.client.rest import ApiException
from kubernetes.client import CoreV1Api
from kubernetes.client import CustomObjectsApi
from kubernetes.client import RbacAuthorizationV1Api

from lightmano.managers.k8smanager.vnfhandler import VNFInstancesHandler
from lightmano.managers.k8smanager.vnfstats import VNFStatsHandler
from lightmano.managers.k8smanager.nodestats import NodeStatsHandler
from lightmano.managers.k8smanager.vnf import VNF
from lightmano.managers.k8smanager.k8s_yaml_handler import handle_yaml

from lightmano.core.service import EService


DEFAULT_KUBECONFIG = 'k8s/lightmano.kubeconfig'#None


class K8sManager(EService):
    """Service exposing the K8s functions

    Parameters:
        kubeconfig: kubeconfig file path to be used for accessing the cluster
    """

    HANDLERS = [VNFInstancesHandler, VNFStatsHandler, NodeStatsHandler]

    def __init__(self, context, service_id, kubeconfig):

        super().__init__(context=context, service_id=service_id,
                         kubeconfig=kubeconfig)

        self.vnfs = dict()

    def start(self):
        """Start K8s manager."""

        super().start()

        if self.kubeconfig:
            config.load_kube_config(self.kubeconfig)
        else:
            config.load_incluster_config()

    def create_vnf(self, uuid, **params):

        v1 = CoreV1Api()
        namespaces = [ns.metadata.name for ns in v1.list_namespace().items]

        tenant = params["tenant"]
        if tenant not in namespaces:
            ns_file = open("k8s/_internal/namespace.yaml")
            ns = ns_file.read()
            ns_file.close()
            ns = ns.replace("-NAME-", tenant)
            ns = yaml.safe_load(ns)
            v1.create_namespace(ns)

            rbac_api = RbacAuthorizationV1Api()

            role_file = open("k8s/_internal/ns_role.yaml")
            role = role_file.read()
            role_file.close()
            role = yaml.safe_load(role)
            rbac_api.create_namespaced_role(namespace=tenant, body=role)

            rolebind_file = open("k8s/_internal/ns_role_binding.yaml")
            rolebinding = rolebind_file.read()
            rolebind_file.close()
            rolebinding = yaml.safe_load(rolebinding)
            rbac_api.create_namespaced_role_binding(namespace=tenant,
                                                    body=rolebinding)

        vnf = VNF(uuid, **params)

        handle_yaml(k8s_client=ApiClient(),
                    yaml_file=vnf.get_k8s_desc_file().name,
                    mode="create",
                    namespace=tenant)
        self.vnfs[uuid] = vnf

    def delete_vnf(self, uuid, tenant=None):

        if uuid:
            todelete_uuids = [uuid]
        else:
            todelete_uuids = [uuid for uuid in self.vnfs
                              if self.vnfs[uuid].tenant == tenant]

        for todelete_uuid in todelete_uuids:
            vnf = self.vnfs[todelete_uuid]
            handle_yaml(k8s_client=ApiClient(),
                        yaml_file=vnf.get_k8s_desc_file().name,
                        mode="delete",
                        namespace=tenant)
            del self.vnfs[todelete_uuid]

        if not [vnf for vnf in self.vnfs.values() if vnf.tenant == tenant]:
            v1 = CoreV1Api()
            try:
                v1.delete_namespace(tenant)
            except:
                pass

    def get_pod_stats(self, tenant, vnf_uuid):

        cust = CustomObjectsApi()
        data = ['metrics.k8s.io', 'v1beta1', tenant, 'pods']
        try:
            if vnf_uuid:
                data.append(self.vnfs[vnf_uuid].name)
                return cust.get_namespaced_custom_object(*data)
            else:
                return cust.list_namespaced_custom_object(*data)
        except ApiException as ex:
            raise KeyError(ex)

    def get_node_stats(self, node_name):

        cust = CustomObjectsApi()

        if node_name:
            return cust.get_cluster_custom_object('metrics.k8s.io',
                                                  'v1beta1',
                                                  'nodes',
                                                  node_name)
        else:
            return cust.list_cluster_custom_object('metrics.k8s.io',
                                                   'v1beta1',
                                                   'nodes')

    @property
    def kubeconfig(self):
        """Return element."""

        return self.params["kubeconfig"]

    @kubeconfig.setter
    def kubeconfig(self, value):
        """Set element."""

        if "kubeconfig" in self.params and self.params["kubeconfig"]:
            raise ValueError("Param kubeconfig can not be changed")

        self.params["kubeconfig"] = value


def launch(context, service_id, kubeconfig=DEFAULT_KUBECONFIG):
    """ Initialize the module. """

    return K8sManager(context, service_id, kubeconfig)
