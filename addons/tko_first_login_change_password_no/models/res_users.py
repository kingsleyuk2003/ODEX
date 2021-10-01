from openerp import api, fields, models, _
from datetime import datetime,date, timedelta


class Users(models.Model):
    _inherit = 'res.users'



    @api.multi
    def action_signup_prepare(self):
        for record in self:
            record.sudo().partner_id.signup_prepare(signup_type='reset', expiration=datetime.now() + timedelta(days=1))

    is_password_user_changed = fields.Boolean(string='Is Password Changed by User')