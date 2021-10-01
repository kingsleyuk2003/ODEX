{
    'name': 'ROG Modifications for Legal',
    'version': '0.1',
    'description': """
ROG Modifications
=======================================================================================
image from openclip http://openclipart.org/
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com)',
    'depends': ['base','web_notify','kin_reminder','mail','report_xlsx'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'sequence.xml',
'report.xml',
        'wizard/legal_advice.xml',
        'wizard/legal_response.xml',
        'wizard/case_file_report_wizard_view.xml',

        'legal_view.xml',

        'cron_data.xml',

    ],
    'installable': True,
    'images': [],
}