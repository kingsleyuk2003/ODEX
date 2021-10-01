# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017-2019  Kinsolve Solutions
# Copyright 2017-2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Depot Loading Process',
    'version': '0.1',
    'category': 'other',
    'description': """
Loading Process for the Oil and Gas Industry
=======================================================================================

""",
    'author': 'Kinsolve Solutions - kingsley@kinsolve.com',
    'website': 'http://kinsolve.com',
    'depends': ['base','mail','report_xlsx','stock','account','kin_sales','kin_product','kin_stock','sale_stock'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/truck_check_list_approvals.xml',
        'wizard/tarmac_truck_check_list_approvals.xml',
        'wizard/loading_ticket_wizard_view.xml',
        'wizard/transfer_order_wizard_view.xml' ,
        'wizard/loading_programme_disapproval_reason.xml',
        'wizard/cancel_qty.xml',
        'wizard/stock_dispatch_wizard_view.xml',
        'wizard/sales_loading_report_wizard_view.xml',
        'wizard/stock_picking_wizard_view.xml',
        'wizard/customer_stock_summary_report_wizard_view.xml',
        'wizard/customer_stock_report_wizard_view.xml',
        'wizard/police_report.xml',
        'wizard/ticket_recovered.xml',
        'wizard/mass_confirm_order_view.xml',
        'wizard/sales_order_disapprove.xml',
        'wizard/block_ticket_wizard.xml',
        'wizard/unblock_ticket_wizard.xml',
        'wizard/loading_programme_wizard_view.xml',
        'wizard/mass_email_sot_view.xml',
        'data/data.xml',
        'kin_report.xml',
        'report/loading_ticket.xml',
        'report/loading_waybill.xml',
        'report/loading_programme.xml',
        'report/truck_park_ticket.xml',
        'report/empty_truck_exit.xml',
        'report/template.xml',
        'report/summary_of_transactions.xml',
        'loading_view.xml',
        'sequence.xml',
        'mail_template.xml'
    ],
    'test':[],
    'installable': True,
    'images': [],
}