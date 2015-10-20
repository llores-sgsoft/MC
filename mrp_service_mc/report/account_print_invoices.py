# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
#    Authors: Aktiva (<http://www.aktiva.com.mx/>)
#             
#    Coded by: Luis Felipe Lores Caignet (luisfqba@gmail.com  llores@aktiva.com.mx)
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

import openerp
from openerp.tools.translate import _
from openerp.report import report_sxw
import time

class PrintPartnerInvoice(report_sxw.rml_parse):
    
    def __init__(self, cr, uid, name, context):
        super(PrintPartnerInvoice, self).__init__(cr, uid, name, context=context)
        
        self.localcontext.update({
            'get_invoices':  self._get_partner_invoice,
            'get_emitter_data': self._get_emitter_data,
            'get_partner_data': self._get_partner_data,
            'time':time.strftime('%d de %B del %Y'),
        })       
           
    def _get_partner_invoice(self,invoice): 
        sql_query = "SELECT id, number, date_invoice, num_fact_proyecto,sale_ext_origin, state from account_invoice  where partner_id = "+str(invoice.partner_id.id)+" and state in ('paid','open')"
        self.cr.execute(sql_query)    
        result = self.cr.fetchall()
        return result     
    
    def _get_emitter_data(self, partner, data='name'):
        # Simple cache for speed up
        if not hasattr(self, 'emitter_data'):
            self.emitter_data = self._get_invoice_address(partner)
        return self.emitter_data[data]

    def _get_partner_data(self, partner, data='name'):
        # Simple cache for speed up
        if not hasattr(self, 'partner_data'):
            self.partner_data = self._get_invoice_address(partner)
        return self.partner_data[data]

    def _get_invoice_address(self, partner):
        # Si la dirección del partner no es default o invoice
        if partner.type not in ['invoice', 'default']:
            # Obtiene la dirección del padre
            add_invoice = partner.parent_id
        else:
            add_invoice = partner

        # Aseguramos que la dirección sea de facturación
        if add_invoice.type in ['invoice', 'default']:
            res = {
                'name': add_invoice.name or '',
                'vat': add_invoice.vat_split or add_invoice.vat or '',
                'street': add_invoice.street or False,
                'no_ext': add_invoice.l10n_mx_street3 or '',
                'no_int': add_invoice.l10n_mx_street4 or '',
                'suburb': add_invoice.street2 or '',
                'city': add_invoice.city or '',
                'state': add_invoice.state_id.name or '',
                'country': add_invoice.country_id.name or '',
                'county': add_invoice.l10n_mx_city2 or '',
                'zip': add_invoice.zip or '',
                'phone': add_invoice.phone or '',
                'fax': add_invoice.fax or '',
                'mobile': add_invoice.mobile or '',
            }
            if not res['vat']:
                # Comprobamos que tengamos un RFC definido
                raise openerp.exceptions.Warning(
                    _('Not Vat Number set on partner'))
        else:
            raise openerp.exceptions.Warning(
                _('Customer Address Not Invoice Type'))
        return res

    
report_sxw.report_sxw(
    'report.account.invoice.partner.webkit',
    'account.invoice',
    'addons/ak_account_print_partner_invoices/report/account_print_invoices.mako',
    parser=PrintPartnerInvoice,
)
