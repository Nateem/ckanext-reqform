# -*- coding: utf-8 -*-

# Copyright (c) 2015-2016 CoNWeT Lab., Universidad Politécnica de Madrid

# This file is part of CKAN Data Requests Extension.

# CKAN Data Requests Extension is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# CKAN Data Requests Extension is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with CKAN Data Requests Extension. If not, see <http://www.gnu.org/licenses/>.

import ckan.lib.helpers as h
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import auth
import actions
import constants
import helpers
import os
import sys

from functools import partial
from pylons import config


def get_config_bool_value(config_name, default_value=False):
    value = config.get(config_name, default_value)
    value = value if type(value) == bool else value != 'False'
    return value

def is_fontawesome_4():
    if hasattr(h, 'ckan_version'):
        ckan_version = float(h.ckan_version()[0:3])
        return ckan_version >= 2.7
    else:
        return False

def get_plus_icon():
    return 'plus-square' if is_fontawesome_4() else 'plus-sign-alt'

def get_question_icon():
    return 'question-circle' if is_fontawesome_4() else 'question-sign'


class DataRequestsPlugin(p.SingletonPlugin):

    p.implements(p.IActions)
    p.implements(p.IAuthFunctions)
    p.implements(p.IConfigurer)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.ITemplateHelpers)

    # ITranslation only available in 2.5+
    try:
        p.implements(p.ITranslation)
    except AttributeError:
        pass

    def __init__(self, name=None):
        self.comments_enabled = get_config_bool_value('ckan.reqform.comments', True)
        self._show_reqforms_badge = get_config_bool_value('ckan.reqform.show_reqforms_badge')
        self.name = 'reqform'

    ######################################################################
    ############################## IACTIONS ##############################
    ######################################################################

    def get_actions(self):
        additional_actions = {
            constants.CREATE_REQFORM: actions.create_reqform,
            constants.SHOW_REQFORM: actions.show_reqform,
            constants.UPDATE_REQFORM: actions.update_reqform,
            constants.LIST_REQFORMS: actions.list_reqforms,
            constants.DELETE_REQFORM: actions.delete_reqform,
            constants.CLOSE_REQFORM: actions.close_reqform,
            constants.FOLLOW_REQFORM: actions.follow_reqform,
            constants.UNFOLLOW_REQFORM: actions.unfollow_reqform,
        }

        if self.comments_enabled:
            additional_actions[constants.COMMENT_REQFORM] = actions.comment_reqform
            additional_actions[constants.LIST_REQFORM_COMMENTS] = actions.list_reqform_comments
            additional_actions[constants.SHOW_REQFORM_COMMENT] = actions.show_reqform_comment
            additional_actions[constants.UPDATE_REQFORM_COMMENT] = actions.update_reqform_comment
            additional_actions[constants.DELETE_REQFORM_COMMENT] = actions.delete_reqform_comment

        return additional_actions

    ######################################################################
    ########################### AUTH FUNCTIONS ###########################
    ######################################################################

    def get_auth_functions(self):
        auth_functions = {
            constants.CREATE_REQFORM: auth.create_reqform,
            constants.SHOW_REQFORM: auth.show_reqform,
            constants.UPDATE_REQFORM: auth.update_reqform,
            constants.LIST_REQFORMS: auth.list_reqforms,
            constants.DELETE_REQFORM: auth.delete_reqform,
            constants.CLOSE_REQFORM: auth.close_reqform,
            constants.FOLLOW_REQFORM: auth.follow_reqform,
            constants.UNFOLLOW_REQFORM: auth.unfollow_reqform,
        }

        if self.comments_enabled:
            auth_functions[constants.COMMENT_REQFORM] = auth.comment_reqform
            auth_functions[constants.LIST_REQFORM_COMMENTS] = auth.list_reqform_comments
            auth_functions[constants.SHOW_REQFORM_COMMENT] = auth.show_reqform_comment
            auth_functions[constants.UPDATE_REQFORM_COMMENT] = auth.update_reqform_comment
            auth_functions[constants.DELETE_REQFORM_COMMENT] = auth.delete_reqform_comment

        return auth_functions

    ######################################################################
    ############################ ICONFIGURER #############################
    ######################################################################

    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')

        # Register this plugin's fanstatic directory with CKAN.
        tk.add_public_directory(config, 'public')

        # Register this plugin's fanstatic directory with CKAN.
        tk.add_resource('fanstatic', 'reqform')

    ######################################################################
    ############################## IROUTES ###############################
    ######################################################################

    def before_map(self, m):
        # Data Requests index
        m.connect('datarequests_index', "/%s" % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='index', conditions=dict(method=['GET']))

        # Create a Request Form
        m.connect('/%s/new' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='new', conditions=dict(method=['GET', 'POST']))

        # Show a Request Form
        m.connect('show_reqform', '/%s/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='show', conditions=dict(method=['GET']), ckan_icon=get_question_icon())

        # Update a Request Form
        m.connect('/%s/edit/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='update', conditions=dict(method=['GET', 'POST']))

        # Delete a Request Form
        m.connect('/%s/delete/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='delete', conditions=dict(method=['POST']))

        # Close a Request Form
        m.connect('/%s/close/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='close', conditions=dict(method=['GET', 'POST']))

        # Request Form that belongs to an organization
        m.connect('organization_reqforms', '/organization/%s/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='organization_reqforms', conditions=dict(method=['GET']),
                  ckan_icon=get_question_icon())

        # Request Form that belongs to an user
        m.connect('user_reqforms', '/user/%s/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='user_reqforms', conditions=dict(method=['GET']),
                  ckan_icon=get_question_icon())

        # Follow & Unfollow
        m.connect('/%s/follow/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='follow', conditions=dict(method=['POST']))

        m.connect('/%s/unfollow/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                  controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                  action='unfollow', conditions=dict(method=['POST']))

        if self.comments_enabled:
            # Comment, update and view comments (of) a Request Form
            m.connect('comment_reqform', '/%s/comment/{id}' % constants.DATAREQUESTS_MAIN_PATH,
                      controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                      action='comment', conditions=dict(method=['GET', 'POST']), ckan_icon='comment')

            # Delete data request
            m.connect('/%s/comment/{reqform_id}/delete/{comment_id}' % constants.DATAREQUESTS_MAIN_PATH,
                      controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                      action='delete_comment', conditions=dict(method=['GET', 'POST']))

        return m

    ######################################################################
    ######################### ITEMPLATESHELPER ###########################
    ######################################################################

    def get_helpers(self):
        return {
            'show_comments_tab': lambda: self.comments_enabled,
            'get_comments_number': helpers.get_comments_number,
            'get_comments_badge': helpers.get_comments_badge,
            'get_open_reqforms_number': helpers.get_open_reqforms_number,
            'get_open_reqforms_badge': partial(helpers.get_open_reqforms_badge, self._show_reqforms_badge),
            'get_plus_icon': get_plus_icon,
            'is_following_reqform': helpers.is_following_reqform
        }

    ######################################################################
    ########################### ITRANSLATION #############################
    ######################################################################

    # The following methods are copied from ckan.lib.plugins.DefaultTranslation
    # and have been modified to fix a bug in CKAN 2.5.1 that prevents CKAN from
    # starting. In addition by copying these methods, it is ensured that Data
    # Requests can be used even if Itranslation isn't available (less than 2.5)

    def i18n_directory(self):
        '''Change the directory of the *.mo translation files
        The default implementation assumes the plugin is
        ckanext/myplugin/plugin.py and the translations are stored in
        i18n/
        '''
        # assume plugin is called ckanext.<myplugin>.<...>.PluginClass
        extension_module_name = '.'.join(self.__module__.split('.')[:3])
        module = sys.modules[extension_module_name]
        return os.path.join(os.path.dirname(module.__file__), 'i18n')

    def i18n_locales(self):
        '''Change the list of locales that this plugin handles
        By default the will assume any directory in subdirectory in the
        directory defined by self.directory() is a locale handled by this
        plugin
        '''
        directory = self.i18n_directory()
        return [ d for
                 d in os.listdir(directory)
                 if os.path.isdir(os.path.join(directory, d))
        ]

    def i18n_domain(self):
        '''Change the gettext domain handled by this plugin
        This implementation assumes the gettext domain is
        ckanext-{extension name}, hence your pot, po and mo files should be
        named ckanext-{extension name}.mo'''
        return 'ckanext-{name}'.format(name=self.name)
