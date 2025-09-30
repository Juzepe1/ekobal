# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Sitaram Solutions (<https://sitaramsolutions.in/>).
#
#    For Module Support : info@sitaramsolutions.in  or Mobile/Whatsapp : +91 7405030365
#
##############################################################################

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, datetime
from odoo.exceptions import UserError


class InventorySessionReportWizard(models.TransientModel):
    _name = 'inventory.session.report.wizard'
    _description = 'Inventory Session Report Wizard'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    user_ids = fields.Many2many('res.users', string="User")

    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError("End Date must be greater than or equal to Start Date.")

    def action_print_report(self):
        domain = []
        today = date.today()

        if self.start_date:
            domain.append(('date', '>=', self.start_date))
        if self.end_date:
            domain.append(('date', '<=', self.end_date))
        if not self.start_date and not self.end_date:
            domain.append(('date', '<=', today))

        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))

        sessions = self.env['sr.inventory.session'].search(domain)

        session_data = []
        for session_line in sessions:
            for line in session_line.session_line_ids:
                session_data.append({
                    'name': session_line.name,
                    'date': session_line.date.strftime('%d/%m/%Y'),
                    'user_ids': session_line.user_id.display_name,
                    'approver_id': session_line.approver_id.display_name,
                    'product_id': line.product_id.display_name,
                    'counted_qty': line.counted_qty,
                    'total_product': session_line.total_product,
                    'location_id': line.location_id.display_name,
                    'type': dict(session_line._fields['type'].selection).get(session_line.type, ''),
                    'session_status': dict(session_line._fields['status'].selection).get(session_line.status, ''),
                    'count_status': dict(line._fields['status'].selection).get(line.status, '')
                })

        if not sessions:
            raise UserError('No Records Found')

        user_ids = self.user_ids.ids if self.user_ids else sessions.mapped('user_id.id')
        today_str = today.strftime('%d/%m/%Y')
        start_date_str = self.start_date.strftime('%d/%m/%Y') if self.start_date else ''
        end_date_str = self.end_date.strftime('%d/%m/%Y') if self.end_date else today_str

        data = {
            'start_date': start_date_str,
            'end_date': end_date_str,
            'today': today_str,
            'user_name': user_ids,
            'lines': session_data,
        }
        return self.env.ref('sr_inventory_counting.action_report_inventory_session').report_action(self, data=data)
