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


class SrAdjustmentConfirmationWizard(models.TransientModel):
    _name = 'sr.adjustment.confirmation.wizard'
    _description = 'Adjustment Wizard'

    caution = fields.Text(default="You're about to perform a physical inventory adjustment. Would you like to proceed?")

    def action_ok(self):
        active_id = self.env.context.get('active_id')
        adjustment = self.env['sr.inv.adjustment'].browse(active_id)
        adjustment.adjustment_line_count = len(adjustment.sr_adjustment_line_ids)

        for line in adjustment.sr_adjustment_line_ids:
            if not line.product_id or not line.location_id:
                continue

            ctx = dict(self.env.context, set_inventory_quantity_auto_apply=True)
            quant = self.env['stock.quant'].with_context(ctx).sudo().search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', line.location_id.id),
            ], limit=1)

            if not quant:
                quant = self.env['stock.quant'].with_context(ctx).sudo().create({
                    'product_id': line.product_id.id,
                    'location_id': line.location_id.id,
                })
            existing_move_line_ids = self.env['stock.move.line'].sudo().search([
                ('product_id', '=', line.product_id.id),
                ('location_dest_id', '=', line.location_id.id),
            ])
            for move_line in existing_move_line_ids:
                if not move_line.adjustment_id:
                    move_line.adjustment_id = adjustment.id

            quant.inventory_quantity = line.counted_qty
            quant.inventory_quantity_set = True
            quant.with_context(ctx).sudo().action_apply_inventory()

            self.env['stock.quant'].sudo().browse(quant.id)

            new_move_lines = self.env['stock.move.line'].sudo().search([
                ('product_id', '=', line.product_id.id),
                ('location_dest_id', '=', line.location_id.id),
                ('id', 'not in', existing_move_line_ids.ids),
            ])

            for move_line in new_move_lines:
                if not move_line.adjustment_id:
                    move_line.adjustment_id = adjustment.id

        adjustment.status = 'done'
        return {'type': 'ir.actions.act_window_close'}
