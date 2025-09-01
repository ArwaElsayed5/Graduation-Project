from odoo import models, fields


class SlottingResult(models.Model):
    _name = 'slotting.result'
    _description = 'Slotting Optimization Result'

    item_id = fields.Many2one('product.product', string='Item', ondelete='set null')
    slot_id = fields.Char(string='Slot')
    score = fields.Float(string='Fitness Score')
    timeframe = fields.Selection([
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('this_quarter', 'This Quarter')
    ], string='Timeframe')

    # Add the active field for soft deletion
    active = fields.Boolean(string="Active", default=True)
