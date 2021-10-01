{
    'name': 'ROG Modifications',
    'version': '0.1',
    'description': """
ROG Modifications
=======================================================================================
image from openclip http://openclipart.org/
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com)',
    'depends': ['base','purchase','web_notify','kin_reminder','hr_expense','account_voucher_extend','account_fiscal_year_closing','stock','stock_landed_costs','kin_account','account_asset','kin_stock','kin_loading','kin_sales','kin_report','account_payment_group','kin_account_payment_group','hr','kin_purchase','purchase_request','purchase_request_department','hr_holiday_exclude_special_days','hr_holidays_multi_levels_approval','account_fiscal_year_closing','kin_hr','hr_contract','ohrms_salary_advance','ohrms_loan','ohrms_loan_accounting','kin_bank_reconcile','hr_recruitment','board','account_financial_report_qweb'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/custom_receipt_rog.xml',
        'report/custom_invoice.xml',
        'report/custom_report_layouts_rog.xml',
        'report/report_purchaseorder.xml',
        'report/custom_payslip.xml',
        'data.xml',
        'rog_report.xml',
        'wizard/shipping_report_wizard_view.xml',
        'wizard/form_m_report_wizard_view.xml',
        'wizard/lc_bc_report_wizard_view.xml',
        'wizard/pef_pppra_report_wizard_view.xml',
        'wizard/create_entry_view.xml',
        'wizard/epccos_report_wizard_view.xml',
        'wizard/refund_rule_view.xml',
        'wizard/ml_report_wizard_view.xml',
        'wizard/pfa_report_wizard_view.xml',
        'wizard/general_pension_report_wizard_view.xml',
        'wizard/bank_advice_report_wizard_view.xml',
        'wizard/paye_report_wizard_view.xml',
        'wizard/payroll_report_wizard_view.xml',
        'wizard/consolidated_report_wizard_view.xml',
        'wizard/consolidated_finance_report_wizard_view.xml',
        'wizard/depot_report_wizard_view.xml',
        'wizard/bank_report_wizard_view.xml',
        'wizard/consol_report_wizard_view.xml',
        'wizard/sales_summary_report_wizard_view.xml',
        'wizard/sos_report_wizard_view.xml',
        'wizard/salary_section_report_wizard_view.xml',
        # 'wizard/import_biometric_view.xml',

        'purchase_view.xml',
        'inventory_view.xml',
        'sequence.xml',
        'shipping_view.xml',
        'account_view.xml',
        'hr_view.xml',
        'stock_view.xml',
        'res_partner_view.xml',
        'sale_view.xml',
        'product.xml',
        'procurement_view.xml',
        'management_report_view.xml',
        'cron_data.xml'
    ],
    'installable': True,
    'images': [],
}
