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


class SrRejectReasonWizard(models.TransientModel):
    _name = 'sr.reject.reason.wizard'
    _description = 'Reject wizard'

    message = fields.Text(default="Warning: You are about to Reject lines that were previously Approved. Proceed?")
    reason = fields.Text('Reason')
    session_line_ids = fields.Many2one('sr.inventory.session.line', string='Session Lines')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if not self.env.context.get('hide_warning_message'):
            res['message'] = "Warning: You are about to Reject lines that were previously Approved. Proceed?"
        else:
            res['message'] = ""
        return res

    def action_reject_ok(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model == 'sr.inventory.session':
            session = self.env[active_model].browse(active_id)
            session.session_line_ids.write({
                'status': 'rejected',
                'reject_reason': self.reason,
            })

        if active_model == 'sr.inventory.counting':
            count = self.env[active_model].browse(active_id)
            if count.status != 'to_be_approve':
                raise UserError("Only counts in 'To Be Approve' status can be rejected.")
            count.write({
                'status': 'rejected',
                'reject_reason': self.reason
            })

        if active_model == 'sr.inventory.session.line':
            line = self.env[active_model].browse(active_id)
            line.write({
                'status': 'rejected',
                'reject_reason': self.reason,
            })
