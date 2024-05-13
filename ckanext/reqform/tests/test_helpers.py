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

import ckanext.reqform.helpers as helpers
import unittest

from mock import MagicMock, patch


class HelpersTest(unittest.TestCase):

    def setUp(self):
        self.tk_patch = patch('ckanext.reqform.helpers.tk')
        self.tk_patch.start()

        self.model_patch = patch('ckanext.reqform.helpers.model')
        self.model_patch.start()

        self.db_patch = patch('ckanext.reqform.helpers.db')
        self.db_patch.start()

        self.c_patch = patch('ckanext.reqform.helpers.c')
        self.c = self.c_patch.start()

    def tearDown(self):
        self.tk_patch.stop()
        self.model_patch.stop()
        self.db_patch.stop()
        self.c_patch.stop()

    def test_get_comments_number(self):
        # Mocking
        n_comments = 3
        helpers.db.Comment.get_comment_reqforms_number.return_value = n_comments

        # Call the function
        reqform_id = 'example_uuidv4'
        result = helpers.get_comments_number(reqform_id)

        # Assertions
        helpers.db.init_db.assert_called_once_with(helpers.model)
        helpers.db.Comment.get_comment_reqforms_number.assert_called_once_with(reqform_id=reqform_id)
        self.assertEquals(result, n_comments)

    def test_get_comments_badge(self):
        # Mocking
        n_comments = 3
        helpers.db.Comment.get_comment_reqforms_number.return_value = n_comments

        # Call the function
        reqform_id = 'example_uuidv4'
        result = helpers.get_comments_badge(reqform_id)

        # Assertions
        helpers.db.init_db.assert_called_once_with(helpers.model)
        helpers.db.Comment.get_comment_reqforms_number.assert_called_once_with(reqform_id=reqform_id)
        self.assertEquals(result, helpers.tk.render_snippet.return_value)
        helpers.tk.render_snippet.assert_called_once_with('reqform/snippets/badge.html',
                                                          {'comments_count': n_comments})

    def test_get_open_reqforms_number(self):
        # Mocking
        n_reqforms = 3
        helpers.db.DataRequest.get_open_reqforms_number.return_value = n_reqforms

        # Call the function
        result = helpers.get_open_reqforms_number()

        # Assertions
        helpers.db.init_db.assert_called_once_with(helpers.model)
        helpers.db.DataRequest.get_open_reqforms_number.assert_called_once_with()
        self.assertEquals(result, n_reqforms)

    def test_get_open_reqforms_badge_true(self):
        # Mocking
        n_reqforms = 3
        helpers.db.DataRequest.get_open_reqforms_number.return_value = n_reqforms

        # Call the function
        result = helpers.get_open_reqforms_badge(True)

        # Assertions
        helpers.db.init_db.assert_called_once_with(helpers.model)
        helpers.db.DataRequest.get_open_reqforms_number.assert_called_once_with()
        self.assertEquals(result, helpers.tk.render_snippet.return_value)
        helpers.tk.render_snippet.assert_called_once_with('reqform/snippets/badge.html',
                                                          {'comments_count': n_reqforms})

    def test_get_open_reqforms_badge_false(self):
        self.assertEquals(helpers.get_open_reqforms_badge(False), '')

    def test_is_following_reqform_true(self):
        follower = MagicMock()
        reqform_id = 'example_id'
        helpers.db.DataRequestFollower.get.return_value = [follower]

        self.assertTrue(helpers.is_following_reqform(reqform_id))

        helpers.db.DataRequestFollower.get.assert_called_once_with(reqform_id=reqform_id, user_id=self.c.userobj.id)

    def test_is_following_reqform_false(self):
        reqform_id = 'example_id'
        helpers.db.DataRequestFollower.get.return_value = []

        self.assertFalse(helpers.is_following_reqform(reqform_id))

        helpers.db.DataRequestFollower.get.assert_called_once_with(reqform_id=reqform_id, user_id=self.c.userobj.id)
