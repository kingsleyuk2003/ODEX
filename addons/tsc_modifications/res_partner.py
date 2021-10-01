
from openerp import api, fields, models, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_status = fields.Selection([('not_registered', 'Not Registered'), ('processing', 'Processing'),
                              ('registered', 'Registered')], string="Status")

