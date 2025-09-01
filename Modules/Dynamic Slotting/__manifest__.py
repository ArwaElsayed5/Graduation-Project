{
    'name': 'Dynamic Slotting Optimization',
    'version': '1.0',
    'depends': ['base', 'web', 'stock', 'sale'],

    'data': [
        'views/slotting_menu.xml',
        'data/slotting_models.xml',
        'views/slotting_result_views.xml',
        'views/slotting_wizard_views.xml',
        'security/ir.model.access.csv',

    ],
    'license': 'LGPL-3',  # Specify the license
    'installable': True,
    'application': True,
    'auto_install': False,
}

