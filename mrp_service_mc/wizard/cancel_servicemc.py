# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import osv,fields
from openerp.tools.translate import _

class servicemc_cancel(osv.osv_memory):
    _name = 'mrp.servicemc.cancel'
    _description = 'Cancel servicemc'

    def cancel_servicemc(self, cr, uid, ids, context=None):
        """ Cancels the servicemc
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        @return:
        """
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False) or False
        assert record_id, _('Active ID not Found')
        servicemc_order_obj = self.pool.get('mrp.servicemc')
        servicemc_line_obj = self.pool.get('mrp.servicemc.line')
        servicemc_order = servicemc_order_obj.browse(cr, uid, record_id, context=context)

        if servicemc_order.invoiced or servicemc_order.invoice_method == 'none':
            servicemc_order_obj.action_cancel(cr, uid, [record_id], context=context)
        else:
            raise osv.except_osv(_('Warning!'),_('servicemc order is not invoiced.'))

        return {'type': 'ir.actions.act_window_close'}

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """ Changes the view dynamically
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param context: A standard dictionary
        @return: New arch of view.
        """
        if context is None:
            context = {}
        res = super(servicemc_cancel, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar,submenu=False)
        record_id = context and context.get('active_id', False) or False
        active_model = context.get('active_model')

        if not record_id or (active_model and active_model != 'mrp.servicemc'):
            return res

        servicemc_order = self.pool.get('mrp.servicemc').browse(cr, uid, record_id, context=context)
        if not servicemc_order.invoiced:
            res['arch'] = """
                <form string="Cancel servicemc" version="7.0">
                    <header>
                        <button name="cancel_servicemc" string="_Yes" type="object" class="oe_highlight"/>
                        or
                        <button string="Cancel" class="oe_link" special="cancel"/>
                    </header>
                    <label string="Do you want to continue?"/>
                </form>
            """
        return res

servicemc_cancel()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

