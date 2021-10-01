# -*- coding: utf-8 -*-
# © 2016 Jérôme Guerriat
# © 2016 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'Project - Create tasks from issues',
    'category': 'Project',
    'summary': 'Directly create tasks based on your issues',
    'description':"""
- This module adds the possibility to create a task directly from an issue with several information prefilled
- This module adds a tab to the linked issues in the task view
    """,
    'website': 'https://www.niboo.be/',
    'version': '9.0.1.0.0',
    'author': 'Niboo',
    'license': 'AGPL-3',
    'depends': [
        'project_issue',
    ],
    'data': [
        'views/project_issue.xml',
        'views/project_task.xml',
    ],
    'images': [
        'static/description/cover.png',
    ],
    'installable': True,
    'application': False,
}
