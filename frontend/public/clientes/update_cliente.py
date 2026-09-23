import re

with open('e:/OrderSync/frontend/public/clientes/cliente.html', 'r', encoding='utf-8') as f:
    content = f.read()

# The block to remove:
#             <div class="form-group">
#               <label for="tipo_entrega_faturamento">Tipo de Entrega:</label>
#               <select id="tipo_entrega_faturamento" name="tipo_entrega_faturamento">
#                 <option value="">Selecione</option>
#                 <option value="Entrega">Entrega</option>
#                 <option value="Retira">Retira</option>
#                 <option value="Ambos">Ambos</option>
#               </select>
#             </div>

block_regex = r'\s*<div class="form-group">\s*<label for="tipo_entrega_faturamento">Tipo de Entrega:</label>\s*<select id="tipo_entrega_faturamento" name="tipo_entrega_faturamento">\s*<option value="">Selecione</option>\s*<option value="Entrega">Entrega</option>\s*<option value="Retira">Retira</option>\s*<option value="Ambos">Ambos</option>\s*</select>\s*</div>'
content = re.sub(block_regex, '', content)

# Now, insert it into "Endereço de Entrega" section.
# We can find:
#             <div>
#               <label for="observacao_motorista_EnderecoEntrega">Observação para o Motorista:</label>
#               <input type="text" id="observacao_motorista_EnderecoEntrega" name="observacao_motorista_EnderecoEntrega" />
#             </div>
# And add it after this div.

new_block = """
            <div class="form-group">
              <label for="tipo_entrega_EnderecoEntrega">Tipo de Entrega:</label>
              <select id="tipo_entrega_EnderecoEntrega" name="tipo_entrega_EnderecoEntrega">
                <option value="">Selecione</option>
                <option value="Entrega">Entrega</option>
                <option value="Retira">Retira</option>
                <option value="Ambos">Ambos</option>
              </select>
            </div>
"""

insert_target = r'(<div>\s*<label for="observacao_motorista_EnderecoEntrega">Observação para o Motorista:</label>\s*<input type="text" id="observacao_motorista_EnderecoEntrega" name="observacao_motorista_EnderecoEntrega" />\s*</div>)'
content = re.sub(insert_target, r'\1' + new_block, content)


# Now fix JS parsing logic:
# 1. Remove from faturamento
content = content.replace('tipo_entrega_faturamento: document.getElementById("tipo_entrega_faturamento")?.value || ""', '')
# This leaves an empty line or a trailing comma. It's inside a dict.
# Actually, the original is:
#               email_danfe_faturamento: document.getElementById("email_danfe_faturamento")?.value || "",
#               tipo_entrega_faturamento: document.getElementById("tipo_entrega_faturamento")?.value || ""

content = content.replace(',\n              tipo_entrega_faturamento: document.getElementById("tipo_entrega_faturamento")?.value || ""\n            },', '\n            },')

# 2. Add to entrega
# original:
#               observacao_motorista_EnderecoEntrega: document.getElementById("observacao_motorista_EnderecoEntrega")?.value || ""
#             },
content = content.replace('observacao_motorista_EnderecoEntrega: document.getElementById("observacao_motorista_EnderecoEntrega")?.value || ""\n            },', 'observacao_motorista_EnderecoEntrega: document.getElementById("observacao_motorista_EnderecoEntrega")?.value || "",\n              tipo_entrega_EnderecoEntrega: document.getElementById("tipo_entrega_EnderecoEntrega")?.value || ""\n            },')

# 3. Fix JS load logic (setVal)
content = content.replace('setVal("tipo_entrega_faturamento", ef.tipo_entrega_faturamento || "");', '')

# add under entrega
content = content.replace('setVal("observacao_motorista_EnderecoEntrega", ee.observacao_motorista_EnderecoEntrega || "");', 'setVal("observacao_motorista_EnderecoEntrega", ee.observacao_motorista_EnderecoEntrega || "");\n          setVal("tipo_entrega_EnderecoEntrega", ee.tipo_entrega_EnderecoEntrega || "");')


with open('e:/OrderSync/frontend/public/clientes/cliente.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated cliente.html")
