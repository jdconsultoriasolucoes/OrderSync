import re

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find broken fragments that look like:
#     } else 
#     , e: {r:1, c:0} },
# ...
#             ws['!cols'].push({ wch: 15 }); // Peso e Valor
#         }
#     }

pattern = r'\} else\s*,\s*e:\s*\{r:1,\s*c:0\}\s*\},\s*\{\s*s:\s*\{r:0,\s*c:1\},\s*e:\s*\{r:1,\s*c:1\}\s*\},\s*\{\s*s:\s*\{r:0,\s*c:2\},\s*e:\s*\{r:1,\s*c:2\}\s*\},\s*\{\s*s:\s*\{r:0,\s*c:3\},\s*e:\s*\{r:1,\s*c:3\}\s*\}\s*\];\s*let\s*cIndex\s*=\s*4;\s*gerencial3Meses\.forEach\(m\s*=>\s*\{\s*ws\[\'!merges\'\]\.push\(\{ s: \{r:0, c:cIndex\}, e: \{r:0, c:cIndex\+1\} \}\);\s*cIndex\s*\+=\s*2;\s*\}\);\s*\}\s*,\s*\{\s*wch:\s*40\s*\},\s*\{\s*wch:\s*15\s*\},\s*\{\s*wch:\s*15\s*\}\s*\];\s*for\s*\(let\s*i\s*=\s*0;\s*i\s*<\s*gerencial3Meses\.length\s*\*\s*2;\s*i\+\+\)\s*\{\s*ws\[\'!cols\'\]\.push\(\{ wch: 15 \}\);\s*// Peso e Valor\s*\}\s*\}'

new_content = re.sub(pattern, '}', content, flags=re.DOTALL)

# Let's also make sure we fix the one that just had } instead of } else
pattern2 = r',\s*e:\s*\{r:1,\s*c:0\}\s*\},\s*\{\s*s:\s*\{r:0,\s*c:1\},\s*e:\s*\{r:1,\s*c:1\}\s*\},\s*\{\s*s:\s*\{r:0,\s*c:2\},\s*e:\s*\{r:1,\s*c:2\}\s*\},\s*\{\s*s:\s*\{r:0,\s*c:3\},\s*e:\s*\{r:1,\s*c:3\}\s*\}\s*\];\s*let\s*cIndex\s*=\s*4;\s*gerencial3Meses\.forEach\(m\s*=>\s*\{\s*ws\[\'!merges\'\]\.push\(\{ s: \{r:0, c:cIndex\}, e: \{r:0, c:cIndex\+1\} \}\);\s*cIndex\s*\+=\s*2;\s*\}\);\s*\}\s*,\s*\{\s*wch:\s*40\s*\},\s*\{\s*wch:\s*15\s*\},\s*\{\s*wch:\s*15\s*\}\s*\];\s*for\s*\(let\s*i\s*=\s*0;\s*i\s*<\s*gerencial3Meses\.length\s*\*\s*2;\s*i\+\+\)\s*\{\s*ws\[\'!cols\'\]\.push\(\{ wch: 15 \}\);\s*// Peso e Valor\s*\}\s*\}'
new_content = re.sub(pattern2, '', new_content, flags=re.DOTALL)

with open('e:/OrderSync/frontend/public/relatorios/relatorios_vendas.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Cleaned up broken JS")
