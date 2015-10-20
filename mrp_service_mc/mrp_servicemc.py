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

from openerp.osv import fields,osv
from openerp import netsvc
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class mrp_servicemc(osv.osv):
    _name = 'mrp.servicemc'
    _inherit = 'mail.thread'
    _description = 'servicemc Order'

    def _amount_untaxed(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates untaxed amount.
        @param self: The object pointer
        @param cr: The current row, from the database cursor,
        @param uid: The current user ID for security checks
        @param ids: List of selected IDs
        @param field_name: Name of field.
        @param arg: Argument
        @param context: A standard dictionary for contextual values
        @return: Dictionary of values.
        """
        res = {}
        cur_obj = self.pool.get('res.currency')

        for servicemc in self.browse(cr, uid, ids, context=context):
            res[servicemc.id] = 0.0
            for line in servicemc.operations:
                res[servicemc.id] += line.price_subtotal
            for line in servicemc.fees_lines:
                res[servicemc.id] += line.price_subtotal
            cur = servicemc.pricelist_id.currency_id
            res[servicemc.id] = cur_obj.round(cr, uid, cur, res[servicemc.id])
        return res

    def _amount_tax(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates taxed amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        #return {}.fromkeys(ids, 0)
        cur_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        for servicemc in self.browse(cr, uid, ids, context=context):
            val = 0.0
            cur = servicemc.pricelist_id.currency_id
            for line in servicemc.operations:
                #manage prices with tax included use compute_all instead of compute
                if line.to_invoice:
                    tax_calculate = tax_obj.compute_all(cr, uid, line.tax_id, line.price_unit, line.product_uom_qty, line.product_id, servicemc.partner_id)
                    for c in tax_calculate['taxes']:
                        val += c['amount']
            for line in servicemc.fees_lines:
                if line.to_invoice:
                    tax_calculate = tax_obj.compute_all(cr, uid, line.tax_id, line.price_unit, line.product_uom_qty,  line.product_id, servicemc.partner_id)
                    for c in tax_calculate['taxes']:
                        val += c['amount']
            res[servicemc.id] = cur_obj.round(cr, uid, cur, val)
        return res

    def _amount_total(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates total amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        untax = self._amount_untaxed(cr, uid, ids, field_name, arg, context=context)
        tax = self._amount_tax(cr, uid, ids, field_name, arg, context=context)
        cur_obj = self.pool.get('res.currency')
        for id in ids:
            servicemc = self.browse(cr, uid, id, context=context)
            cur = servicemc.pricelist_id.currency_id
            res[id] = cur_obj.round(cr, uid, cur, untax.get(id, 0.0) + tax.get(id, 0.0))
        return res

    def _get_default_address(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        partner_obj = self.pool.get('res.partner')
        for data in self.browse(cr, uid, ids, context=context):
            adr_id = False
            if data.partner_id:
                adr_id = partner_obj.address_get(cr, uid, [data.partner_id.id], ['default'])['default']
            res[data.id] = adr_id
        return res

    def _get_lines(self, cr, uid, ids, context=None):
        return self.pool['mrp.servicemc'].search(
            cr, uid, [('operations', 'in', ids)], context=context)

    def _get_fee_lines(self, cr, uid, ids, context=None):
        return self.pool['mrp.servicemc'].search(
            cr, uid, [('fees_lines', 'in', ids)], context=context)

    _columns = {
        'facproducto': fields.many2one('product.product','Producto'),   
        'facpreciounitario': fields.float('Precio unitario', help = 'Precio unitario',  required=False), 
        'facimpuestos': fields.many2many('account.tax', 'repair_operation_line_tax', 'repair_operation_line_id', 'tax_id', 'Impuesto'),
        'facafacturar':fields.boolean('A facturar'),
        'facsubtotal':fields.float('Subtotal'),
        'total': fields.float('Total'),
        'faccantidad': fields.float('Cantidad',help = 'Cantidad',required=True),
        'noeconomicomc':fields.char('Numero Economico',size=24),
        'noseriemc':fields.char('Numero de Serie',size=24),
        'name': fields.char('servicemc Reference',size=24, required=True, states={'confirmed':[('readonly',True)]}),
        'product_id': fields.many2one('product.product', string='Product to give service', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'partner_id' : fields.many2one('res.partner', 'Partner', select=True, help='Choose partner for whom the order will be invoiced and delivered.', states={'confirmed':[('readonly',True)]}),
        'address_id': fields.many2one('res.partner', 'Delivery Address', domain="[('parent_id','=',partner_id)]", states={'confirmed':[('readonly',True)]}),
        'default_address_id': fields.function(_get_default_address, type="many2one", relation="res.partner"),
        'prodlot_id': fields.many2one('stock.production.lot', 'Lot Number', select=True, states={'draft':[('readonly',False)]},domain="[('product_id','=',product_id)]"),
        'state': fields.selection([
            ('draft','Quotation'),
            ('cancel','Cancelled'),
            ('confirmed','Confirmed'),
            ('under_servicemc','Under servicio'),
            ('ready','listo para dar servicio'),
            ('2binvoiced','To be Invoiced'),
            ('invoice_except','Invoice Exception'),
            ('done','Hecho')
            ], 'Status', readonly=True, track_visibility='onchange',
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed servicemc order. \
            \n* The \'Confirmed\' status is used when a user confirms the servicemc order. \
            \n* The \'Ready to servicemc\' status is used to start to servicemcing, user can start servicemcing only after servicemc order is confirmed. \
            \n* The \'To be Invoiced\' status is used to generate the invoice before or after servicemcing done. \
            \n* The \'Done\' status is set when servicemcing is completed.\
            \n* The \'Cancelled\' status is used when user cancel servicemc order.'),
        'location_id': fields.many2one('stock.location', 'Current Location', select=True, readonly=True, states={'draft':[('readonly',False)], 'confirmed':[('readonly',True)]}),
        'location_dest_id': fields.many2one('stock.location', 'Delivery Location', readonly=True, states={'draft':[('readonly',False)], 'confirmed':[('readonly',True)]}),
        'move_id': fields.many2one('stock.move', 'Move',required=True, domain="[('product_id','=',product_id)]", readonly=True, states={'draft':[('readonly',False)]}),
        'guarantee_limit': fields.date('Warranty Expiration', help="The warranty expiration limit is computed as: last move date + warranty defined on selected product. If the current date is below the warranty expiration limit, each operation and fee you will add will be set as 'not to invoiced' by default. Note that you can change manually afterwards.", states={'confirmed':[('readonly',True)]}),
        'operations' : fields.one2many('mrp.servicemc.line', 'servicemc_id', 'Operation Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'pricelist_id': fields.many2one('product.pricelist', 'Pricelist', help='Pricelist of the selected partner.'),
        'partner_invoice_id':fields.many2one('res.partner', 'Invoicing Address'),
        'invoice_method':fields.selection([
            ("none","No Invoice"),
            ("b4servicemc","Before servicemc"),
            ("after_servicemc","After servicemc")
           ], "Invoice Method",
            select=True, required=True, states={'draft':[('readonly',False)]}, readonly=True, help='Selecting \'Before servicemc\' or \'After servicemc\' will allow you to generate invoice before or after the servicemc is done respectively. \'No invoice\' means you don\'t want to generate invoice for this servicemc order.'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
        'picking_id': fields.many2one('stock.picking', 'Picking',readonly=True),
        'fees_lines': fields.one2many('mrp.servicemc.fee', 'servicemc_id', 'Fees Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'internal_notes': fields.text('Internal Notes'),
        'quotation_notes': fields.text('Quotation Notes'),
        'company_id': fields.many2one('res.company', 'Company'),
        'deliver_bool': fields.boolean('Deliver', help="Check this box if you want to manage the delivery once the product is servicemced and create a picking with selected product. Note that you can select the locations in the Info tab, if you have the extended view.", states={'confirmed':[('readonly',True)]}),
        'invoiced': fields.boolean('Invoiced', readonly=True),
        'servicemced': fields.boolean('Entregado', readonly=True),
        'amount_untaxed': fields.function(_amount_untaxed, string='Untaxed Amount',
            store={
                'mrp.servicemc': (lambda self, cr, uid, ids, c={}: ids, ['operations', 'fees_lines'], 10),
                'mrp.servicemc.line': (_get_lines, ['price_unit', 'price_subtotal', 'product_id', 'tax_id', 'product_uom_qty', 'product_uom'], 10),
                'mrp.servicemc.fee': (_get_fee_lines, ['price_unit', 'price_subtotal', 'product_id', 'tax_id', 'product_uom_qty', 'product_uom'], 10),
            }),
        'amount_tax': fields.function(_amount_tax, string='Taxes',
            store={
                'mrp.servicemc': (lambda self, cr, uid, ids, c={}: ids, ['operations', 'fees_lines'], 10),
                'mrp.servicemc.line': (_get_lines, ['price_unit', 'price_subtotal', 'product_id', 'tax_id', 'product_uom_qty', 'product_uom'], 10),
                'mrp.servicemc.fee': (_get_fee_lines, ['price_unit', 'price_subtotal', 'product_id', 'tax_id', 'product_uom_qty', 'product_uom'], 10),
            }),
        'amount_total': fields.function(_amount_total, string='Total',
            store={
                'mrp.servicemc': (lambda self, cr, uid, ids, c={}: ids, ['operations', 'fees_lines'], 10),
                'mrp.servicemc.line': (_get_lines, ['price_unit', 'price_subtotal', 'product_id', 'tax_id', 'product_uom_qty', 'product_uom'], 10),
                'mrp.servicemc.fee': (_get_fee_lines, ['price_unit', 'price_subtotal', 'product_id', 'tax_id', 'product_uom_qty', 'product_uom'], 10),
            }),
         'clienteNombre': fields.many2one('res.partner','Nombre del Cliente', required= True),   
        'clienteEntregaNombre': fields.many2one('res.partner','Nombre del Cliente'),    
        'empresaEntregaNombre': fields.many2one('hr.employee','Nombre'),    
        'empresaNombre': fields.many2one('hr.employee','Nombre Jefe de Area'),      
        'produccion_fecha_final':  fields.date('Fecha final', required = False),
        'produccion_notas': fields.text('Notas'),
        'produccion_re_ter_unidad': fields.many2one('hr.employee','Reporta Terminio de la Unidad', required=False), 
        'calidad_fecha_inicial':  fields.date('Fecha Inicial', required = False),
        'calidad_fecha_final':  fields.date('Fecha Final', required = False),
        'calidad_notas': fields.text('Notas'),
        'calidad_re_li_unidad': fields.many2one('hr.employee','Reporta Terminio de la Unidad', required=False), 
        'calidad_fecha_liberacion':  fields.date('Fecha de Liberacion', required = False),
        'calidad_pri_inpeccion': fields.boolean('Primera Inspeccion'),
        'calidad_liberada': fields.boolean('Liberada'),
        'fecha_alta': fields.date('Fecha de Alta', required = True),
        'modelo_id': fields.many2one('fleet.vehicle','Modelo',required = True),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'deliver_bool': lambda *a: True,
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'mrp.servicemc'),
        'invoice_method': lambda *a: 'none',
        'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'mrp.servicemc', context=context),
        'pricelist_id': lambda self, cr, uid,context : self.pool.get('product.pricelist').search(cr, uid, [('type','=','sale')])[0]
    }

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({
            'state':'draft',
            'servicemced':False,
            'invoiced':False,
            'invoice_id': False,
            'picking_id': False,
            'name': self.pool.get('ir.sequence').get(cr, uid, 'mrp.servicemc'),
        })
        return super(mrp_servicemc, self).copy(cr, uid, id, default, context)

    def onchange_product_id(self, cr, uid, ids, product_id=None):
        """ On change of product sets some values.
        @param product_id: Changed product
        @return: Dictionary of values.
        """
        return {'value': {
                    'prodlot_id': False,
                    'move_id': False,
                    'guarantee_limit' :False,
                    'location_id':  False,
                    'location_dest_id': False,
                }
        }

    def onchange_move_id(self, cr, uid, ids, prod_id=False, move_id=False):
        """ On change of move id sets values of guarantee limit, source location,
        destination location, partner and partner address.
        @param prod_id: Id of product in current record.
        @param move_id: Changed move.
        @return: Dictionary of values.
        """
        data = {}
        data['value'] = {'guarantee_limit': False, 'location_id': False, 'prodlot_id': False, 'partner_id': False}
        if not prod_id:
            return data
        if move_id:
            move =  self.pool.get('stock.move').browse(cr, uid, move_id)
            product = self.pool.get('product.product').browse(cr, uid, prod_id)
            limit = datetime.strptime(move.date_expected, '%Y-%m-%d %H:%M:%S') + relativedelta(months=int(product.warranty))
            data['value']['guarantee_limit'] = limit.strftime('%Y-%m-%d')
            data['value']['location_id'] = move.location_dest_id.id
            data['value']['location_dest_id'] = move.location_dest_id.id
            data['value']['prodlot_id'] = move.prodlot_id.id
            if move.partner_id:
                data['value']['partner_id'] = move.partner_id.id
            else:
                data['value']['partner_id'] = False
            d = self.onchange_partner_id(cr, uid, ids, data['value']['partner_id'], data['value']['partner_id'])
            data['value'].update(d['value'])
        return data

    def button_dummy(self, cr, uid, ids, context=None):
        return True

    def onchange_partner_id(self, cr, uid, ids, part, address_id):
        """ On change of partner sets the values of partner address,
        partner invoice address and pricelist.
        @param part: Changed id of partner.
        @param address_id: Address id from current record.
        @return: Dictionary of values.
        """
        part_obj = self.pool.get('res.partner')
        pricelist_obj = self.pool.get('product.pricelist')
        if not part:
            return {'value': {
                        'address_id': False,
                        'partner_invoice_id': False,
                        'pricelist_id': pricelist_obj.search(cr, uid, [('type','=','sale')])[0]
                    }
            }
        addr = part_obj.address_get(cr, uid, [part], ['delivery', 'invoice', 'default'])
        partner = part_obj.browse(cr, uid, part)
        pricelist = partner.property_product_pricelist and partner.property_product_pricelist.id or False
        return {'value': {
                    'address_id': addr['delivery'] or addr['default'],
                    'partner_invoice_id': addr['invoice'],
                    'pricelist_id': pricelist
                }
        }

    def onchange_lot_id(self, cr, uid, ids, lot, product_id):
        """ On change of Serial Number sets the values of source location,
        destination location, move and guarantee limit.
        @param lot: Changed id of Serial Number.
        @param product_id: Product id from current record.
        @return: Dictionary of values.
        """
        move_obj = self.pool.get('stock.move')
        data = {}
        data['value'] = {
            'location_id': False,
            'location_dest_id': False,
            'move_id': False,
            'guarantee_limit': False
        }

        if not lot:
            return data
        move_ids = move_obj.search(cr, uid, [('prodlot_id', '=', lot)])

        if not len(move_ids):
            return data

        def get_last_move(lst_move):
            while lst_move.move_dest_id and lst_move.move_dest_id.state == 'done':
                lst_move = lst_move.move_dest_id
            return lst_move

        move_id = move_ids[0]
        move = get_last_move(move_obj.browse(cr, uid, move_id))
        data['value']['move_id'] = move.id
        d = self.onchange_move_id(cr, uid, ids, product_id, move.id)
        data['value'].update(d['value'])
        return data

    def action_cancel_draft(self, cr, uid, ids, *args):
        """ Cancels servicemc order when it is in 'Draft' state.
        @param *arg: Arguments
        @return: True
        """
        if not len(ids):
            return False
        mrp_line_obj = self.pool.get('mrp.servicemc.line')
        for servicemc in self.browse(cr, uid, ids):
            mrp_line_obj.write(cr, uid, [l.id for l in servicemc.operations], {'state': 'draft'})
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for id in ids:
            wf_service.trg_create(uid, 'mrp.servicemc', id, cr)
        return True

    def action_confirm(self, cr, uid, ids, *args):
        """ servicemc order state is set to 'To be invoiced' when invoice method
        is 'Before servicemc' else state becomes 'Confirmed'.
        @param *arg: Arguments
        @return: True
        """
        mrp_line_obj = self.pool.get('mrp.servicemc.line')
        for o in self.browse(cr, uid, ids):
            if (o.invoice_method == 'b4servicemc'):
                self.write(cr, uid, [o.id], {'state': '2binvoiced'})
            else:
                self.write(cr, uid, [o.id], {'state': 'confirmed'})
                for line in o.operations:
                    if line.product_id.track_production and not line.prodlot_id:
                        raise osv.except_osv(_('Warning!'), _("Serial number is required for operation line with product '%s'") % (line.product_id.name))
                mrp_line_obj.write(cr, uid, [l.id for l in o.operations], {'state': 'confirmed'})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels servicemc order.
        @return: True
        """
        mrp_line_obj = self.pool.get('mrp.servicemc.line')
        for servicemc in self.browse(cr, uid, ids, context=context):
            if not servicemc.invoiced:
                mrp_line_obj.write(cr, uid, [l.id for l in servicemc.operations], {'state': 'cancel'}, context=context)
            else:
                raise osv.except_osv(_('Warning!'),_('servicemc order is already invoiced.'))
        return self.write(cr,uid,ids,{'state':'cancel'})

    def wkf_invoice_create(self, cr, uid, ids, *args):
        self.action_invoice_create(cr, uid, ids)
        return True

    def action_invoice_create(self, cr, uid, ids, group=False, context=None):
        """ Creates invoice(s) for servicemc order.
        @param group: It is set to true when group invoice is to be generated.
        @return: Invoice Ids.
        """
        res = {}
        invoices_group = {}
        inv_line_obj = self.pool.get('account.invoice.line')
        inv_obj = self.pool.get('account.invoice')
        servicemc_line_obj = self.pool.get('mrp.servicemc.line')
        servicemc_fee_obj = self.pool.get('mrp.servicemc.fee')
        for servicemc in self.browse(cr, uid, ids, context=context):
            res[servicemc.id] = False
            if servicemc.state in ('draft','cancel') or servicemc.invoice_id:
                continue
            if not (servicemc.partner_id.id and servicemc.partner_invoice_id.id):
                raise osv.except_osv(_('No partner!'),_('You have to select a Partner Invoice Address in the servicemc form!'))
            comment = servicemc.quotation_notes
            if (servicemc.invoice_method != 'none'):
                if group and servicemc.partner_invoice_id.id in invoices_group:
                    inv_id = invoices_group[servicemc.partner_invoice_id.id]
                    invoice = inv_obj.browse(cr, uid, inv_id)
                    invoice_vals = {
                        'name': invoice.name +', '+servicemc.name,
                        'origin': invoice.origin+', '+servicemc.name,
                        'comment':(comment and (invoice.comment and invoice.comment+"\n"+comment or comment)) or (invoice.comment and invoice.comment or ''),
                    }
                    inv_obj.write(cr, uid, [inv_id], invoice_vals, context=context)
                else:
                    if not servicemc.partner_id.property_account_receivable:
                        raise osv.except_osv(_('Error!'), _('No account defined for partner "%s".') % servicemc.partner_id.name )
                    account_id = servicemc.partner_id.property_account_receivable.id
                    inv = {
                        'name': servicemc.name,
                        'origin':servicemc.name,
                        'type': 'out_invoice',
                        'account_id': account_id,
                        'partner_id': servicemc.partner_id.id,
                        'currency_id': servicemc.pricelist_id.currency_id.id,
                        'comment': servicemc.quotation_notes,
                        'fiscal_position': servicemc.partner_id.property_account_position.id
                    }
                    inv_id = inv_obj.create(cr, uid, inv)
                    invoices_group[servicemc.partner_invoice_id.id] = inv_id
                self.write(cr, uid, servicemc.id, {'invoiced': True, 'invoice_id': inv_id})

                for operation in servicemc.operations:
                    if operation.to_invoice == True:
                        if group:
                            name = servicemc.name + '-' + operation.name
                        else:
                            name = operation.name

                        if operation.product_id.property_account_income:
                            account_id = operation.product_id.property_account_income.id
                        elif operation.product_id.categ_id.property_account_income_categ:
                            account_id = operation.product_id.categ_id.property_account_income_categ.id
                        else:
                            raise osv.except_osv(_('Error!'), _('No account defined for product "%s".') % operation.product_id.name )

                        invoice_line_id = inv_line_obj.create(cr, uid, {
                            'invoice_id': inv_id,
                            'name': name,
                            'origin': servicemc.name,
                            'account_id': account_id,
                            'quantity': operation.product_uom_qty,
                            'invoice_line_tax_id': [(6,0,[x.id for x in operation.tax_id])],
                            'uos_id': operation.product_uom.id,
                            'price_unit': operation.price_unit,
                            'price_subtotal': operation.product_uom_qty*operation.price_unit,
                            'product_id': operation.product_id and operation.product_id.id or False
                        })
                        servicemc_line_obj.write(cr, uid, [operation.id], {'invoiced': True, 'invoice_line_id': invoice_line_id})
                for fee in servicemc.fees_lines:
                    if fee.to_invoice == True:
                        if group:
                            name = servicemc.name + '-' + fee.name
                        else:
                            name = fee.name
                        if not fee.product_id:
                            raise osv.except_osv(_('Warning!'), _('No product defined on Fees!'))

                        if fee.product_id.property_account_income:
                            account_id = fee.product_id.property_account_income.id
                        elif fee.product_id.categ_id.property_account_income_categ:
                            account_id = fee.product_id.categ_id.property_account_income_categ.id
                        else:
                            raise osv.except_osv(_('Error!'), _('No account defined for product "%s".') % fee.product_id.name)

                        invoice_fee_id = inv_line_obj.create(cr, uid, {
                            'invoice_id': inv_id,
                            'name': name,
                            'origin': servicemc.name,
                            'account_id': account_id,
                            'quantity': fee.product_uom_qty,
                            'invoice_line_tax_id': [(6,0,[x.id for x in fee.tax_id])],
                            'uos_id': fee.product_uom.id,
                            'product_id': fee.product_id and fee.product_id.id or False,
                            'price_unit': fee.price_unit,
                            'price_subtotal': fee.product_uom_qty*fee.price_unit
                        })
                        servicemc_fee_obj.write(cr, uid, [fee.id], {'invoiced': True, 'invoice_line_id': invoice_fee_id})
                res[servicemc.id] = inv_id
        return res

    def action_servicemc_ready(self, cr, uid, ids, context=None):
        """ Writes servicemc order state to 'Ready'
        @return: True
        """
        for servicemc in self.browse(cr, uid, ids, context=context):
            self.pool.get('mrp.servicemc.line').write(cr, uid, [l.id for
                    l in servicemc.operations], {'state': 'confirmed'}, context=context)
            self.write(cr, uid, [servicemc.id], {'state': 'ready'})
        return True

    def action_servicemc_start(self, cr, uid, ids, context=None):
        """ Writes servicemc order state to 'Under servicemc'
        @return: True
        """
        servicemc_line = self.pool.get('mrp.servicemc.line')
        for servicemc in self.browse(cr, uid, ids, context=context):
            servicemc_line.write(cr, uid, [l.id for
                    l in servicemc.operations], {'state': 'confirmed'}, context=context)
            servicemc.write({'state': 'under_servicemc'})
        return True

    def action_servicemc_end(self, cr, uid, ids, context=None):
        """ Writes servicemc order state to 'To be invoiced' if invoice method is
        After servicemc else state is set to 'Ready'.
        @return: True
        """
        for order in self.browse(cr, uid, ids, context=context):
            val = {}
            val['servicemced'] = True
            if (not order.invoiced and order.invoice_method=='after_servicemc'):
                val['state'] = '2binvoiced'
            elif (not order.invoiced and order.invoice_method=='b4servicemc'):
                val['state'] = 'ready'
            else:
                pass
            self.write(cr, uid, [order.id], val)
        return True

    def wkf_servicemc_done(self, cr, uid, ids, *args):
        self.action_servicemc_done(cr, uid, ids)
        return True

    def action_servicemc_done(self, cr, uid, ids, context=None):
        """ Creates stock move and picking for servicemc order.
        @return: Picking ids.
        """
        res = {}
        move_obj = self.pool.get('stock.move')
        wf_service = netsvc.LocalService("workflow")
        servicemc_line_obj = self.pool.get('mrp.servicemc.line')
        seq_obj = self.pool.get('ir.sequence')
        pick_obj = self.pool.get('stock.picking')
        for servicemc in self.browse(cr, uid, ids, context=context):
            for move in servicemc.operations:
                move_id = move_obj.create(cr, uid, {
                    'name': move.name,
                    'product_id': move.product_id.id,
                    'product_qty': move.product_uom_qty,
                    'product_uom': move.product_uom.id,
                    'partner_id': servicemc.address_id and servicemc.address_id.id or False,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'tracking_id': False,
                    'prodlot_id': move.prodlot_id and move.prodlot_id.id or False,
                    'state': 'assigned',
                })
                move_obj.action_done(cr, uid, [move_id], context=context)
                servicemc_line_obj.write(cr, uid, [move.id], {'move_id': move_id, 'state': 'done'}, context=context)
            if servicemc.deliver_bool:
                pick_name = seq_obj.get(cr, uid, 'stock.picking.out')
                picking = pick_obj.create(cr, uid, {
                    'name': pick_name,
                    'origin': servicemc.name,
                    'state': 'draft',
                    'move_type': 'one',
                    'partner_id': servicemc.address_id and servicemc.address_id.id or False,
                    'note': servicemc.internal_notes,
                    'invoice_state': 'none',
                    'type': 'out',
                })
                move_id = move_obj.create(cr, uid, {
                    'name': servicemc.name,
                    'picking_id': picking,
                    'product_id': servicemc.product_id.id,
                    'product_uom': servicemc.product_id.uom_id.id,
                    'prodlot_id': servicemc.prodlot_id and servicemc.prodlot_id.id or False,
                    'partner_id': servicemc.address_id and servicemc.address_id.id or False,
                    'location_id': servicemc.location_id.id,
                    'location_dest_id': servicemc.location_dest_id.id,
                    'tracking_id': False,
                    'state': 'assigned',
                })
                wf_service.trg_validate(uid, 'stock.picking', picking, 'button_confirm', cr)
                self.write(cr, uid, [servicemc.id], {'state': 'done', 'picking_id': picking})
                res[servicemc.id] = picking
            else:
                self.write(cr, uid, [servicemc.id], {'state': 'done'})
        return res

class actividades_lines(osv.osv):
    _name = 'actividades.lines'
    _description = 'tareas'
    _columns = {
        'facproducto': fields.many2one('product.product','Producto'),   
        'faccantidad': fields.float('Cantidad',help = 'Cantidad',required=True),        
        'facpreciounitario': fields.float('Precio unitario', help = 'Precio unitario',  required=True), 
        'facimpuestos': fields.many2many('account.tax', 'repair_operation_line_tax', 'repair_operation_line_id', 'tax_id', 'Impuesto'),
        'facafacturar':fields.boolean('A facturar'),
        'facsubtotal':fields.float('Subtotal'),
        'total': fields.float('Total')        
        }
   
actividades_lines()


class ProductChangeMixin(object):
    def product_id_change(self, cr, uid, ids, pricelist, product, uom=False,
                          product_uom_qty=0, partner_id=False, guarantee_limit=False):
        """ On change of product it sets product quantity, tax account, name,
        uom of product, unit price and price subtotal.
        @param pricelist: Pricelist of current record.
        @param product: Changed id of product.
        @param uom: UoM of current record.
        @param product_uom_qty: Quantity of current record.
        @param partner_id: Partner of current record.
        @param guarantee_limit: Guarantee limit of current record.
        @return: Dictionary of values and warning message.
        """
        result = {}
        warning = {}

        if not product_uom_qty:
            product_uom_qty = 1
        result['product_uom_qty'] = product_uom_qty

        if product:
            product_obj = self.pool.get('product.product').browse(cr, uid, product)
            if partner_id:
                partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
                result['tax_id'] = self.pool.get('account.fiscal.position').map_tax(cr, uid, partner.property_account_position, product_obj.taxes_id)

            result['name'] = product_obj.partner_ref
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id or False
            if not pricelist:
                warning = {
                    'title':'No Pricelist!',
                    'message':
                        'You have to select a pricelist in the servicemc form !\n'
                        'Please set one before choosing a product.'
                }
            else:
                price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                            product, product_uom_qty, partner_id, {'uom': uom,})[pricelist]

                if price is False:
                     warning = {
                        'title':'No valid pricelist line found !',
                        'message':
                            "Couldn't find a pricelist line matching this product and quantity.\n"
                            "You have to change either the product, the quantity or the pricelist."
                     }
                else:
                    result.update({'price_unit': price, 'price_subtotal': price*product_uom_qty})

        return {'value': result, 'warning': warning}


class mrp_servicemc_line(osv.osv, ProductChangeMixin):
    _name = 'mrp.servicemc.line'
    _description = 'servicemc Line'

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default: default = {}
        default.update( {'invoice_line_id': False, 'move_id': False, 'invoiced': False, 'state': 'draft'})
        return super(mrp_servicemc_line, self).copy_data(cr, uid, id, default, context)

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        cur_obj=self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.to_invoice and line.price_unit * line.product_uom_qty or 0
            cur = line.servicemc_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res

    _columns = {
        'name' : fields.char('Description',size=64,required=True),
        'servicemc_id': fields.many2one('mrp.servicemc', 'servicemc Order Reference',ondelete='cascade', select=True),
        'type': fields.selection([('add','Add'),('remove','Remove')],'Type', required=True),
        'to_invoice': fields.boolean('To Invoice'),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'invoiced': fields.boolean('Invoiced',readonly=True),
        'price_unit': fields.float('Unit Price', required=True, digits_compute= dp.get_precision('Product Price')),
        'price_subtotal': fields.function(_amount_line, string='Subtotal',digits_compute= dp.get_precision('Account')),
        'tax_id': fields.many2many('account.tax', 'servicemc_operation_line_tax', 'servicemc_operation_line_id', 'tax_id', 'Taxes'),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
        'prodlot_id': fields.many2one('stock.production.lot', 'Lot Number',domain="[('product_id','=',product_id)]"),
        'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line', readonly=True),
        'location_id': fields.many2one('stock.location', 'Source Location', required=True, select=True),
        'location_dest_id': fields.many2one('stock.location', 'Dest. Location', required=True, select=True),
        'move_id': fields.many2one('stock.move', 'Inventory Move', readonly=True),
        'state': fields.selection([
                    ('draft','Draft'),
                    ('confirmed','Confirmed'),
                    ('done','Done'),
                    ('cancel','Cancelled')], 'Status', required=True, readonly=True,
                    help=' * The \'Draft\' status is set automatically as draft when servicemc order in draft status. \
                        \n* The \'Confirmed\' status is set automatically as confirm when servicemc order in confirm status. \
                        \n* The \'Done\' status is set automatically when servicemc order is completed.\
                        \n* The \'Cancelled\' status is set automatically when user cancel servicemc order.'),
    }
    _defaults = {
     'state': lambda *a: 'draft',
     'product_uom_qty': lambda *a: 1,
    }

    def onchange_operation_type(self, cr, uid, ids, type, guarantee_limit, company_id=False, context=None):
        """ On change of operation type it sets source location, destination location
        and to invoice field.
        @param product: Changed operation type.
        @param guarantee_limit: Guarantee limit of current record.
        @return: Dictionary of values.
        """
        if not type:
            return {'value': {
                'location_id': False,
                'location_dest_id': False
                }}
        location_obj = self.pool.get('stock.location')
        warehouse_obj = self.pool.get('stock.warehouse')
        location_id = location_obj.search(cr, uid, [('usage','=','production')], context=context)
        location_id = location_id and location_id[0] or False

        if type == 'add':
            # TOCHECK: Find stock location for user's company warehouse or
            # servicemc order's company's warehouse (company_id field is added in fix of lp:831583)
            args = company_id and [('company_id', '=', company_id)] or []
            warehouse_ids = warehouse_obj.search(cr, uid, args, context=context)
            stock_id = False
            if warehouse_ids:
                stock_id = warehouse_obj.browse(cr, uid, warehouse_ids[0], context=context).lot_stock_id.id
            to_invoice = (guarantee_limit and datetime.strptime(guarantee_limit, '%Y-%m-%d') < datetime.now())

            return {'value': {
                'to_invoice': to_invoice,
                'location_id': stock_id,
                'location_dest_id': location_id
                }}
        scrap_location_ids = location_obj.search(cr, uid, [('scrap_location', '=', True)], context=context)

        return {'value': {
                'to_invoice': False,
                'location_id': location_id,
                'location_dest_id': scrap_location_ids and scrap_location_ids[0] or False,
                }}

mrp_servicemc_line()

class mrp_servicemc_fee(osv.osv, ProductChangeMixin):
    _name = 'mrp.servicemc.fee'
    _description = 'servicemc Fees Line'

    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default: default = {}
        default.update({'invoice_line_id': False, 'invoiced': False})
        return super(mrp_servicemc_fee, self).copy_data(cr, uid, id, default, context)

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        """ Calculates amount.
        @param field_name: Name of field.
        @param arg: Argument
        @return: Dictionary of values.
        """
        res = {}
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.to_invoice and line.price_unit * line.product_uom_qty or 0
            cur = line.servicemc_id.pricelist_id.currency_id
            res[line.id] = cur_obj.round(cr, uid, cur, res[line.id])
        return res

    _columns = {
        'servicemc_id': fields.many2one('mrp.servicemc', 'servicemc Order Reference', required=True, ondelete='cascade', select=True),
        'name': fields.char('Description', size=64, select=True,required=True),
        'product_id': fields.many2one('product.product', 'Product'),
        'product_uom_qty': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure'), required=True),
        'price_unit': fields.float('Unit Price', required=True),
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
        'price_subtotal': fields.function(_amount_line, string='Subtotal',digits_compute= dp.get_precision('Account')),
        'tax_id': fields.many2many('account.tax', 'servicemc_fee_line_tax', 'servicemc_fee_line_id', 'tax_id', 'Taxes'),
        'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line', readonly=True),
        'to_invoice': fields.boolean('To Invoice'),
        'invoiced': fields.boolean('Invoiced',readonly=True),
    }
    _defaults = {
        'to_invoice': lambda *a: True,
    }

mrp_servicemc_fee()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
