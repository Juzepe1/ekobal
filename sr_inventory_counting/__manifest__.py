# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Mobile/Whatsapp : +91 7405030365
#
##############################################################################

{
    'name': 'Physical Stock Inventory Count & Adjustment with Session-Based Management',
    'category': 'Inventory',
    'version': '17.0.0.0',
    'license': 'OPL-1',
    'Summary': 'Efficient inventory counting, session tracking, and adjustment management with approval workflow.',
    'description':"""This module enhances Odoo’s inventory management by introducing structured
                    inventory counting sessions, approval workflows, and adjustment tracking.
                    
                    Key Features:
                    - Create and manage inventory counting sessions.
                    - Approve or reject counts with mandatory reasons for rejections.
                    - Track discrepancies between system stock and counted stock.
                    - Automatic generation of adjustment entries for variances.
                    - Detailed reports: Inventory Count Report, Session Report, and Adjustment Report.
                    - Improved accountability and transparency in stock management.
                    - Dashboard and analytics for real-time inventory insights.
                    
                    This ensures greater accuracy, control, and reliability in warehouse operations.
                    Physical Stock Inventory Count & Adjustment with Session-Based Management
                    This module makes the process of physical inventory counting simple, organized, and reliable. It allows businesses to conduct stock counts in a structured way, whether through a single session or multiple sessions across different warehouses, locations, or product groups.
                    Inventory managers can create sessions and assign them to specific team members, making it easier to divide large counts into smaller, manageable tasks. The system records the quantities entered during the count and highlights differences between the physically counted stock and the system’s existing data.
                    Once a session is completed, managers can review the results and either approve or reject them. After approval, the system provides an option to adjust the on-hand quantity with a single button click. This ensures that physical counts can be accurately reflected in Odoo whenever required, while still giving flexibility to skip adjustment if not needed.
                    All sessions, approvals, and adjustments are stored for future reference, giving companies a clear history of their stock take activities and improving inventory accuracy over time.
                """,
    'price': 50,
    'currency': 'EUR',
    'author': 'Sitaram',
    'depends': ['base','stock'],
    'data': [
        'security/security_group.xml',
        'security/record_rule.xml',
        'security/ir.model.access.csv',
        'data/inventory_counting_sequence.xml',
        'data/inventory_session_sequence.xml',
        'data/sr_inv_adjustment_sequence.xml',
        'view/inventory_counting_view.xml',
        'view/inventory_session_view.xml',
        'view/sr_inv_adjustment_view.xml',
        'view/stock_move_view.xml',
        'wizard/sr_create_session_wizard_view.xml',
        'wizard/sr_approve_wizard_view.xml',
        'wizard/sr_reject_reason_wizard_view.xml',
        'wizard/inventory_session_report_wizard_view.xml',
        'wizard/sr_inv_count_report_wizard_view.xml',
        'wizard/sr_adjustment_confirmation_wizard_view.xml',
        'wizard/sr_inv_adjustment_report_wizard_view.xml',
        'reports/report_inventory_session.xml',
        'reports/report_inventory_session_template.xml',
        'reports/inventory_count_report_action.xml',
        'reports/inventory_count_report_template.xml',
        'reports/inventory_adjustment_report_action.xml',
        'reports/inventory_adjustment_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sr_inventory_counting/static/src/**/*',
        ]
    },
    'website': 'https://www.sitaramsolutions.in',
    'application': True,
    'installable': True,
    'auto_install': False,
    'live_test_url': 'https://youtu.be/GR5dKY9yVJc',
    'images': ['static/description/banner.png'],
}