# -*- coding: utf-8 -*-
# © 2017 Jérôme Guerriat
# © 2017 Niboo SPRL (https://www.niboo.be/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import http, _
from openerp.addons.bus.controllers.main import BusController
from openerp.http import request
import logging

_logger = logging.getLogger(__name__)


class BusControllerInherit(BusController):

    @http.route('/longpolling/poll', type="json", auth="public")
    def poll(self, channels, last, options=None):
        if request.session.uid:
            active_user = request.env['res.users'].browse(request.session.uid)
            _logger.info("### active user: %s ###" % active_user.login)

        return super(BusControllerInherit, self).poll(channels, last, options)
