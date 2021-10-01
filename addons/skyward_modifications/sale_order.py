
from openerp import api, fields, models, _

class SaleOrderExtend(models.Model):
    _inherit = 'sale.order'

    empties_total = fields.Monetary(string ="Total Value of Empties")