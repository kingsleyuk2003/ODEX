from openerp import http
from openerp.addons.auth_signup.controllers.main import AuthSignupHome
from openerp.addons.web.controllers.main import ensure_db, Home
from openerp.http import request
import werkzeug.utils
import werkzeug.wrappers
import json
import openerp
# from odoo.addons.password_security.controllers.main import PasswordSecurityHome



class HomeExtend(Home):

    # source:
    def db_info(self):
        version_info = openerp.service.common.exp_version()
        return {
            'server_version': version_info.get('server_version'),
            'server_version_info': version_info.get('server_version_info'),
        }


    # ideally, this route should be `auth="user"` but that don't work in non-monodb mode.
    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        ensure_db()
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        if kw.get('redirect'):
            return werkzeug.utils.redirect(kw.get('redirect'), 303)

        # Now, I'm logging in for the second time or more
        current_user = request.env['res.users'].browse(request.session.uid)
        if not current_user.is_password_user_changed:
            #My login is for the first time, redirect to reset password
            current_user.action_signup_prepare()
            request.session.logout(keep_db=True)
            redirect = current_user.partner_id.sudo().signup_url
            return http.redirect_with_hash(redirect)

        request.uid = request.session.uid
        menu_data = request.registry['ir.ui.menu'].load_menus(request.cr, request.uid, request.debug, context=request.context)
        return request.render('web.webclient_bootstrap', qcontext={'menu_data': menu_data, 'db_info': json.dumps(self.db_info())})


