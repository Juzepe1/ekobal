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


class SrInventoryCounting(models.Model):
    _name = 'sr.inventory.counting'
    _description = 'Inventory Counting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Name', copy=False)
    session_id = fields.Many2one('sr.inventory.session', string='Inventory Session', copy=False, tracking=True)
    approver_id = fields.Many2one('res.users', string='Approver', tracking=True, copy=False)
    date = fields.Date(string='Date', default=fields.Date.context_today, tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', tracking=True)
    location_id = fields.Many2one('stock.location', string='Location',
                                  domain="[('warehouse_id', '=', warehouse_id),('usage', '=', 'internal')]",
                                  tracking=True)
    type = fields.Selection([
        ('single_session', 'Single Session'),
        ('multi_session', 'Multi Session')
    ], default='single_session', string="Type", tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('to_be_approve', 'To Be Approve'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancel')
    ], default='draft', string="Status", copy=False, tracking=True)

    inventory_count_line_ids = fields.One2many('sr.inventory.counting.line', 'inventory_counting_id',
                                               string='Inventory Count Line')
    session_count = fields.Integer(string='Session', compute='_compute_session_count')
    reject_reason = fields.Char('Reject Reason')
    adjustment_count = fields.Integer(string='Adjustment', compute='_compute_adjustment_count')
    adjustment_create = fields.Boolean('Adjustment Create', default=False, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name']:
                vals['name'] = self.env['ir.sequence'].next_by_code('sr.inventory.counting')
        return super().create(vals_list)

    def action_send_for_approval(self):
        for record in self:
            sessions = self.env['sr.inventory.session'].search([
                ('inventory_count_id', '=', record.id),
                ('status', '!=', 'done')
            ])
            if sessions:
                session_names = ', '.join(sessions.mapped('name'))
                raise UserError(f"You cannot finish counting. The following sessions are not done:\n{session_names}")
            record.status = 'to_be_approve'

    def action_reject_count(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Count',
            'res_model': 'sr.reject.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'hide_warning_message': True,
            }
        }

    def action_approve_count(self):
        self.status = 'approved'

    def action_create_session(self):
        for record in self:
            if not record.inventory_count_line_ids:
                raise ValidationError("Please Add At-least One Line To Proceed.")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Session',
            'res_model': 'sr.create.session.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': False,
            }
        }

    def action_cancel(self):
        self.status = 'cancel'

    def action_show_created_session(self):
        self.ensure_one()
        sessions = self.env['sr.inventory.session'].search([
            ('inventory_count_id', '=', self.id)
        ])
        action = {
            'name': 'Sessions',
            'type': 'ir.actions.act_window',
            'res_model': 'sr.inventory.session',
        }
        if len(sessions) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': sessions.id,
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('inventory_count_id', '=', self.id)],
            })
        return action

    def action_open_adjustment(self):
        self.ensure_one()
        adjustments = self.env['sr.inv.adjustment'].search([
            ('count_id', '=', self.id)
        ])

        action = {
            'name': 'Adjustment',
            'type': 'ir.actions.act_window',
            'res_model': 'sr.inv.adjustment',
        }
        if len(adjustments) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': adjustments.id,
                'target': 'current',
            })
        else:
            action.update({
                'view_mode': 'list,form',
                'domain': [('id', 'in', adjustments.ids)],
                'target': 'current',
            })
        return action

    def _compute_session_count(self):
        for rec in self:
            rec.session_count = self.env['sr.inventory.session'].search_count([
                ('inventory_count_id', '=', rec.id)
            ])

    def _compute_adjustment_count(self):
        for rec in self:
            rec.adjustment_count = self.env['sr.inv.adjustment'].search_count([
                ('count_id', '=', rec.id)
            ])

    def action_create_adjustment(self):
        self.adjustment_create = True
        new_adjustment = self.env['sr.inv.adjustment'].create({
            'count_id': self.id,
            'date': fields.Date.context_today(self),
            'status': 'draft',
        })
        return {
            'name': 'Create Adjustment',
            'type': 'ir.actions.act_window',
            'res_model': 'sr.inv.adjustment',
            'view_mode': 'form',
            'res_id': new_adjustment.id,
            'target': 'current',
        }

    def unlink(self):
        for record in self:
            if record.status != 'draft':
                raise ValidationError("You can only delete Inventory Count in Draft status.")

            if self.env['sr.inventory.session'].search([('inventory_count_id', '=', record.id)]):
                raise ValidationError("The sessions must be deleted first before the count can be deleted.")
        return super().unlink()


class SrInventoryCountingLine(models.Model):
    _name = 'sr.inventory.counting.line'
    _description = 'Inventory Counting Line'

    inventory_counting_id = fields.Many2one('sr.inventory.counting')
    product_id = fields.Many2one('product.product', string='Product', domain=[('type', '!=', 'service')])
    internal_ref = fields.Char('Internal Reference', store=True, related='product_id.default_code')
    counted_qty = fields.Float(string='Counted Qty', default=0)
    count_related_location_id = fields.Many2one(
        'stock.location',
        related='inventory_counting_id.location_id',
        store=False,
        readonly=True,
        string='Location'
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location ',
        domain="[('id', 'child_of', count_related_location_id)]"
    )

    @api.onchange('internal_ref')
    def _onchange_internal_ref(self):
        if self.internal_ref:
            product = self.env['product.product'].search([('default_code', '=', self.internal_ref)], limit=1)
            if product:
                self.product_id = product

    @api.constrains('counted_qty')
    def _check_counted_qty_non_negative(self):
        for rec in self:
            if rec.counted_qty < 0:
                raise ValidationError("Counted Quantity must be zero or greater.")
