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


class SrInvCountReportWizard(models.TransientModel):
    _name = 'sr.inv.count.report.wizard'
    _description = 'inventory count line report wizard'

    product_ids = fields.Many2many('product.product', string="Product")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    location_ids = fields.Many2many('stock.location', string='Location', domain="[('usage', '=', 'internal')]")
    approver_ids = fields.Many2many('res.users', string='Approver')

    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError('End Date must be greater than or equal to Start Date.')

    def action_print_report(self):
        domain = []
        today = date.today()

        end_date = self.end_date or (today if self.start_date else None)
        if self.start_date:
            domain.append(('date', '>=', self.start_date))
        if self.end_date:
            domain.append(('date', '<=', end_date))
        if self.approver_ids:
            domain.append(('approver_id', 'in', self.approver_ids.ids))
        if self.location_ids:
            domain.append(('location_id', 'in', self.location_ids.ids))

        counts = self.env['sr.inventory.counting'].search(domain)

        if not counts:
            raise UserError('No Records Found')

        count_lines = []
        for cont_line in counts:
            for line in cont_line.inventory_count_line_ids:
                if self.product_ids and line.product_id not in self.product_ids:
                    continue
                count_lines.append({
                    'name': cont_line.name,
                    'date': cont_line.date.strftime('%d/%m/%Y'),
                    'approver_id': cont_line.approver_id.display_name,
                    'product_id': line.product_id.display_name,
                    'location_id': (cont_line.warehouse_id.code or '') + '/' + (cont_line.location_id.name or ''),
                    'type': dict(cont_line._fields['type'].selection).get(cont_line.type, ''),
                    'status': dict(cont_line._fields['status'].selection).get(cont_line.status, '')
                })

        today_str = date.today().strftime('%d/%m/%Y')
        start_date_str = self.start_date.strftime('%d/%m/%Y') if self.start_date else ''
        end_date_str = self.end_date.strftime('%d/%m/%Y') if self.end_date else ''

        data = {
            'doc_ids': counts.ids,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'today': today_str,
            'product_ids': self.product_ids.ids,
            'location_ids': self.location_ids.ids,
            'approver_ids': self.approver_ids.ids,
            'lines': count_lines
        }
        return self.env.ref('sr_inventory_counting.action_report_inventory_count').report_action(self, data=data)
