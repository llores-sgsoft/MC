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


{
    'name': 'Ordenes de Servicio',
    'version': '2.0',
    'category': 'Manufacturing',
    'description': """
The aim is to have a complete module to manage all products servicemcs.
====================================================================

The following topics should be covered by this module:
------------------------------------------------------
    * Add/remove products in the reparation
    * Impact for stocks
    * Invoicing (products and/or services)
    * Warranty concept
    * servicemc quotation report
    * Notes for the technician and for the final customer
""",
    'author': 'Grupo de desarrollo MC',
    'images': ['images/servicemc_order.jpeg'],
    'depends': ['mrp', 'sale', 'account','hr','fleet'],
    'data': [
        'security/ir.model.access.csv',
        'security/mrp_servicemc_security.xml',
        'mrp_servicemc_data.xml',
        'mrp_servicemc_sequence.xml',
        'wizard/mrp_servicemc_cancel_view.xml',
        'wizard/mrp_servicemc_make_invoice_view.xml',
        'mrp_servicemc_view.xml',
        'mrp_servicemc_workflow.xml',
        'mrp_servicemc_report.xml',
        'report/print_service.xml',
    ],
    'demo': ['mrp_servicemc_demo.yml'],
    'test': ['test/test_mrp_servicemc_noneinv.yml',
             'test/test_mrp_servicemc_b4inv.yml',
             'test/test_mrp_servicemc_afterinv.yml',
             'test/test_mrp_servicemc_cancel.yml',
             'test/mrp_servicemc_report.yml',
             'test/test_mrp_servicemc_fee.yml',
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
