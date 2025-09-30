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
from datetime import datetime, timedelta


class SrInventorySession(models.Model):
    _name = 'sr.inventory.session'
    _inherit = ['timer.count.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Inventory Session'
    _order = 'id desc'

    name = fields.Char(string='Name', copy=False)
    inventory_count_id = fields.Many2one('sr.inventory.counting', string='Inventory Count')
    user_id = fields.Many2one('res.users', string='User')
    approver_id = fields.Many2one('res.users', string='Approver ')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    location_id = fields.Many2one('stock.location', string='Location',
                                  domain="[('warehouse_id', '=', warehouse_id),('usage', '=', 'internal')]")
    type = fields.Selection([
        ('single_session', 'Single Session'),
        ('multi_session', 'Multi Session')
    ], string="Type")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], default='draft', string="Status")
    total_product = fields.Integer('Total Products', compute='_compute_total_product', store=True)
    session_line_ids = fields.One2many('sr.inventory.session.line', 'inventory_session_id', string='Session Lines')
    approved_all = fields.Boolean(string="All Approved", compute="_compute_approved_reject_all")
    reject_all = fields.Boolean(string="All reject", compute="_compute_approved_reject_all")
    original_session_id = fields.Many2one('sr.inventory.session', string='Original Session')
    is_re_session = fields.Boolean(string="Is Re-Session")
    rejected_line = fields.Boolean(string="Rejected line", compute='_compute_rejected_line', store=True)
    re_session_created = fields.Boolean('Re Session Created')
    timer_in_second = fields.Float("Timer in Second")
    timer_in_char = fields.Char("Time Spent", compute="_compute_timer_in_char")
    re_session_count = fields.Integer(string='Session', compute='_compute_re_session_count')

    def _compute_re_session_count(self):
        for rec in self:
            rec.re_session_count = self.env['sr.inventory.session'].search_count([
                ('original_session_id', '=', rec.id)
            ])

    @api.depends('timer_in_second')
    def _compute_timer_in_char(self):
        for rec in self:
            if rec.timer_in_second:
                rec.timer_in_char = str(timedelta(seconds=rec.timer_in_second))
            else:
                rec.timer_in_char = "00:00:00"

    @api.depends('status', 'session_line_ids.status', 'type')
    def _compute_rejected_line(self):
        for rec in self:
            has_rejected = any(line.status == 'rejected' for line in rec.session_line_ids)
            rec.rejected_line = has_rejected and rec.status == 'done' and rec.type == 'multi_session'

    @api.depends('session_line_ids.status')
    def _compute_approved_reject_all(self):
        for rec in self:
            statuses = rec.session_line_ids.mapped('status')
            rec.approved_all = all(status == 'approve' for status in statuses) if statuses else False
            rec.reject_all = bool(statuses) and all(status == 'rejected' for status in statuses)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name']:
                vals['name'] = self.env['ir.sequence'].next_by_code('sr.inventory.session')
        return super().create(vals_list)

    @api.depends('session_line_ids')
    def _compute_total_product(self):
        for rec in self:
            rec.total_product = len(rec.session_line_ids)

    def action_approve_all_lines(self):
        rejected_lines = self.session_line_ids.filtered(lambda line: line.status == 'rejected')
        if rejected_lines:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Approve All Session Lines',
                'res_model': 'sr.approve.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'active_id': self.id,
                },
            }
        else:
            for line in self.session_line_ids:
                line.status = 'approve'

    def action_session_start(self):
        res = super(SrInventorySession, self).action_session_start()
        self.status = 'in_progress'
        return res

    def action_session_stop(self):
        min = super(SrInventorySession, self).action_session_stop()
        if min:
            self.timer_in_second += min * 60
        self.status = 'done'

    def action_reject_all(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject All Session Line',
            'res_model': 'sr.reject.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'sr.inventory.session',
                'active_id': self.id,
            }
        }

    def action_create_re_session(self):
        self.ensure_one()
        self.re_session_created = True
        lines_to_copy = self.session_line_ids.filtered(lambda l: l.status in ['rejected'])

        new_line_vals = [
            (0, 0, {
                'product_id': line.product_id.id,
                'location_id': line.location_id.id,
                'status': 'pending',
            }) for line in lines_to_copy
        ]
        if new_line_vals:
            self.env['sr.inventory.session'].create({
                'user_id': self.user_id.id,
                'approver_id': self.approver_id.id,
                'warehouse_id': self.warehouse_id.id,
                'location_id': self.location_id.id,
                'type': self.type,
                'date': fields.Date.today(),
                'session_line_ids': new_line_vals,
                'original_session_id': self.id,
                'inventory_count_id': self.inventory_count_id.id,
                'is_re_session': True,
            })

    def action_open_re_session(self):
        self.ensure_one()
        re_session_id = self.env['sr.inventory.session'].search([
            ('original_session_id', '=', self.id)
        ], limit=1, order='id desc')
        if re_session_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Re-Session',
                'res_model': 'sr.inventory.session',
                'res_id': re_session_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def unlink(self):
        for record in self:
            if record.status != 'draft':
                raise ValidationError("You can only delete Inventory Session in Draft state.")
            linked_count_ids = self.env['sr.inventory.counting'].search([('id', '=', record.inventory_count_id.id)])
            if linked_count_ids:
                raise ValidationError('You cannot delete this Inventory Session because it is linked to a Count.')
        return super().unlink()


class SrInventorySessionLine(models.Model):
    _name = 'sr.inventory.session.line'
    _description = 'Inventory Session Line'

    inventory_session_id = fields.Many2one('sr.inventory.session')
    product_id = fields.Many2one('product.product', string='Product', domain=[('type', '!=', 'service')])
    counted_qty = fields.Float(string='Counted qty')
    parent_status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done')
    ], default='draft', string="Status", related="inventory_session_id.status")
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approve', 'Approve'),
        ('rejected', 'Rejected')
    ], default='pending', string="Status")
    reject_reason = fields.Char('Reject Reason')

    show_reject_reason = fields.Boolean(
        compute='_compute_show_reject_reason', store=True
    )
    related_location_id = fields.Many2one(
        'stock.location',
        related='inventory_session_id.location_id',
        store=False,
        readonly=True,
        string='Location\u00A0'
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        domain="[('id', 'child_of', related_location_id)]"
    )
    adjustment_done = fields.Boolean(string='Adjustment')

    @api.constrains('counted_qty')
    def _check_counted_qty_non_negative(self):
        for rec in self:
            if rec.counted_qty < 0:
                raise ValidationError("Counted Quantity must be zero or greater.")

    @api.depends('status')
    def _compute_show_reject_reason(self):
        for line in self:
            line.show_reject_reason = line.status == 'rejected'

    def action_approve_line(self):
        self.ensure_one()
        self.write({'status': 'approve'})

    def action_reject_line(self):
        self.ensure_one()

        if self.status == 'approve' or self.status == 'pending':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Reject Session Line',
                'res_model': 'sr.reject.reason.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'active_model': self._name,
                    'active_id': self.id,
                    'hide_warning_message': True,
                }
            }
        else:
            self.write({'status': 'rejected'})
