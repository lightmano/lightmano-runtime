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

"""API Manager (REST Northbound Interface)."""

import inspect
import json
import base64
import re

from uuid import UUID

import tornado.web
import tornado.httpserver

from tornado.web import Application
from pymodm.errors import ValidationError

from lightmano.core.serialize import serialize
from lightmano.core.service import EService
from lightmano.main import srv_or_die

DEBUG = True
DEFAULT_PORT = 8888
DEFAULT_WEBUI = "/var/www/lightmano/"
COOKIE_SECRET = b'xyRTvZpRSUyk8/9/McQAvsQPB4Rqv0w9mBtIpH9lf1o='
LOGIN_URL = "/auth/login"


def validate(returncode=200, min_args=0, max_args=0):
    """Validate REST method."""

    def decorator(func):

        def magic(self, *args):

            try:

                if len(args) < min_args or len(args) > max_args:
                    msg = "Invalid url (%u, %u)" % (min_args, max_args)
                    raise ValueError(msg)

                params = {}

                if self.request.body and json.loads(self.request.body.decode('utf-8')):
                    params = json.loads(self.request.body.decode('utf-8'))

                if "version" in params:
                    del params["version"]

                output = func(self, *args, **params)

                if returncode == 200:
                    self.write_as_json(output)

            except KeyError as ex:
                self.send_error(404, message=str(ex))

            except ValueError as ex:
                self.send_error(400, message=str(ex))

            except AttributeError as ex:
                self.send_error(400, message=str(ex))

            except TypeError as ex:
                self.send_error(400, message=str(ex))

            except ValidationError as ex:
                self.send_error(400, message=ex.message)

            self.set_status(returncode, None)

        magic.__doc__ = func.__doc__

        return magic

    return decorator


# pylint: disable=W0223
class BaseHandler(tornado.web.RequestHandler):
    """Base Handler."""

    # service associated to this handler
    service = None

    URLS = []

    def get_current_user(self):
        """Return username of the currently logged user or None."""

        return self.get_secure_cookie("username")


class IndexHandler(BaseHandler):
    """Index page handler."""

    URLS = [r"/", r"/([a-z]*).html"]

    def get_project(self):
        """Get the current project or return None if not project is set."""

        # check if a project has been selected
        project_id = self.get_secure_cookie("project_id")

        if not project_id:
            return None

        project_id = UUID(project_id.decode('UTF-8'))

        return self.service.projects_manager.projects[project_id]

    @tornado.web.authenticated
    def get(self, args=None):
        """Render index page."""

        try:

            username = self.get_secure_cookie("username").decode('UTF-8')
            account = self.service.accounts_manager.accounts[username]

            page = "index.html" if not args else "%s.html" % args

            self.render(page,
                        username=account.username,
                        password=account.password,
                        name=account.name,
                        email=account.email,
                        project=self.get_project())

        except KeyError as ex:
            self.send_error(404, message=str(ex))

        except ValueError as ex:
            self.send_error(400, message=str(ex))


class AuthSwitchProjectHandler(BaseHandler):
    """Login page handler."""

    URLS = [r"/auth/switch_project"]

    def get(self):
        """Set the active project."""

        username = self.get_secure_cookie("username").decode('UTF-8')

        # if root deselect project
        if username == "root":
            self.clear_cookie("project_id")
            self.redirect('/')
            return

        # check if the project id is in the URL
        project_id = self.get_argument("project_id", None)

        # reset project selected
        if not project_id:
            self.clear_cookie("project_id")
            self.redirect('/')
            return

        try:

            # set project
            project_id = UUID(project_id)
            project = self.service.projects_manager.projects[project_id]

            if project.owner != username:
                self.clear_cookie("project_id")
                self.redirect('/')
                return

            self.set_secure_cookie("project_id", str(project.project_id))

        except KeyError:
            self.clear_cookie("project_id")

        except ValueError:
            self.clear_cookie("project_id")

        self.redirect('/')


class AuthLoginHandler(BaseHandler):
    """Login page handler."""

    URLS = [r"/auth/login"]

    def get(self):
        """Render login page."""

        if self.get_current_user():
            self.redirect('/')
            return

        self.render("login.html", error=self.get_argument("error", ""))

    def post(self):
        """Process login credentials."""

        username = self.get_argument("username", "")
        password = self.get_argument("password", "")

        if self.service.accounts_manager.check_permission(username, password):
            self.set_secure_cookie("username", username)
            self.redirect("/index.html")
        else:
            self.clear_cookie("username")
            self.redirect("/auth/login?error=Wrong credentials!")


class AuthLogoutHandler(BaseHandler):
    """Logout page handler."""

    URLS = [r"/auth/logout"]

    def get(self):
        """Process logout request."""

        self.clear_cookie("username")
        self.clear_cookie("project_id")
        self.redirect("/auth/login")


class APIHandler(tornado.web.RequestHandler):
    """Base class for all the REST calls."""

    # service associated to this handler
    service = None

    def write_error(self, status_code, **kwargs):
        """Write error as JSON message."""

        self.set_header('Content-Type', 'application/json')

        value = {
            "title": self._reason,
            "status_code": status_code,
            "detail": kwargs.get("message"),
        }

        self.finish(json.dumps(serialize(value), indent=4))

    def write_as_json(self, value):
        """Return reply as a json document."""

        self.write(json.dumps(serialize(value), indent=4))

    def prepare(self):
        """Prepare to handler reply."""

        self.set_header('Content-Type', 'application/json')

        return  # temporary solution

        # get requests do not require authentication
        if self.request.method == "GET":
            return

        accounts_manager = srv_or_die("accountsmanager")
        projects_manager = srv_or_die("projectsmanager")

        auth_header = self.request.headers.get('Authorization')

        if auth_header is None or not auth_header.startswith('Basic '):
            self.set_header('WWW-Authenticate', 'Basic realm=Restricted')
            self.send_error(401, message="Missing authorization header")
            return

        auth_bytes = bytes(auth_header[6:], 'utf-8')
        auth_decoded = base64.b64decode(auth_bytes).decode()
        username, password = auth_decoded.split(':', 2)

        # account does not exists
        if not accounts_manager.check_permission(username, password):
            self.send_error(401,
                            message="Invalid username/password combination")
            return

        account = accounts_manager.accounts[username]

        # root can do everything
        if account.username == "root":
            return

        # check if logged user is accessing his/her own account
        if self.request.uri.startswith("/api/v1/accounts"):

            pattern = re.compile("/api/v1/accounts/([a-zA-Z0-9:-]*)/?")
            match = pattern.match(self.request.uri)

            if match and match.group(1):
                username = match.group(1)
                if username == account.username:
                    return

        # check if logged user is accessing one of his/her projects
        if self.request.uri.startswith("/api/v1/projects"):

            pattern = re.compile("/api/v1/projects/([a-zA-Z0-9-]*)/?")
            match = pattern.match(self.request.uri)

            if match and match.group(1):
                project_id = UUID(match.group(1))
                if project_id in projects_manager.projects:
                    project = projects_manager.projects[project_id]
                    if account.username == project.owner:
                        return

        self.send_error(401, message="URI not authorized")


class APIManager(EService):
    """Service exposing the lightMANO REST API

    This service exposes the lightMANO REST API, the 'port' parameter
    specifies on which port the HTTP server should listen.

    Parameters:
        port: the port on which the HTTP server should listen (optional,
            default: 8888)
    """

    HANDLERS = [IndexHandler, AuthLoginHandler, AuthLogoutHandler,
                AuthSwitchProjectHandler]

    accounts_manager = None
    projects_manager = None

    def __init__(self, context, service_id, webui, port):

        super().__init__(context=context, service_id=service_id, webui=webui,
                         port=port)

        self.settings = {
            "static_path": self.webui + "static/",
            "cookie_secret": COOKIE_SECRET,
            "template_path": self.webui + "templates/",
            "login_url": LOGIN_URL,
            "debug": DEBUG,
        }

        self.application = Application([], **self.settings)

        self.http_server = tornado.httpserver.HTTPServer(self.application)

    @property
    def webui(self):
        """Return path to Web UI."""

        return self.params["webui"]

    @webui.setter
    def webui(self, value):
        """Set path to Web UI."""

        if "webui" in self.params and self.params["webui"]:
            raise ValueError("Param webui can not be changed")

        self.params["webui"] = value

    @property
    def port(self):
        """Return port."""

        return self.params["port"]

    @port.setter
    def port(self, value):
        """Set port."""

        if "port" in self.params and self.params["port"]:
            raise ValueError("Param port can not be changed")

        self.params["port"] = int(value)

    def start(self):
        """Start api manager."""

        super().start()

        self.accounts_manager = srv_or_die("accountsmanager")
        self.projects_manager = srv_or_die("projectsmanager")

        self.http_server.listen(self.port)

        self.log.info("Listening on port %u", self.port)

        self.http_server.start()

    def register_handler(self, handler):
        """Add a new handler class."""

        for url in handler.URLS:
            self.log.info("Registering URL: %s", url)
            self.application.add_handlers(r".*$", [(url, handler)])


def launch(context, service_id, webui=DEFAULT_WEBUI, port=DEFAULT_PORT):
    """ Initialize the module. """

    return APIManager(context=context, service_id=service_id, webui=webui,
                      port=port)
