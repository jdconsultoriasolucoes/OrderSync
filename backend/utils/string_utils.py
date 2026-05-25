import re
from typing import Optional

def clean_client_name(name: Optional[str]) -> str:
    """
    Higieniza o nome do cliente de forma extremamente robusta, removendo qualquer
    documento numérico (CPF, CNPJ, RG, IE) do início, meio ou fim da string,
    enquanto preserva números legítimos de nomes comerciais (ex: RAÇÕES 43).
    """
    if not name:
        return "---"
    
    s = str(name).strip()
    
    # 1. Se a string contiver apenas dígitos e pontuações de documentos, ela é um documento puro.
    # Se não restar nenhum caractere alfabético, retorna "Não Cadastrado".
    if not re.search(r'[a-zA-ZáéíóúâêîôûãõçÁÉÍÓÚÂÊÎÔÛÃÕÇ]', s):
        return "Não Cadastrado"
        
    # 2. Remove CPFs e CNPJs jogados em qualquer parte (sequências de 11 a 14 dígitos com separadores opcionais)
    # Ex: 123.456.789-00 ou 12.345.678/0001-99 ou 12345678901 ou 12345678000199
    s = re.sub(r'\b\d{2,3}[\.\/]?\d{3}[\.\/]?\d{3}[\-\/]?\d{2,4}\b', '', s)
    
    # 3. Remove RGs comuns (sequências de 7 a 10 dígitos com ou sem pontos/traços)
    # Ex: 50.669.437 ou 50669437 ou 12.345.678-9
    s = re.sub(r'\b\d{1,2}\.?\d{3}\.?\d{3}\b', '', s)
    s = re.sub(r'\b\d{1,2}\.?\d{3}\.?\d{3}[\-\s]?[0-9xX]\b', '', s)
    
    # 4. Remove qualquer sequência inicial de números, traços, barras e espaços
    s = re.sub(r'^[\d\.\/\-\s]+', '', s)
    
    # 5. Remove qualquer sequência final de números, traços, barras e espaços
    s = re.sub(r'[\d\.\/\-\s]+$', '', s)
    
    # 6. Remove palavras indicadoras de documento soltas como "CPF:", "CNPJ:", "RG:", "IE:", "SSP"
    s = re.sub(r'\b(rg|cpf|cnpj|ie|ssp)\b[\s\.\:\-]*', '', s, flags=re.IGNORECASE)
    
    # Limpa hífens ou traços residuais no início ou fim
    s = re.sub(r'^\s*-\s*', '', s)
    s = re.sub(r'\s*-\s*$', '', s)
    
    # Se a string resultante for muito curta ou vazia, retorna "Não Cadastrado"
    if len(s.strip()) < 2:
        return "Não Cadastrado"
        
    return s.strip()
