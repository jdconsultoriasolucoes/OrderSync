
import re
from datetime import datetime, date

# CPF e CNPJ (mantidos do anterior)
def validar_cpf_valido(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)  # Remove tudo que não for número

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    # Cálculo de verificação
    soma1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = ((soma1 * 10) % 11) % 10
    soma2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = ((soma2 * 10) % 11) % 10

    return d1 == int(cpf[9]) and d2 == int(cpf[10])

def validar_cnpj_valido(cnpj: str) -> bool:
    cnpj = re.sub(r"\D", "", cnpj)  # Remove pontos, barras e traços

    if len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    def calc_digito(cnpj, peso):
        soma = sum(int(cnpj[i]) * peso[i] for i in range(len(peso)))
        resto = soma % 11
        return '0' if resto < 2 else str(11 - resto)

    peso1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    peso2 = [6] + peso1

    digito1 = calc_digito(cnpj, peso1)
    digito2 = calc_digito(cnpj + digito1, peso2)

    return cnpj[-2:] == digito1 + digito2

# Email
def validar_email(email: str) -> bool:
    regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(regex, email) is not None

# Telefone/Celular
def validar_telefone(telefone: str) -> bool:
    telefone = re.sub(r'\D', '', telefone)
    return re.fullmatch(r"\d{10,11}", telefone) is not None

# Datas
def validar_data_nascimento(data_str: str) -> bool:
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        return data < date.today()
    except:
        return False

def validar_data_vencimento(data_str: str) -> bool:
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        return data >= date.today()
    except:
        return False

def validar_emissao(data_str: str) -> bool:
    try:
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        return data <= date.today()
    except:
        return False

# Valores
def validar_valor_positivo(valor: float) -> bool:
    return valor >= 0

# Consumo coerente
def validar_consumo_coerente(consumo_diario: float, consumo_mensal: float, dias_mes: int = 30) -> bool:
    if consumo_diario is None or consumo_mensal is None:
        return True
    estimado = consumo_diario * dias_mes
    return abs(estimado - consumo_mensal) <= (0.1 * estimado)  # 10% de tolerância

# Documento conforme tipo de pessoa
def validar_documento_por_tipo_pessoa(tipo: str, cpf: str, cnpj: str) -> bool:
    tipo = tipo.lower()
    if tipo == "pessoa física" and not cpf:
        return False
    if tipo == "pessoa jurídica" and not cnpj:
        return False
    return True
