# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Mobile/Whatsapp : +91 7405030365
#
##############################################################################

from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    adjustment_id = fields.Many2one('sr.inv.adjustment', string="Inventory Adjustment", store=True)
