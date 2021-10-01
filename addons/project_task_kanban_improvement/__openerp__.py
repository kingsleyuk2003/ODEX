# -*- coding: utf-8 -*-
# © 2016 Pierre Faniel
# © 2016 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Project Task - Kanban Improvement',
    'category': 'Project',
    'summary': 'Project task kanban view design improvement',
    'website': 'https://www.niboo.be/',
    'version': '9.0.1.0.0',
    'license': 'AGPL-3',
    'description': '''
        - Customer's logo added in the Kanban box.
        - Added planned hours, remaining hours, time spent in task kanban box
        ''',

    'author': 'Niboo',
    'depends': [
        'project',
    ],
    'data': [
        'views/project_task_view.xml',
    ],
    'installable': True,
    'application': False,
}
