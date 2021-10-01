{
    'name': 'ROG Modifications for QHSSE',
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
        'qhsse_view.xml',
        'report.xml',
        'cron_data.xml',

    ],
    'installable': True,
    'images': [],
}