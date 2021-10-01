# -*- coding: utf-8 -*-
# Copyright 2017 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Budget Variance",
    "version": "9.0.1.0.0",
    "summary": "Adds variance amount and percent",
    "category": "Accounting",
    "website": "https://opensynergy-indonesia.com",
    "author": "OpenSynergy Indonesia",
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "account_budget",
    ],
    "data": [
        "views/crossovered_budget_view.xml",
        "views/crossovered_budget_line_view.xml"
    ],
}
