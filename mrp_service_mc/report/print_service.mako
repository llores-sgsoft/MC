<html>
    <head>
        <style type="text/css">
            ${css}
        </style>
    </head>
    <body>
		%for o in objects :
            <% setLang(user.lang) %>          
            <div class="contenedor_principal">
                <div class="contenedor_contenido">  
                <div class="act_as_table">
                        <div class="act_as_row">
                            <div class="act_as_cell" style="width:20%;">
                                <div style="position: relative;">
                                    <div style="position: absolute; top: 10px; bottom: 0px;">
                                        ${helper.embed_image('jpeg',str(o.company_id.logo),130)}                         
                                    </div>                               
                                </div>
                            </div>
                            <div class="act_as_cell" style="width:45%">
                                <div class="act_as_table">
                                    <div class="act_as_row" style="text-align:left; font-weight:bold;">
                                        <div class="act_as_cell" style="padding-top:0px; font-size:15px;">
                                            ${o.partner_id.name}
                                        </div>
                                    </div>
                                    
                                </div>
                            </div>
                            <div class="act_as_cell" style="border:1px solid black;">
                                <div class="act_as_table">
                                    <div class="act_as_row">
                                        <div class="act_as_cell" style="color:red; text-align:center; font-size:18px;">
                                            <b>ORDEN DE SERVICIO </b>
                                        </div>
                                    </div> 
                                    <div class="act_as_row">
                                        <div class="act_as_cell" style="text-align:center;">                                            
                                            ${o.fecha_alta}
                                        </div>
                                    </div> 
                                    <div class="act_as_row">
                                        <div class="act_as_cell" style="text-align:center;">
                                            <b>${o.guarantee_limit}</b><br> <br>                                            
                                        </div>
                                    </div>                                                                      
                                </div>
                            </div>                             
                        </div>
                    </div>  
                    </br>
                    
                    <div class="act_as_table">
                        <div class="act_as_row">
                            <div class="act_as_cell" style="width:20%;">
                            	<div>
						            ${o.name} <br>
						 			${o.product_id.name}	<br>           
						            ${o.partner_id.name}<br>
						            ${o.modelo_id.name}<br>
					            </div>
                            </div>
                        </div>
                    </div>
                                    
                    <div class="act_as_table">
                        <div class="act_as_row">
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; color:#4B0082; text-align:center; padding:5px;">
                                <b>${_("TIPO")}</b>
                            </div>
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; color:#4B0082; text-align:center; padding:5px; word-wrap: break-word;">
                                <b>${_("PRODUCTO")}</b>
                            </div>
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; color:#4B0082;text-align:center; padding:5px;">
                                <b>${_("X de Y")}</b>
                            </div>
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; color:#4B0082; text-align:center; padding:5px;">
                                <b>${_("ORIGEN")}</b>
                            </div>
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; color:#4B0082; text-align:center; padding:5px;">
                                <b>${_("ESTADO")}</b>
                            </div>
                        </div>
                        %for l in o.operations:
                        <div class="act_as_row">
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; text-align:center; padding:5px;">
                                ${l.type or 'No identificado'} 
                            </div>
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; text-align:center; padding:5px;">
                                ${l.product_id.name or 'No identificado' }
                            </div>
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; text-align:center; padding:5px;">
                                ${ l.name or 'No identificado'}
                            </div>
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; text-align:center; padding:5px;">
                                ${ l.prodlot_id.name or 'No identificado'}
                            </div>
                            <div class="act_as_cell" style="border:1px solid #D3D3D3; text-align:center; padding:5px;">
                               %if l.name == 'serviciomc1': 
                                 	okkkkkk
                                % else: 
                                	Nooooooo                                	
                                %endif
                            </div>
                        </div>
                        %endfor
                   </div>   
            </div>
        %endfor
    </body> 
</html>    