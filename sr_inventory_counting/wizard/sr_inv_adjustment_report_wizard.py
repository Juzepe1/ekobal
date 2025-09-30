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


class SrInvAdjustmentReportWizard(models.TransientModel):
    _name = 'sr.inv.adjustment.report.wizard'
    _description = 'inventory adjustment report wizard'

    product_ids = fields.Many2many('product.product', string="Product")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    location_ids = fields.Many2many('stock.location', string='Location', domain="[('usage', '=', 'internal')]")

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
        if self.product_ids:
            domain.append(('sr_adjustment_line_ids.product_id', 'in', self.product_ids.ids))
        if self.location_ids:
            domain.append(('sr_adjustment_line_ids.location_id', 'in', self.location_ids.ids))

        adjustments = self.env['sr.inv.adjustment'].search(domain)

        if not adjustments:
            raise UserError('No Records Found')

        line_data = []
        for adj in adjustments:
            for line in adj.sr_adjustment_line_ids:
                if self.product_ids and line.product_id not in self.product_ids:
                    continue
                if self.location_ids and line.location_id not in self.location_ids:
                    continue

                line_data.append({
                    'date': adj.date.strftime('%d/%m/%Y') if adj.date else '',
                    'count': adj.count_id.name or '',
                    'product': line.product_id.display_name or '',
                    'location': line.location_id.display_name or '',
                    'counted_qty': line.counted_qty,
                    'on_hand_qty': line.on_hand_qty,
                    'difference': line.difference,
                })

        today_str = today.strftime('%d/%m/%Y')
        start_date_str = self.start_date.strftime('%d/%m/%Y') if self.start_date else ''
        end_date_str = end_date.strftime('%d/%m/%Y') if end_date else ''

        data = {
            'model': 'sr.inv.adjustment.line',
            'today': today_str,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'lines': line_data,
        }

        return self.env.ref('sr_inventory_counting.action_report_inv_adjustment').report_action(self, data=data)
