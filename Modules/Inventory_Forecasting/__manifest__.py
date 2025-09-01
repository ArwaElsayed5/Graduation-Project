{
    'name': 'AI-powered Inventory Forecasting',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Advanced inventory Managment with sales prediction',
    'description': """
        This module provides advanced inventory slotting functionality with:
        - Sales prediction using machine learning
        - Dynamic slotting optimization
        - Warehouse zone management
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/inventory_slotting_views.xml',
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['pandas', 'numpy', 'pycaret'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
} 