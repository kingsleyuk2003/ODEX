
from openerp import api, fields, models, _

class ProductTemplateExtend(models.Model):
    _inherit = "product.template"

    @api.model
    def create(self,vals):
        #vals['default_code'] = self.env['ir.sequence'].get('prod_id_code')
        return super(ProductTemplateExtend,self).create(vals)

