# -*- coding: utf-8 -*-

from openerp import api, fields, models


class DocumentFollowers(models.Model):
    """ mail_followers holds the data related to the follow mechanism inside
    Odoo. Partners can choose to follow documents (records) of any kind
    that inherits from mail.thread. Following documents allow to receive
    notifications for new messages. A subscription is characterized by:

    :param: res_model: model of the followed objects
    :param: res_id: ID of resource (may be 0 for every objects)
    """
    _name = 'document.followers'
    _rec_name = 'model_id'
#    _log_access = False
    _description = 'Document Followers'

    model_id = fields.Many2one(
        'ir.model', string='Model')    
    auto_add_followers = fields.Boolean(string="Auto Add Followers")
    internal_follower_ids = fields.Many2many(
        'res.users','res_users_int_followers_rel','doc_follower_id','user_id', string='Internal Followers')
    external_follower_ids = fields.Many2many(
        'res.users','res_users_ext_followers_rel','doc_follower_id','user_id', string='External Followers')