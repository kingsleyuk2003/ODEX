
from openerp import api, fields, models, _



class KinTicketExtend(models.Model):
    _inherit = "kin.ticket"

   # engineer_costs = fields.One2many('account.analytic.account')