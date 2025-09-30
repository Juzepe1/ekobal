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


class SrApproveWizard(models.TransientModel):
    _name = 'sr.approve.wizard'
    _description = 'approve wizard'

    message = fields.Text(default="Warning: This session includes rejected lines. Continue with approval?")

    def action_confirm_approve(self):
        active_id = self.env.context.get('active_id')
        session = self.env['sr.inventory.session'].browse(active_id)
        session.session_line_ids.write({'status': 'approve'})
