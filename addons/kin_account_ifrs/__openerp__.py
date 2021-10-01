# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Account IFRS',
    'version': '0.1',
    'category': 'report',
    'description': """
Account IFRS
=======================================================================================

This module create the custom IFRS account type, which resolves the issue of the base module update or invoicing account module update from deleting the account type, thereby raising the following error:

The operation cannot be completed, probably due to the following:
- deletion: you may be trying to delete a record while other records still reference it
- creation/update: a mandatory field is not correctly set [object with reference: Account - account.account]

with backend error as:
IntegrityError: null value in column "user_type_id" violates not-null constraint
DETAIL:  Failing row contains (664, 1, other, 2019-01-10 02:22:34.448222, Loan Interest, f, null, 1, 1, null, ROG72001, 2019-01-22 08:50:14.322523, null, null, f, f, 79, null).
CONTEXT:  SQL statement "UPDATE ONLY "public"."account_account" SET "user_type_id" = NULL WHERE $1 OPERATOR(pg_catalog.=) "user_type_id""
see link: https://www.odoo.com/forum/help-1/question/if-i-am-upgrading-the-module-account-why-does-odoo-try-to-remove-the-records-i-created-manually-142971

""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','account','mis_builder','kin_account'],
    'data': [
        'data/account_type.xml',
        'data/ifrs_report_head.xml',
        'data/mis_report_styles.xml',
        'data/ifrs_bs.xml',
        'data/ifrs_pl.xml',
        'data/ifrs_cf.xml',

    ],
    'test':[],
    'installable': True,
    'images': [],
}