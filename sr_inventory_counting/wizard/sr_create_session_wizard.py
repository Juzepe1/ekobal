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
from odoo.exceptions import UserError


class SrCreateSessionWizard(models.TransientModel):
    _name = 'sr.create.session.wizard'
    _description = 'Create Session Wizard'

    user_id = fields.Many2one('res.users', string='User')
    wizard_line_ids = fields.One2many('sr.create.session.wizard.line', 'wizard_id', string='Wizard Line')
    inventory_count_id = fields.Many2one('sr.inventory.counting', string='Inventory Count')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if self.env.context.get('active_id'):
            res['inventory_count_id'] = self.env.context.get('active_id')
        if active_id:
            vals = []
            inv_id = self.env['sr.inventory.counting'].browse(active_id)
            for line in inv_id.inventory_count_line_ids:
                vals.append((0, 0, {
                    'product_id': line.product_id.id,
                    'internal_ref': line.product_id.default_code,
                    'location_id': line.location_id,
                }))
            res['wizard_line_ids'] = vals
        return res

    def action_create_session(self):
        self.ensure_one()
        if not self.wizard_line_ids:
            raise UserError(_("Please add at least one line to proceed."))

        session_id = self.env['sr.inventory.session'].create({
            'user_id': self.user_id.id,
            'warehouse_id': self.inventory_count_id.warehouse_id.id,
            'location_id': self.inventory_count_id.location_id.id,
            'type': self.inventory_count_id.type,
            'inventory_count_id': self.inventory_count_id.id,
            'approver_id': self.inventory_count_id.approver_id.id,
        })

        for line in self.wizard_line_ids:
            location_ids = self.env['stock.location'].search([
                ('id', 'child_of', self.inventory_count_id.location_id.id)
            ])
            for location in location_ids:
                vals_dict = {
                    'inventory_session_id': self.id,
                    'product_id': line.product_id.id,
                    'location_id': location.id,
                    'counted_qty': line.counted_qty,
                    'status': 'pending',
                }
                session_id.session_line_ids = [(0, 0, vals_dict)]
        self.inventory_count_id.status = 'in_progress'
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inventory Session',
            'res_model': 'sr.inventory.session',
            'res_id': session_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
