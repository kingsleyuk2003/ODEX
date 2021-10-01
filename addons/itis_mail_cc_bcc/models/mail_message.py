# -*- coding: utf-8 -*-

from email.header import decode_header
from email.utils import formataddr
import logging

from openerp import _, api, fields, models, SUPERUSER_ID
from openerp import tools
from openerp.exceptions import UserError, AccessError
from openerp.osv import expression


_logger = logging.getLogger(__name__)


def decode(text):
    """Returns unicode() string conversion of the the given encoded smtp header text"""
    # TDE proposal: move to tools ?
    if text:
        text = decode_header(text.replace('\r', ''))
        # The joining space will not be needed as of Python 3.3
        # See https://hg.python.org/cpython/rev/8c03fe231877
        return ' '.join([tools.ustr(x[0], x[1]) for x in text])


class Message(models.Model):
    """ Messages model: system notification (replacing res.log notifications),
        comments (OpenChatter discussion) and incoming emails. """
    _inherit = 'mail.message'
    
    # content
    email_partner_cc = fields.Many2many('res.partner', 'message_partnercc_rel','mailid','partner_id', string="Cc", help='Carbon copy message recipients')
    email_partner_bcc = fields.Many2many('res.partner', 'message_partnerbcc_rel','mailid','partner_id', string="Bcc", help='Blind Carbon copy message recipients')
    