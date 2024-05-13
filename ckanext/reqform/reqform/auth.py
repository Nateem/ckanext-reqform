# -*- coding: utf-8 -*-

# Copyright (c) 2015 CoNWeT Lab., Universidad Politécnica de Madrid

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

import constants
from ckan.plugins import toolkit as tk


def create_reqform(context, data_dict):
    return {'success': True}


@tk.auth_allow_anonymous_access
def show_reqform(context, data_dict):
    return {'success': True}


def auth_if_creator(context, data_dict, show_function):
    # Sometimes data_dict only contains the 'id'
    if 'user_id' not in data_dict:
        function = tk.get_action(show_function)
        data_dict = function({'ignore_auth': True}, {'id': data_dict.get('id')})

    return {'success': data_dict['user_id'] == context.get('auth_user_obj').id}


def update_reqform(context, data_dict):
    return auth_if_creator(context, data_dict, constants.SHOW_REQFORM)


@tk.auth_allow_anonymous_access
def list_reqforms(context, data_dict):
    return {'success': True}


def delete_reqform(context, data_dict):
    return auth_if_creator(context, data_dict, constants.SHOW_REQFORM)


def close_reqform(context, data_dict):
    return auth_if_creator(context, data_dict, constants.SHOW_REQFORM)


def comment_reqform(context, data_dict):
    return {'success': True}


@tk.auth_allow_anonymous_access
def list_reqform_comments(context, data_dict):
    new_data_dict = {'id': data_dict['reqform_id']}
    return show_reqform(context, new_data_dict)


@tk.auth_allow_anonymous_access
def show_reqform_comment(context, data_dict):
    return {'success': True}


def update_reqform_comment(context, data_dict):
    return auth_if_creator(context, data_dict, constants.SHOW_REQFORM_COMMENT)


def delete_reqform_comment(context, data_dict):
    return auth_if_creator(context, data_dict, constants.SHOW_REQFORM_COMMENT)


def follow_reqform(context, data_dict):
    return {'success': True}


def unfollow_reqform(context, data_dict):
    return {'success': True}
