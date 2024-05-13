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

import ckanext.reqform.constants as constants
import ckanext.reqform.controllers.ui_controller as controller
import unittest

from mock import MagicMock
from nose_parameterized import parameterized


INDEX_FUNCTION = 'index'
ORGANIZATION_REQFORMS_FUNCTION = 'organization_reqforms'
USER_REQFORMS_FUNCTION = 'user_reqforms'


class UIControllerTest(unittest.TestCase):

    def setUp(self):
        self._plugins = controller.plugins
        controller.plugins = MagicMock()

        self._tk = controller.tk
        controller.tk = MagicMock()
        controller.tk._ = self._tk._
        controller.tk.ValidationError = self._tk.ValidationError
        controller.tk.NotAuthorized = self._tk.NotAuthorized
        controller.tk.ObjectNotFound = self._tk.ObjectNotFound

        self._c = controller.c
        controller.c = MagicMock()

        self._request = controller.request
        controller.request = MagicMock()

        self._model = controller.model
        controller.model = MagicMock()

        self._request = controller.request
        controller.request = MagicMock()

        self._helpers = controller.helpers
        controller.helpers = MagicMock()

        self._base = controller.base
        controller.base = MagicMock()

        self._reqforms_per_page = controller.constants.DATAREQUESTS_PER_PAGE

        self.expected_context = {
            'model': controller.model,
            'session': controller.model.Session,
            'user': controller.c.user,
            'auth_user_obj': controller.c.userobj
        }

        self.controller_instance = controller.DataRequestsUI()

    def tearDown(self):
        controller.plugins = self._plugins
        controller.tk = self._tk
        controller.c = self._c
        controller.request = self._request
        controller.model = self._model
        controller.request = self._request
        controller.helpers = self._helpers
        controller.base = self._base
        controller.constants.DATAREQUESTS_PER_PAGE = self._reqforms_per_page


    ######################################################################
    ################################# AUX ################################
    ######################################################################

    def _test_not_authorized(self, function, action, check_access_func):
        reqform_id = 'example_uuidv4'
        controller.tk.check_access.side_effect = controller.tk.NotAuthorized('User not authorized')

        # Call the function
        result = function(reqform_id)

        # Assertions
        controller.tk.check_access.assert_called_once_with(check_access_func, self.expected_context, {'id': reqform_id})
        controller.tk.abort.assert_called_once_with(403, 'You are not authorized to %s the Request Form %s' % (action, reqform_id))
        self.assertEquals(0, controller.tk.render.call_count)
        self.assertIsNone(result)

    def _test_not_found(self, function, get_action_func):
        reqform_id = 'example_uuidv4'

        def _get_action(action):
            if action == get_action_func:
                return MagicMock(side_effect=controller.tk.ObjectNotFound('Data set not found'))
            elif action == constants.SHOW_REQFORM:
                # test_close_not_found needs show_reqform to return closed = False to work
                return MagicMock(return_value={'closed': False})

        controller.tk.get_action.side_effect = _get_action

        # Call the function
        result = function(reqform_id)

        # Assertions
        controller.tk.get_action.assert_any_call(get_action_func)
        controller.tk.abort.assert_called_once_with(404, 'Request Form %s not found' % reqform_id)
        self.assertEquals(0, controller.tk.render.call_count)
        self.assertIsNone(result)


    ######################################################################
    ################################# NEW ################################
    ######################################################################

    @parameterized.expand([
        (True,),
        (False,)
    ])
    def test_new_no_post(self, authorized):
        controller.tk.response.location = None
        controller.tk.response.status_int = 200
        controller.request.POST = {}

        # Raise exception if the user is not authorized to create a new data request
        if not authorized:
            controller.tk.check_access.side_effect = controller.tk.NotAuthorized('User not authorized')

        result = self.controller_instance.new()

        controller.tk.check_access.assert_called_once_with(constants.CREATE_REQFORM, self.expected_context, None)

        if authorized:
            self.assertEquals(0, controller.tk.abort.call_count)
            self.assertEquals(controller.tk.render.return_value, result)
            controller.tk.render.assert_called_once_with('reqform/new.html')
        else:
            controller.tk.abort.assert_called_once_with(403, 'Unauthorized to create a Request Form')
            self.assertEquals(0, controller.tk.render.call_count)

        self.assertIsNone(controller.tk.response.location)
        self.assertEquals(200, controller.tk.response.status_int)
        self.assertEquals({}, controller.c.errors)
        self.assertEquals({}, controller.c.errors_summary)
        self.assertEquals({}, controller.c.reqform)

    @parameterized.expand([
        (False, False),
        (True,  False),
        (True,  True)
    ])
    def test_new_post_content(self, authorized, validation_error):
        reqform_id = 'this-represents-an-uuidv4()'

        # Raise exception if the user is not authorized to create a new data request
        if not authorized:
            controller.tk.check_access.side_effect = controller.tk.NotAuthorized('User not authorized')

        # Raise exception when the user input is not valid
        action = controller.tk.get_action.return_value
        if validation_error:
            action.side_effect = controller.tk.ValidationError({'Title': ['error1', 'error2'],
                                                                'Description': ['error3, error4']})
        else:
            action.return_value = {'id': reqform_id}

        # Create the request
        request_data = controller.request.POST = {
            'title': 'Example Title',
            'description': 'Example Description',
            'organization_id': 'organization uuid4'
        }
        result = self.controller_instance.new()

        # Authorize function has been called
        controller.tk.check_access.assert_called_once_with(constants.CREATE_REQFORM, 
                                                           self.expected_context, None)

        if authorized:
            self.assertEquals(0, controller.tk.abort.call_count)
            self.assertEquals(controller.tk.render.return_value, result)
            controller.tk.render.assert_called_once_with('reqform/new.html')

            controller.tk.get_action.return_value.assert_called_once_with(self.expected_context, request_data)

            if validation_error:
                errors_summary = {}
                for key, error in action.side_effect.error_dict.items():
                    errors_summary[key] = ', '.join(error)

                self.assertEquals(action.side_effect.error_dict, controller.c.errors)
                expected_request_data = request_data.copy()
                expected_request_data['id'] = ''
                self.assertEquals(expected_request_data, controller.c.reqform)
                self.assertEquals(errors_summary, controller.c.errors_summary)
            else:
                self.assertEquals({}, controller.c.errors)
                self.assertEquals({}, controller.c.errors_summary)
                self.assertEquals({}, controller.c.reqform)
                controller.helpers.url_for.assert_called_once_with(
                    controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                    action='show', id=reqform_id)
                controller.tk.redirect_to.assert_called_once_with(controller.helpers.url_for.return_value)
        else:
            controller.tk.abort.assert_called_once_with(403, 'Unauthorized to create a Request Form')
            self.assertEquals(0, controller.tk.render.call_count)


    ######################################################################
    ################################ SHOW ################################
    ######################################################################

    def test_show_not_authorized(self):
        self._test_not_authorized(self.controller_instance.show, 'view', constants.SHOW_REQFORM)

    def test_show_not_found(self):
        self._test_not_found(self.controller_instance.show, constants.SHOW_REQFORM)

    @parameterized.expand({
        (False, False, None),
        (False, True,  None),
        (True,  False, None),
        (True,  True,  None),
        (False, False, 'uudiv4', False),
        (False, True,  'uudiv4', False),
        (True,  False, 'uudiv4', False),
        (True,  True,  'uudiv4', False),
        (False, False, 'uudiv4', True),
        (False, True,  'uudiv4', True),
        (True,  False, 'uudiv4', True),
        (True,  True,  'uudiv4', True)
    })
    def test_show_found(self, user_show_exception, organization_show_exception, accepted_dataset, package_show_exception=False):

        reqform_id = 'example_uuidv4'
        default_user = {'display_name': 'User Display Name'}
        default_organization = {'display_name': 'Organization Name'}
        default_package = {'title': 'Package'}

        show_reqform = MagicMock(return_value={
            'id': 'example_uuidv4',
            'user_id': 'example_uuidv4_user',
            'organization_id': 'example_uuidv4_organization',
            'accepted_dataset_id': accepted_dataset,
            'user': default_user,
            'organization': default_organization,
            'accepted_dataset': default_package
        })

        def _user_show(context, req_form):
            if user_show_exception:
                raise controller.tk.ObjectNotFound('User not Found')
            else:
                return default_user

        def _organization_show(context, req_form):
            if organization_show_exception:
                raise controller.tk.ObjectNotFound('Organization not Found')
            else:
                return default_organization

        def _package_show(context, req_form):
            if package_show_exception:
                raise controller.tk.ObjectNotFound('Package nof Found')
            else:
                return default_package

        user_show = MagicMock(side_effect=_user_show)
        organization_show = MagicMock(side_effect=_organization_show)
        package_show = MagicMock(side_effect=_package_show)

        def _get_action(action):
            if action == 'show_reqform':
                return show_reqform
            elif action == 'user_show':
                return user_show
            elif action == 'organization_show':
                return organization_show
            elif action == 'package_show':
                return package_show

        controller.tk.get_action.side_effect = _get_action

        # Call the function
        result = self.controller_instance.show(reqform_id)

        # Authorize function has been called
        controller.tk.check_access.assert_called_once_with(constants.SHOW_REQFORM, self.expected_context,
                                                           {'id': reqform_id})

        # Assertions
        expected_reqform = show_reqform.return_value.copy()
        if not user_show_exception:
            expected_reqform['user'] = default_user
        if not organization_show_exception:
            expected_reqform['organization'] = default_organization
        if not package_show_exception and accepted_dataset:
            expected_reqform['accepted_dataset'] = default_package
        self.assertEquals(expected_reqform, controller.c.reqform)
        controller.tk.render.assert_called_once_with('reqform/show.html')
        self.assertEquals(controller.tk.render.return_value, result)


    ######################################################################
    ############################### UPDATE ###############################
    ######################################################################

    def test_update_not_authorized(self):
        self._test_not_authorized(self.controller_instance.update, 'update', constants.UPDATE_REQFORM)

    def test_update_not_found(self):
        self._test_not_found(self.controller_instance.update, constants.UPDATE_REQFORM)

    def test_update_no_post_content(self):
        controller.tk.response.location = None
        controller.tk.response.status_int = 200
        controller.request.POST = {}

        reqform_id = 'example_uuidv4'
        reqform = {'id': 'uuid4', 'user_id': 'user_uuid4', 'title': 'example_title'}
        show_reqform = controller.tk.get_action.return_value
        show_reqform.return_value = reqform

        # Call the function
        result = self.controller_instance.update(reqform_id)

        # Authorize function has been called
        controller.tk.check_access.assert_called_once_with(constants.UPDATE_REQFORM, self.expected_context, {'id': reqform_id})

        # Assertions
        controller.tk.render.assert_called_once_with('reqform/edit.html')
        self.assertEquals(result, controller.tk.render.return_value)

        self.assertIsNone(controller.tk.response.location)
        self.assertEquals(200, controller.tk.response.status_int)
        self.assertEquals({}, controller.c.errors)
        self.assertEquals({}, controller.c.errors_summary)
        self.assertEquals(reqform, controller.c.reqform)
        self.assertEquals(reqform['title'], controller.c.original_title)

    @parameterized.expand([
        (False, False),
        (True,  False),
        (True,  True)
    ])
    def test_update_post_content(self, authorized, validation_error):
        reqform_id = 'this-represents-an-uuidv4()'

        original_dr = {
            'id': reqform_id,
            'title': 'A completly different title',
            'description': 'Other description'
        }

        # Set up the get_action function
        show_reqform = MagicMock(return_value=original_dr)
        update_reqform = MagicMock()

        def _get_action(action):
            if action == constants.SHOW_REQFORM:
                return show_reqform
            else:
                return update_reqform

        controller.tk.get_action.side_effect = _get_action

        # Raise exception if the user is not authorized to create a new data request
        if not authorized:
            controller.tk.check_access.side_effect = controller.tk.NotAuthorized('User not authorized')

        # Raise exception when the user input is not valid
        if validation_error:
            update_reqform.side_effect = controller.tk.ValidationError({'Title': ['error1', 'error2'],
                                                                            'Description': ['error3, error4']})
        else:
            update_reqform.return_value = {'id': reqform_id}

        # Create the request
        request_data = controller.request.POST = {
            'id': reqform_id,
            'title': 'Example Title',
            'description': 'Example Description',
            'organization_id': 'organization uuid4'
        }
        result = self.controller_instance.update(reqform_id)

        # Authorize function has been called
        controller.tk.check_access.assert_called_once_with(constants.UPDATE_REQFORM, self.expected_context, {'id': reqform_id})

        if authorized:
            self.assertEquals(0, controller.tk.abort.call_count)
            self.assertEquals(controller.tk.render.return_value, result)
            controller.tk.render.assert_called_once_with('reqform/edit.html')

            show_reqform.assert_called_once_with(self.expected_context, {'id': reqform_id})
            update_reqform.assert_called_once_with(self.expected_context, request_data)

            if validation_error:
                errors_summary = {}
                for key, error in update_reqform.side_effect.error_dict.items():
                    errors_summary[key] = ', '.join(error)

                self.assertEquals(update_reqform.side_effect.error_dict, controller.c.errors)
                expected_request_data = request_data.copy()
                expected_request_data['id'] = reqform_id
                self.assertEquals(expected_request_data, controller.c.reqform)
                self.assertEquals(errors_summary, controller.c.errors_summary)
                self.assertEquals(original_dr['title'], controller.c.original_title)
            else:
                self.assertEquals({}, controller.c.errors)
                self.assertEquals({}, controller.c.errors_summary)
                self.assertEquals(original_dr, controller.c.reqform)
                controller.helpers.url_for.assert_called_once_with(
                    controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                    action='show', id=reqform_id)
                controller.tk.redirect_to.assert_called_once_with(controller.helpers.url_for.return_value)
        else:
            controller.tk.abort.assert_called_once_with(403, 'You are not authorized to update the Request Form %s' % reqform_id)
            self.assertEquals(0, controller.tk.render.call_count)


    ######################################################################
    ################################ INDEX ###############################
    ######################################################################

    def test_index_not_authorized(self):
        controller.tk.check_access.side_effect = controller.tk.NotAuthorized('User is not authorized')
        organization_name = 'org'
        controller.request.GET = {'organization': organization_name}

        # Call the function
        result = self.controller_instance.index()

        # Assertions
        expected_data_req = {'organization_id': organization_name, 'limit': 10, 'offset': 0, 'sort': 'desc'}
        controller.tk.check_access.assert_called_once_with(constants.LIST_REQFORMS, self.expected_context, expected_data_req)
        controller.tk.abort.assert_called_once_with(403, 'Unauthorized to list Data Requests')
        self.assertEquals(0, controller.tk.get_action.call_count)
        self.assertEquals(0, controller.tk.render.call_count)
        self.assertIsNone(result)

    def test_index_invalid_page(self):
        controller.request.GET = controller.request.params = {'page': '2a'}

        # Call the function
        result = self.controller_instance.index()

        # Assertions
        controller.tk.abort.assert_called_once_with(400, '"page" parameter must be an integer')
        self.assertEquals(0, controller.tk.check_access.call_count)
        self.assertEquals(0, controller.tk.get_action.call_count)
        self.assertEquals(0, controller.tk.render.call_count)
        self.assertIsNone(result)

    @parameterized.expand([
        (INDEX_FUNCTION, '1', 'conwet', '', 0,    10),
        (INDEX_FUNCTION, '2', 'conwet', '', 10,   10),
        (INDEX_FUNCTION, '7', 'conwet', '', 60,   10),
        (INDEX_FUNCTION, '1', 'conwet', '', 0,    25, 25),
        (INDEX_FUNCTION, '2', 'conwet', '', 25,   25, 25),
        (INDEX_FUNCTION, '7', 'conwet', '', 150,  25, 25),
        (INDEX_FUNCTION, '5', None,     '', 40,   10),
        (INDEX_FUNCTION, '1', None,     '', 0,    10, 10, 'asc'),
        (INDEX_FUNCTION, '1', None,     '', 0,    10, 10, 'desc'),
        (INDEX_FUNCTION, '1', None,     '', 0,    10, 10, 'invalid'),
        (INDEX_FUNCTION, '1', None,     '', 0,    10, 10, None,   'free-text'),
        (ORGANIZATION_REQFORMS_FUNCTION, '1', 'conwet', '',     0,    10),
        (ORGANIZATION_REQFORMS_FUNCTION, '2', 'conwet', '',     10,   10),
        (ORGANIZATION_REQFORMS_FUNCTION, '7', 'conwet', '',     60,   10),
        (ORGANIZATION_REQFORMS_FUNCTION, '1', 'conwet', '',     0,    25, 25),
        (ORGANIZATION_REQFORMS_FUNCTION, '2', 'conwet', '',     25,   25, 25),
        (ORGANIZATION_REQFORMS_FUNCTION, '7', 'conwet', '',     150,  25, 25),
        (ORGANIZATION_REQFORMS_FUNCTION, '1', 'conwet', '',     0,    10, 10, 'asc'),
        (ORGANIZATION_REQFORMS_FUNCTION, '1', 'conwet', '',     0,    10, 10, 'desc'),
        (ORGANIZATION_REQFORMS_FUNCTION, '1', 'conwet', '',     0,    10, 10, 'invalid', ''),
        (ORGANIZATION_REQFORMS_FUNCTION, '1', 'conwet', '',     0,    10, 10, None,      'free-text'),
        (USER_REQFORMS_FUNCTION,         '1', 'conwet', 'ckan', 0,    10),
        (USER_REQFORMS_FUNCTION,         '1', '',       'ckan', 0,    10),
        (USER_REQFORMS_FUNCTION,         '7', 'conwet', 'ckan', 60,   10),
        (USER_REQFORMS_FUNCTION,         '7', '',       'ckan', 150,  25, 25),
        (USER_REQFORMS_FUNCTION,         '1', '',       'ckan', 0,    10, 10, 'asc'),
        (USER_REQFORMS_FUNCTION,         '1', '',       'ckan', 0,    10, 10, 'desc'),
        (USER_REQFORMS_FUNCTION,         '1', '',       'ckan', 0,    10, 10, 'invalid'),
        (USER_REQFORMS_FUNCTION,         '1', '',       'ckan', 0,    10, 10, None,      'free-text'),
    ])
    def test_index_organization_user_dr(self, func, page, organization, user, expected_offset,
                                        expected_limit, datarequests_per_page=10, sort=None,
                                        query=None):
        params = {}
        user_show_action = 'user_show'
        organization_show_action = 'organization_show'
        base_url = 'http://someurl.com/somepath/otherpath'
        expected_sort = sort if sort and sort in ['asc', 'desc'] else 'desc'

        # Expected data_dict
        expected_data_dict = {
            'offset': expected_offset,
            'limit': expected_limit,
            'sort': expected_sort
        }

        if query:
            expected_data_dict['q'] = query

        # Set datarequests_per_page
        constants.DATAREQUESTS_PER_PAGE = datarequests_per_page

        # Get parameters
        controller.request.GET = controller.request.params = {}

        # Set page
        if page:
            controller.request.GET['page'] = page

        # Set the organization in the correct place depending on the function
        if func == ORGANIZATION_REQFORMS_FUNCTION:
            params['id'] = organization
            expected_data_dict['organization_id'] = organization
        else:
            if func == USER_REQFORMS_FUNCTION:
                params['id'] = user
                expected_data_dict['user_id'] = user

            if organization:
                controller.request.GET['organization'] = organization
                expected_data_dict['organization_id'] = organization

        if sort:
            controller.request.GET['sort'] = sort

        if query:
            controller.request.GET['q'] = query

        # Mocking
        user_show = MagicMock()
        organization_show = MagicMock()
        list_reqforms = MagicMock()

        def _get_action(action):
            if action == organization_show_action:
                return organization_show
            elif action == 'user_show':
                return user_show
            else:
                return list_reqforms

        controller.tk.get_action.side_effect = _get_action
        controller.helpers.url_for.return_value = base_url

        # Call the function
        function = getattr(self.controller_instance, func)
        result = function(**params)

        # Assertions
        controller.tk.check_access.assert_called_once_with(constants.LIST_REQFORMS,
                                                           self.expected_context,
                                                           expected_data_dict)

        # Specific assertions depending on the function called
        if func == INDEX_FUNCTION:
            controller.tk.get_action.assert_called_once_with(constants.LIST_REQFORMS)
            self.assertEquals(0, organization_show.call_count)
            expected_render_page = 'reqform/index.html'
        elif func == ORGANIZATION_REQFORMS_FUNCTION:
            self.assertEquals(2, controller.tk.get_action.call_count)
            controller.tk.get_action.assert_any_call(constants.LIST_REQFORMS)
            controller.tk.get_action.assert_any_call(organization_show_action)
            self.assertEquals(organization_show.return_value, controller.c.group_dict)
            organization_show.assert_called_once_with(self.expected_context, {'id': organization})
            expected_render_page = 'organization/reqform.html'
        elif func == USER_REQFORMS_FUNCTION:
            self.assertEquals(2, controller.tk.get_action.call_count)
            controller.tk.get_action.assert_any_call(constants.LIST_REQFORMS)
            controller.tk.get_action.assert_any_call(user_show_action)
            self.assertEquals(user_show.return_value, controller.c.user_dict)
            user_show.assert_called_once_with(self.expected_context, {'id': user, 'include_num_followers': True})
            expected_render_page = 'user/reqform.html'

        # Check the values put in c
        list_reqforms.assert_called_once_with(self.expected_context, expected_data_dict)
        expected_response = list_reqforms.return_value
        self.assertEquals(expected_response['count'], controller.c.reqform_count)
        self.assertEquals(expected_response['result'], controller.c.reqform)
        self.assertEquals(expected_response['facets'], controller.c.search_facets)
        self.assertEquals(controller.helpers.Page.return_value, controller.c.page)

        # Check the pager
        page_arguments = controller.helpers.Page.call_args[1]
        self.assertEquals(datarequests_per_page, page_arguments['items_per_page'])
        self.assertEquals(int(page), page_arguments['page'])
        self.assertEquals(expected_response['count'], page_arguments['item_count'])
        self.assertEquals(expected_response['result'], page_arguments['collection'])
        silly_page = 72
        query_param = 'q={0}&'.format(query) if query else ''
        self.assertEquals("%s?%ssort=%s&page=%d" % (base_url, query_param, expected_sort, silly_page),
                          page_arguments['url'](q=query,page=silly_page))

        # When URL function is called, helpers.url_for is called to get the final URL
        if func == INDEX_FUNCTION:
            controller.helpers.url_for.assert_called_once_with(
                controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                action='index')
        elif func == ORGANIZATION_REQFORMS_FUNCTION:
            controller.helpers.url_for.assert_called_once_with(
                controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                action='organization_reqforms', id=organization)
        elif func == USER_REQFORMS_FUNCTION:
            controller.helpers.url_for.assert_called_once_with(
                controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
                action='user_reqforms', id=user)

        # Check the facets
        expected_facet_titles = {}
        expected_facet_titles['state'] = controller.tk._('State')
        if func != ORGANIZATION_REQFORMS_FUNCTION:
            expected_facet_titles['organization'] = controller.tk._('Organizations')

        self.assertEquals(expected_facet_titles, controller.c.facet_titles)

        # Check that the render functions has been called with the suitable parameters
        expected_user = controller.c.user_dict if hasattr(controller.c, 'user_dict') else None
        self.assertEquals(controller.tk.render.return_value, result)
        controller.tk.render.assert_called_once_with(expected_render_page, extra_vars={'user_dict': expected_user, 'group_type': 'organization'})


    ######################################################################
    ############################### DELETE ###############################
    ######################################################################

    def test_delete_not_authorized(self):
        self._test_not_authorized(self.controller_instance.delete, 'delete', constants.DELETE_REQFORM)

    def test_delete_not_found(self):
        self._test_not_found(self.controller_instance.delete, constants.DELETE_REQFORM)

    def test_delete(self):
        reqform_id = 'example_uuidv4'
        reqform = {
            'id': reqform_id,
            'title': 'DR Title',
            'organization_id': 'example_uuidv4_organization'
        }

        delete_reqform = controller.tk.get_action.return_value
        delete_reqform.return_value = reqform

        # Call the function
        result = self.controller_instance.delete(reqform_id)

        # Assertions
        # The result
        self.assertIsNone(result)

        # Functions has been called
        expected_data_dict = {'id': reqform_id}
        controller.tk.check_access.assert_called_once_with(constants.DELETE_REQFORM, self.expected_context, expected_data_dict)
        delete_reqform.assert_called_once_with(self.expected_context, expected_data_dict)
        controller.helpers.flash_notice.assert_called_once_with(controller.tk._(
            'Request Form %s has been deleted' % reqform.get('title')))

        # Redirection
        controller.helpers.url_for.assert_called_once_with(
            controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
            action='index')
        controller.tk.redirect_to.assert_called_once_with(controller.helpers.url_for.return_value)


    ######################################################################
    ################################ CLOSE ###############################
    ######################################################################

    def test_close_not_authorized(self):
        self._test_not_authorized(self.controller_instance.close, 'close', constants.CLOSE_REQFORM)

    def test_close_not_found(self):
        self._test_not_found(self.controller_instance.close, constants.CLOSE_REQFORM)

    @parameterized.expand([
        (None,),
        ('organization_uuidv4',)
    ])
    def test_close(self, organization, post_content={}, errors={}, errors_summary={}, close_reqform=MagicMock()):
        controller.tk.response.location = None
        controller.tk.response.status_int = 200
        controller.request.POST = post_content

        reqform_id = 'example_uuidv4'
        reqform = {'id': 'uuid4', 'user_id': 'user_uuid4', 'title': 'example_title'}
        if organization:
            reqform['organization_id'] = organization

        show_reqform = MagicMock(return_value=reqform)
        packages_org = [{'name': 'packo1', 'title': 'packo1'}, {'name': 'packo2', 'title': 'packo2'}]
        organization_show = MagicMock(return_value={'packages': packages_org})
        packages_no_org = [{'name': 'pack1', 'title': 'pack1'}, {'name': 'pack2', 'title': 'pack2'}]
        package_search = MagicMock(return_value={'results': packages_no_org})

        def _get_action(action):
            if action == 'organization_show':
                return organization_show
            elif action == 'package_search':
                return package_search
            elif action == constants.SHOW_REQFORM:
                return show_reqform
            elif action == constants.CLOSE_REQFORM:
                return close_reqform

        controller.tk.get_action.side_effect = _get_action

        # Call the function
        result = self.controller_instance.close(reqform_id)

        # Check that the methods has been called
        controller.tk.check_access.assert_called_once_with(constants.CLOSE_REQFORM, self.expected_context, {'id': reqform_id})
        show_reqform.assert_called_once_with(self.expected_context, {'id': reqform_id})

        if organization:
            organization_show.assert_called_once_with({'ignore_auth': True}, {'id': organization, 'include_datasets': True})
        else:
            package_search.assert_called_once_with({'ignore_auth': True}, {'rows': 500})

        # Assertions
        controller.tk.render.assert_called_once_with('reqform/close.html')
        self.assertEquals(result, controller.tk.render.return_value)

        self.assertIsNone(controller.tk.response.location)
        self.assertEquals(200, controller.tk.response.status_int)
        self.assertEquals(errors, controller.c.errors)
        self.assertEquals(errors_summary, controller.c.errors_summary)
        self.assertEquals(reqform, controller.c.reqform)

        expected_datasets = packages_org if organization else packages_no_org
        self.assertEquals(expected_datasets, controller.c.datasets)

    def test_close_post_no_error(self):
        controller.request.POST = {'accepted_dataset': 'example_ds'}

        reqform_id = 'example_uuidv4'
        reqform = {'id': 'uuid4', 'user_id': 'user_uuid4', 'title': 'example_title'}
        show_reqform = MagicMock(return_value=reqform)
        close_reqform = MagicMock(return_value=reqform)

        def _get_action(action):
            if action == constants.SHOW_REQFORM:
                return show_reqform
            elif action == constants.CLOSE_REQFORM:
                return close_reqform

        controller.tk.get_action.side_effect = _get_action

        # Call the function
        result = self.controller_instance.close(reqform_id)

        # Checks
        controller.helpers.url_for.assert_called_once_with(
            controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
            action='show', id=reqform_id)
        controller.tk.redirect_to.assert_called_once_with(controller.helpers.url_for.return_value)
        self.assertIsNone(result)

    @parameterized.expand([
        (None,),
        ('organization_uuidv4', )
    ])
    def test_close_post_errors(self, organization):
        post_content = {'accepted_dataset': 'example_ds'}
        exception = controller.tk.ValidationError({'Accepted Dataset': ['error1', 'error2']})
        close_reqform = MagicMock(side_effect=exception)

        # Execute the test
        self.test_close(organization, post_content, exception.error_dict,
                        {'Accepted Dataset': 'error1, error2'}, close_reqform)


    ######################################################################
    ############################### COMMENT ##############################
    ######################################################################

    def test_comment_list_not_authorized(self):
        reqform_id = 'example_uuidv4'
        controller.tk.check_access.side_effect = controller.tk.NotAuthorized('User not authorized')

        # Call the function
        result = self.controller_instance.comment(reqform_id)

        # Assertions
        controller.tk.check_access.assert_called_once_with(constants.LIST_REQFORM_COMMENTS, self.expected_context, {'reqform_id': reqform_id})
        controller.tk.abort.assert_called_once_with(403, 'You are not authorized to list the comments of the Request Form %s' % reqform_id)
        self.assertEquals(0, controller.tk.render.call_count)
        self.assertIsNone(result)

    def test_comment_list_not_found(self):
        reqform_id = 'example_uuidv4'
        controller.tk.get_action.return_value.side_effect = controller.tk.ObjectNotFound('Comment not found')

        # Call the function
        result = self.controller_instance.comment(reqform_id)

        # Assertions
        controller.tk.get_action(constants.COMMENT_REQFORM)
        controller.tk.abort.assert_called_once_with(404, 'Request Form %s not found' % reqform_id)
        self.assertEquals(0, controller.tk.render.call_count)
        self.assertIsNone(result)

    @parameterized.expand([
        (),
        (True,  False),
        (False, True),
        (True,  False, controller.tk.NotAuthorized),
        (False, True,  controller.tk.NotAuthorized),
        (True,  False, controller.tk.ObjectNotFound('Exception')),
        (False, True,  controller.tk.ObjectNotFound('Exception')),
        (True,  False, controller.tk.ValidationError({'commnet': ['error1', 'error2']})),
        (False, True, controller.tk.ValidationError({'commnet': ['error1', 'error2']}))

    ])
    def test_comment_list(self, new_comment=False, update_comment=False,
                          comment_or_update_exception=None):

        controller.request.POST = {}
        reqform_id = 'example_uuidv4'
        comment_id = 'comment_uuidv4'
        comment = 'example comment'
        new_comment_id = 'another_uuidv4'

        if new_comment or update_comment:
            controller.request.POST = {
                'reqform_id': reqform_id,
                'comment': comment,
                'comment-id': comment_id if update_comment else ''
            }

        reqform = {'id': 'uuid4', 'user_id': 'user_uuid4', 'title': 'example_title'}
        comments_list = [
            {'comment': 'Comment 1\nwith new line'},
            {'comment': 'Commnet 2\nwith two\nnew lines'},
            {'comment': 'Comment 3 with link https://fiware.org/some/path?param1=1&param2=2'},
            {'comment': 'Comment 4 with two links https://fiware.org/some/path?param1=1&param2=2 and https://google.es'},
            {'comment': 'Coment\nwith http://fiware.org\nhttp://fiware.eu'}
        ]

        default_action_return = {
            'id': new_comment_id if new_comment else comment_id,
            'comment': comment
        }

        show_reqform = MagicMock(return_value=reqform)
        list_reqform_comments = MagicMock(return_value=comments_list)
        default_action = MagicMock(side_effect=comment_or_update_exception, return_value=default_action_return)

        def _get_action(action):
            if action == constants.SHOW_REQFORM:
                return show_reqform
            elif action == constants.LIST_REQFORM_COMMENTS:
                return list_reqform_comments
            else:
                return default_action

        delattr(controller.c, 'updated_comment')
        delattr(controller.c, 'errors')
        controller.tk.get_action.side_effect = _get_action

        # Call the function
        result = self.controller_instance.comment(reqform_id)

        # Check the result
        controller.tk.render.assert_called_once_with('reqform/comment.html')
        self.assertEquals(result, controller.tk.render.return_value)

        # Verify comments and data request
        self.assertEquals(controller.c.reqform, reqform)
        self.assertEquals(controller.c.comments, comments_list)

        # Check calls
        show_reqform.assert_called_once_with(self.expected_context, {'id': reqform_id})
        list_reqform_comments.assert_called_once_with(self.expected_context, {'reqform_id': reqform_id})

        if new_comment:
            controller.tk.get_action.assert_any_call(constants.COMMENT_REQFORM)
        elif update_comment:
            controller.tk.get_action.assert_any_call(constants.UPDATE_REQFORM_COMMENT)

        if new_comment or update_comment:
            default_action.assert_called_once_with(self.expected_context, {'reqform_id': reqform_id,
                    'comment': comment, 'id': comment_id if update_comment else ''})

        if comment_or_update_exception == controller.tk.NotAuthorized:
            action = 'comment' if new_comment else 'update comment'
            controller.tk.abort.assert_called_once_with(403, 'You are not authorized to %s' % action)

        if type(comment_or_update_exception) == controller.tk.ObjectNotFound:
            controller.tk.abort.assert_called_once_with(404, str(comment_or_update_exception))

        if type(comment_or_update_exception) == controller.tk.ValidationError:
            # Abort never called
            self.assertEquals(0, controller.tk.abort.call_count)

            # Check controller.c values
            self.assertEquals(comment_or_update_exception.error_dict, controller.c.errors)

            errors_summary = {}
            for key, error in comment_or_update_exception.error_dict.items():
                    errors_summary[key] = ', '.join(error)

            self.assertEquals(errors_summary, controller.c.errors_summary)

        if new_comment or update_comment:

            # self.assertEquals(comment, controller.c.updated_comment['comment'])

            if new_comment:
                if comment_or_update_exception:
                    self.assertEquals('', controller.c.updated_comment['id'])
                else:
                    self.assertEquals(new_comment_id, controller.c.updated_comment['id'])

            if update_comment:
                self.assertEquals(comment_id, controller.c.updated_comment['id'])


    ######################################################################
    ########################### DELETE COMMENT ###########################
    ######################################################################

    def test_delete_comment_not_authorized(self):
        comment_id = 'example_uuidv4_comment'
        controller.tk.check_access.side_effect = controller.tk.NotAuthorized('User not authorized')

        # Call the function
        result = self.controller_instance.delete_comment('reqform_id', comment_id)

        # Assertions
        controller.tk.check_access.assert_called_once_with(constants.DELETE_REQFORM_COMMENT, 
                                                           self.expected_context, {'id': comment_id})
        controller.tk.abort.assert_called_once_with(403, 'You are not authorized to delete this comment')
        self.assertEquals(0, controller.tk.render.call_count)
        self.assertIsNone(result)

    def test_delete_comment_not_found(self):
        reqform_id = 'example_uuidv4'
        comment_id = 'comment_uuidv4'
        controller.tk.get_action.return_value.side_effect = controller.tk.ObjectNotFound('Comment not found')

        # Call the function
        result = self.controller_instance.delete_comment(reqform_id, comment_id)

        # Assertions
        controller.tk.get_action(constants.DELETE_REQFORM_COMMENT)
        controller.tk.abort.assert_called_once_with(404, 'Comment %s not found' % comment_id)
        self.assertEquals(0, controller.tk.render.call_count)
        self.assertIsNone(result)

    def test_delete_comment(self):
        reqform_id = 'example_uuidv4'
        comment_id = 'comment_uuidv4'

        # Call
        self.controller_instance.delete_comment(reqform_id, comment_id)

        # Check calls
        controller.tk.get_action.assert_called_once_with(constants.DELETE_REQFORM_COMMENT)
        delete_reqform_comment = controller.tk.get_action.return_value
        delete_reqform_comment.assert_called_once_with(self.expected_context, {'id': comment_id})

        # Check redirection
        controller.helpers.url_for.assert_called_once_with(
            controller='ckanext.reqform.controllers.ui_controller:DataRequestsUI',
            action='comment', id=reqform_id)
        controller.tk.redirect_to.assert_called_once_with(controller.helpers.url_for.return_value)

    ######################################################################
    ########################## FOLLOW/UNFOLLOW ###########################
    ######################################################################

    def test_follow(self):
        self.controller_instance.follow('example_uuidv4')

    def test_unfollow(self):
        self.controller_instance.unfollow('example_uuidv4')
