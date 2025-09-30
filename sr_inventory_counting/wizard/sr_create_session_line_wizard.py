# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Mobile/Whatsapp : +91 7405030365
#
##############################################################################

from odoo import models, fields, api, _


class SrCreateSessionLine(models.TransientModel):
    _name = 'sr.create.session.wizard.line'
    _description = 'Inventory Counting Wizard'

    wizard_id = fields.Many2one('sr.create.session.wizard')
    product_id = fields.Many2one('product.product', string='Product')
    internal_ref = fields.Char('Internal Refence', store=True, related='product_id.default_code')
    location_id = fields.Many2one('stock.location', string='Location', domain="[('usage', '=', 'internal')]")
    counted_qty = fields.Float('Counted Qty')

    @api.onchange('internal_ref')
    def _onchange_internal_ref(self):
        if self.internal_ref:
            product = self.env['product.product'].search([('default_code', '=', self.internal_ref)], limit=1)
            if product:
                self.product_id = product
