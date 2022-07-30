# SPDX-License-Identifier: LGPL-2.1-or-later

# Copyright (C) 2020-2022 igo95862

# This file is part of python-sdbus

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
from __future__ import annotations

from asyncio import get_running_loop, wait_for
from unittest.mock import MagicMock

from sdbus.unittest import IsolatedDbusTestCase

from sdbus import (
    DbusInterfaceCommonAsync,
    dbus_method_async,
    request_default_bus_name_async,
)
from sdbus.dbus_exceptions import DbusFailedError

NEVER_USED = "never used"


class InterfaceWithErrors(
    DbusInterfaceCommonAsync,
    interface_name='org.example.test',
):
    @dbus_method_async(input_signature='', result_signature='s')
    async def signature_mismatch(self, wrong_param: str) -> str:
        return NEVER_USED


class InterfaceWithErrorsProxy(
    DbusInterfaceCommonAsync,
    interface_name='org.example.test',
):
    @dbus_method_async(input_signature='', result_signature='s')
    async def signature_mismatch(self) -> str:
        """
        Used for proxy to bypass client side error checking
        """
        ...


class TestExternalErrors(IsolatedDbusTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()

        await request_default_bus_name_async('org.test')
        self.test_object = InterfaceWithErrors()
        self.test_object.export_to_dbus('/')

        self.test_object_connection = InterfaceWithErrorsProxy.new_proxy(
            'org.test', '/')

        loop = get_running_loop()
        self.exception_handler = MagicMock()
        loop.set_exception_handler(self.exception_handler)

    async def test_signature_mismatch(self) -> None:
        with self.assertRaises(DbusFailedError):
            await wait_for(
                self.test_object_connection.signature_mismatch(),
                timeout=5,
            )
        self.exception_handler.assert_called_once()
        self.assertIsInstance(
            self.exception_handler.call_args_list[0][0][1]["exception"],
            TypeError
        )
