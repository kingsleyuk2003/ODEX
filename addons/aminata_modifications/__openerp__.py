{
    'name': 'Aminata Modifications',
    'version': '0.1',
    'description': """
Aminata Modifications
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com)',
    'depends': ['base','hr_payroll','hr_contract','hr','kin_hr','kin_report','purchase','kin_sales','kin_purchase','kin_delivery','account','kin_account','kin_lifting','kin_retail_station_general','stock','account_voucher_extend'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'sequence.xml',
        'wizard/create_po.xml',
        'wizard/payroll_report_wizard_view.xml',
        'aminata_view.xml',
        'aminata_report.xml',
        'cron_data.xml',
        'report/custom_report_layouts_aminata.xml',
        'report/custom_delivery_note_aminata.xml',
        'report/custom_retail_mother_do_aminata.xml',
        'report/custom_retail_instant_delivery_order.xml',
        'report/station_to_station_retail_transfer.xml',
        'report/custom_receipt_aminata.xml',
        'report/transfer_aminata.xml',
        'report/custom_invoice.xml',
        'report/custom_payslip.xml',
    ],
    'installable': True,
    'images': [],
}