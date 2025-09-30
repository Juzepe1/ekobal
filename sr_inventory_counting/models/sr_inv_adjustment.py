# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Mobile/Whatsapp : +91 7405030365
#
##############################################################################

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class SrInvAdjustment(models.Model):
    _name = 'sr.inv.adjustment'
    _description = 'Sr Inventory Adjustment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name', copy=False)
    sr_adjustment_line_ids = fields.One2many('sr.inv.adjustment.line', 'sr_inv_adjustment_id',
                                             string='Inventory Adjustment', compute="_compute_sr_adjustment_line_ids",
                                             store=True, copy=False)
    count_id = fields.Many2one('sr.inventory.counting', string='Inventory Count',
                               domain=lambda self: self._get_valid_count_ids(), copy=False)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    status = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default="draft", copy=False)
    adjustment_line_count = fields.Integer(string='Adjustment Lines', default=0)

    @api.model
    def _get_valid_count_ids(self):
        session_lines = self.env['sr.inventory.session.line'].search([
            ('status', '=', 'approve'),
            ('adjustment_done', '=', False),
        ])
        valid_count_ids = session_lines.mapped('inventory_session_id.inventory_count_id.id')
        return [('id', 'in', valid_count_ids), ('approver_id', '!=', False), ('status', '=', 'approved')]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name']:
                vals['name'] = self.env['ir.sequence'].next_by_code('sr.inv.adjustment')
        return super().create(vals_list)

    def action_adjustment_confirm(self):
        if not self.sr_adjustment_line_ids:
            raise ValidationError('Inventory Adjustment Line Is Empty.')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Confirm Inventory Adjustment',
            'res_model': 'sr.adjustment.confirmation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sr_inv_adjustment_id': self.id
            }
        }

    def action_adjustment_count_show(self):
        self.ensure_one()
        self.env['stock.move.line'].search([
            ('adjustment_id', '=', self.id)
        ])
        action = {
            'name': 'Stock Move Lines',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'list,form',
            'domain': [('adjustment_id', '=', self.id)],

        }
        return action

    @api.depends('count_id')
    def _compute_sr_adjustment_line_ids(self):
        if not self.count_id:
            self.sr_adjustment_line_ids = [(5, 0, 0)]
            return

        session_lines = self.env['sr.inventory.session.line'].search([
            ('inventory_session_id.inventory_count_id', '=', self.count_id.id),
            ('status', '=', 'approve'),
            ('adjustment_done', '=', False),
        ])

        lines_vals = []
        for line in session_lines:
            product = line.product_id
            location = line.location_id
            line.adjustment_done = True

            if not product or not location:
                continue

            quants = self.env['stock.quant'].sudo().search([
                ('product_id', '=', product.id),
                ('location_id', '=', location.id),
            ])

            for quant in quants:
                lines_vals.append((0, 0, {
                    'product_id': product.id,
                    'location_id': location.id,
                    'counted_qty': line.counted_qty,
                    'on_hand_qty': quant.quantity,
                }))

            if not quants:
                lines_vals.append((0, 0, {
                    'product_id': product.id,
                    'location_id': location.id,
                    'counted_qty': line.counted_qty,
                    'on_hand_qty': 0.0,
                }))

        self.sr_adjustment_line_ids = [(5, 0, 0)] + lines_vals


class SrInvAdjustmentLine(models.Model):
    _name = 'sr.inv.adjustment.line'
    _description = 'Sr Inventory Adjustment Line'

    sr_inv_adjustment_id = fields.Many2one('sr.inv.adjustment', string='inventory Adjustment')
    product_id = fields.Many2one('product.product', string='Product')
    location_id = fields.Many2one('stock.location', string='Location', domain=[('usage', '=', 'internal')])
    counted_qty = fields.Float(string='Counted Qty')
    on_hand_qty = fields.Float(string='On Hand Qty')
    difference = fields.Float(string='Difference', compute='_compute_difference', store=True)

    @api.depends('counted_qty', 'on_hand_qty')
    def _compute_difference(self):
        for rec in self:
            rec.difference = rec.counted_qty - rec.on_hand_qty

    @api.constrains('counted_qty')
    def _check_counted_qty_non_negative(self):
        for rec in self:
            if rec.counted_qty < 0:
                raise ValidationError("Counted Quantity must be zero or greater.")
