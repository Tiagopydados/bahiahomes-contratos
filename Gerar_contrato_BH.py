# -*- coding: utf-8 -*-

import json
import math
import os
import re
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

import streamlit as st
from docxtpl import DocxTemplate
from num2words import num2words
from deep_translator import GoogleTranslator


# =========================================================
# CAMINHO DO ARQUIVO MODELO
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVOS_DIR = os.path.join(BASE_DIR, "Arquivos_necessarios")
ARQUIVO_MODELO = os.path.join(ARQUIVOS_DIR, "Contrato_Padrao_Bahia_Homes.docx")
ARQUIVO_LOGO = os.path.join(ARQUIVOS_DIR, "Logo_BH_vetorizada.png")
ARQUIVO_MODELO_BILINGUE = os.path.join(ARQUIVOS_DIR, "Contrato_Padrao_Bahia_Homes_BILINGUE.docx")
ARQUIVO_MODELO_BILINGUE_ES = os.path.join(ARQUIVOS_DIR, "Contrato_Padrao_Bahia_Homes_BILINGUE_ES.docx")

CONTAS_CORRETORA = {
    "Banco Itaú": """ERIKA DE OLIVEIRA PLÁ PELEGRIN - ME
Banco Itaú - Ag. 4931 – C/c 99460-4
CNPJ: 29.901.518/0001-88""",

    "Banco Inter": """ERIKA DE OLIVEIRA PLÁ PELEGRIN
Banco Inter - Ag. 0001 – C/c 29998969-0
CNPJ: 29.901.518/0001-88
PIX: 29.901.518/0001-88"""
}


# =========================================================
# UTILIDADES
# =========================================================
def moeda_para_decimal(valor_str: str) -> Decimal:
    valor_str = str(valor_str).strip().replace("R$", "").replace(" ", "")
    valor_str = valor_str.replace(".", "").replace(",", ".")
    return Decimal(valor_str).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def formatar_moeda(valor: Decimal) -> str:
    valor = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    s = f"{valor:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def valor_por_extenso(valor: Decimal) -> str:
    valor = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    inteiro = int(valor)
    centavos = int((valor - inteiro) * 100)

    if centavos == 0:
        return num2words(inteiro, lang="pt_BR") + " reais"

    return (
        num2words(inteiro, lang="pt_BR")
        + " reais e "
        + num2words(centavos, lang="pt_BR")
        + " centavos"
    )


def inteiro_por_extenso(numero: int) -> str:
    return num2words(int(numero), lang="pt_BR")


def data_obj_para_extenso(data) -> str:
    meses = {
        1: "janeiro",
        2: "fevereiro",
        3: "março",
        4: "abril",
        5: "maio",
        6: "junho",
        7: "julho",
        8: "agosto",
        9: "setembro",
        10: "outubro",
        11: "novembro",
        12: "dezembro",
    }
    return f"{data.day:02d} de {meses[data.month]} de {data.year}"


def str_para_data(data_str: str):
    return datetime.strptime(data_str.strip(), "%d/%m/%Y").date()


def str_para_int(valor: str, nome_campo: str) -> int:
    valor = str(valor).strip()
    if not valor:
        raise ValueError(f'O campo "{nome_campo}" está vazio.')
    return int(valor)


def calcular_noites(checkin, checkout) -> int:
    diferenca = (checkout - checkin).days
    if diferenca <= 0:
        raise ValueError("A data de checkout deve ser posterior à data de check-in.")
    return diferenca


def montar_prazo_locacao(noites: int, checkin, checkout) -> str:
    noites_extenso = inteiro_por_extenso(noites)
    checkin_ext = data_obj_para_extenso(checkin)
    checkout_ext = data_obj_para_extenso(checkout)
    return (
        f"{noites} ({noites_extenso}) noites, iniciando-se em {checkin_ext} às 12:00 "
        f"e finalizando em {checkout_ext} às 12:00"
    )


def nome_arquivo_seguro(nome: str) -> str:
    nome = re.sub(r'[<>:"/\\|?*]', "", nome).strip()
    return nome or "Contrato_Preenchido"


def metade_valor(valor: Decimal) -> Decimal:
    return (Decimal(valor) / Decimal("2")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# =========================================================
# BLOCOS PF / PJ
# =========================================================
def gerar_bloco_pf(nome, nacionalidade, estado_civil, profissao, cpf, rg, endereco):
    return (
        f"{nome}, {nacionalidade}, {estado_civil}, {profissao}, "
        f"inscrito no CPF/MF sob nº {cpf}, portador da cédula de identidade R.G. nº {rg}, "
        f"residente e domiciliado na {endereco};"
    )


def gerar_bloco_pj(
    nome_empresa, cnpj, endereco_empresa,
    nome_rep, nacionalidade_rep, estado_civil_rep, profissao_rep,
    cpf_rep, rg_rep, endereco_rep
):
    return (
        f"{nome_empresa}, inscrita no CNPJ: {cnpj}, com sede na {endereco_empresa}, "
        f"neste ato representada por {nome_rep}, {nacionalidade_rep}, {estado_civil_rep}, "
        f"{profissao_rep}, inscrito no CPF/MF sob nº {cpf_rep}, portador da cédula de identidade "
        f"R.G. nº {rg_rep}, residente e domiciliado na {endereco_rep};"
    )


def gerar_resumo_pf(rotulo, nome, cpf):
    return f"{rotulo}: {nome}\nCPF: {cpf}"


def gerar_resumo_pj(rotulo, nome_empresa, cnpj, nome_rep, cpf_rep):
    return f"{rotulo}: {nome_empresa}\nCNPJ: {cnpj}\nREPRESENTANTE: {nome_rep}\nCPF: {cpf_rep}"


# =========================================================
# CÁLCULOS E CONTEXTO
# =========================================================
def calcular_contexto(dados: dict) -> dict:
    checkin = dados["data_checkin"]
    checkout = dados["data_checkout"]

    noites_numero = calcular_noites(checkin, checkout)
    noites_extenso = inteiro_por_extenso(noites_numero)
    prazo_locacao = montar_prazo_locacao(noites_numero, checkin, checkout)

    data_momento_b = checkin - timedelta(days=30)
    data_momento_b_extenso = data_obj_para_extenso(data_momento_b)

    valor_hospedagem = moeda_para_decimal(dados["valor_hospedagem"])
    valor_caucao = moeda_para_decimal(dados["valor_caucao"])

    valor_proprietario = (valor_hospedagem * Decimal("0.85")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    valor_imobiliaria = (valor_hospedagem * Decimal("0.15")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    valor_corretor = (valor_imobiliaria * Decimal("0.22")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    if dados["tem_taxa_servico"]:
        valor_staff = (valor_hospedagem * Decimal("0.10")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    else:
        valor_staff = Decimal("0.00")

    valor_diaria = (valor_hospedagem / Decimal(noites_numero)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    valor_multa = (valor_diaria * Decimal("4")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # Ocupação máxima acrescida de 50% (ex.: 10 pessoas → limite de 15)
    ocupacao_acrescida = math.ceil(dados["ocupacao_maxima"] * 1.5)
    ocupacao_acrescida_extenso = inteiro_por_extenso(ocupacao_acrescida)

    metade_proprietario = metade_valor(valor_proprietario)
    metade_staff = metade_valor(valor_staff)

    valor_momentoA_proprietario = (metade_proprietario + metade_staff).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    valor_momentoB_proprietario = (metade_proprietario + metade_staff).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    valor_momentoA_bahia = metade_valor(valor_imobiliaria)
    valor_momentoB_bahia = metade_valor(valor_imobiliaria)

    valor_momentoA_corretor = metade_valor(valor_corretor)
    valor_momentoB_corretor = metade_valor(valor_corretor)

    bloco_locador, resumo_locador = resolver_parte(dados, "locador")
    bloco_locatario, resumo_locatario = resolver_parte(dados, "locatario")

    contexto = {
        "bloco_locador": bloco_locador,
        "bloco_locatario": bloco_locatario,
        "resumo_locador": resumo_locador,
        "resumo_locatario": resumo_locatario,

        "nome_imovel": dados["nome_imovel"],
        "link_imovel": dados["link_imovel"],
        "cidade_imovel": dados["cidade_imovel"],

        "numero_suites": str(dados["numero_suites"]),
        "numero_suites_extenso": inteiro_por_extenso(dados["numero_suites"]),
        "descricao_suites": dados["descricao_suites"],

        "ocupacao_maxima": str(dados["ocupacao_maxima"]),
        "ocupacao_maxima_extenso": inteiro_por_extenso(dados["ocupacao_maxima"]),

        "quantidade_pessoas": str(dados["quantidade_pessoas"]),
        "quantidade_pessoas_extenso": inteiro_por_extenso(dados["quantidade_pessoas"]),

        "quantidade_staff": str(dados["quantidade_staff"]),
        "quantidade_staff_extenso": inteiro_por_extenso(dados["quantidade_staff"]),
        "descricao_staff": dados["descricao_staff"],

        "prazo_locacao": prazo_locacao,
        "noites_numero": str(noites_numero),
        "noites_extenso": noites_extenso,
        "data_momento_b_extenso": data_momento_b_extenso,

        "valor_proprietario": formatar_moeda(valor_proprietario),
        "valor_proprietario_extenso": valor_por_extenso(valor_proprietario),

        "valor_imobiliaria": formatar_moeda(valor_imobiliaria),
        "valor_imobiliaria_extenso": valor_por_extenso(valor_imobiliaria),

        "valor_corretor": formatar_moeda(valor_corretor),
        "valor_corretor_extenso": valor_por_extenso(valor_corretor),

        "valor_staff": formatar_moeda(valor_staff),
        "valor_staff_extenso": valor_por_extenso(valor_staff),

        "ocupacao_acrescida": str(ocupacao_acrescida),
        "ocupacao_acrescida_extenso": ocupacao_acrescida_extenso,

        "valor_multa": formatar_moeda(valor_multa),
        "valor_multa_extenso": valor_por_extenso(valor_multa),

        "valor_caucao": formatar_moeda(valor_caucao),
        "valor_caucao_extenso": valor_por_extenso(valor_caucao),

        "banco_locador": dados["banco_locador"],
        "banco_corretora": dados["banco_corretora"],

        "valor_momentoA_proprietario": formatar_moeda(valor_momentoA_proprietario),
        "valor_momentoA_proprietario_extenso": valor_por_extenso(valor_momentoA_proprietario),

        "valor_momentoB_proprietario": formatar_moeda(valor_momentoB_proprietario),
        "valor_momentoB_proprietario_extenso": valor_por_extenso(valor_momentoB_proprietario),

        "valor_momentoA_bahia": formatar_moeda(valor_momentoA_bahia),
        "valor_momentoA_bahia_extenso": valor_por_extenso(valor_momentoA_bahia),

        "valor_momentoB_bahia": formatar_moeda(valor_momentoB_bahia),
        "valor_momentoB_bahia_extenso": valor_por_extenso(valor_momentoB_bahia),

        "valor_momentoA_corretor": formatar_moeda(valor_momentoA_corretor),
        "valor_momentoA_corretor_extenso": valor_por_extenso(valor_momentoA_corretor),

        "valor_momentoB_corretor": formatar_moeda(valor_momentoB_corretor),
        "valor_momentoB_corretor_extenso": valor_por_extenso(valor_momentoB_corretor),
    }

    resumo = {
        "valor_proprietario": valor_proprietario,
        "valor_imobiliaria": valor_imobiliaria,
        "valor_corretor": valor_corretor,
        "valor_staff": valor_staff,
        "valor_diaria": valor_diaria,
        "valor_multa": valor_multa,
        "valor_momentoA_proprietario": valor_momentoA_proprietario,
        "valor_momentoB_proprietario": valor_momentoB_proprietario,
        "valor_momentoA_bahia": valor_momentoA_bahia,
        "valor_momentoB_bahia": valor_momentoB_bahia,
        "valor_momentoA_corretor": valor_momentoA_corretor,
        "valor_momentoB_corretor": valor_momentoB_corretor,
        "data_momento_b_extenso": data_momento_b_extenso,
        "noites_numero": noites_numero,
    }

    return {"contexto": contexto, "resumo": resumo}


def resolver_parte(dados: dict, papel: str) -> tuple[str, str]:
    """Gera bloco contratual e resumo para locador ou locatário.

    Args:
        dados: Dicionário com todos os campos do formulário.
        papel: "locador" ou "locatario".

    Returns:
        Tupla (bloco_textual, resumo_textual).
    """
    rotulo = "LOCADOR" if papel == "locador" else "LOCATÁRIO"
    p = papel  # alias curto para montar as chaves

    if dados[f"tipo_{p}"] == "Pessoa Física":
        bloco = gerar_bloco_pf(
            dados[f"nome_{p}_pf"],
            dados[f"nacionalidade_{p}_pf"],
            dados[f"estado_civil_{p}_pf"],
            dados[f"profissao_{p}_pf"],
            dados[f"cpf_{p}_pf"],
            dados[f"rg_{p}_pf"],
            dados[f"endereco_{p}_pf"],
        )
        resumo = gerar_resumo_pf(rotulo, dados[f"nome_{p}_pf"], dados[f"cpf_{p}_pf"])
    else:
        bloco = gerar_bloco_pj(
            dados[f"nome_empresa_{p}"],
            dados[f"cnpj_empresa_{p}"],
            dados[f"endereco_empresa_{p}"],
            dados[f"nome_representante_{p}"],
            dados[f"nacionalidade_representante_{p}"],
            dados[f"estado_civil_representante_{p}"],
            dados[f"profissao_representante_{p}"],
            dados[f"cpf_representante_{p}"],
            dados[f"rg_representante_{p}"],
            dados[f"endereco_representante_{p}"],
        )
        resumo = gerar_resumo_pj(
            rotulo,
            dados[f"nome_empresa_{p}"],
            dados[f"cnpj_empresa_{p}"],
            dados[f"nome_representante_{p}"],
            dados[f"cpf_representante_{p}"],
        )

    return bloco, resumo


def traduzir_contexto(contexto: dict, idioma: str = "en") -> dict:
    """Retorna uma cópia do contexto com valores textuais traduzidos para o idioma indicado."""
    translator = GoogleTranslator(source="pt", target=idioma)
    campos_traduzir = {
        "bloco_locador", "bloco_locatario", "resumo_locador", "resumo_locatario",
        "descricao_suites", "descricao_staff", "prazo_locacao",
        "noites_extenso", "data_momento_b_extenso",
        "valor_proprietario_extenso", "valor_imobiliaria_extenso",
        "valor_corretor_extenso", "valor_staff_extenso", "valor_multa_extenso",
        "valor_caucao_extenso", "ocupacao_acrescida_extenso", "ocupacao_maxima_extenso",
        "quantidade_pessoas_extenso", "quantidade_staff_extenso", "numero_suites_extenso",
        "valor_momentoA_proprietario_extenso", "valor_momentoA_bahia_extenso",
        "valor_momentoA_corretor_extenso", "valor_momentoB_proprietario_extenso",
        "valor_momentoB_bahia_extenso", "valor_momentoB_corretor_extenso",
    }
    ctx_en = {}
    for k, v in contexto.items():
        if k in campos_traduzir and isinstance(v, str) and v.strip():
            try:
                ctx_en[k] = translator.translate(v)
            except Exception:
                ctx_en[k] = v
        else:
            ctx_en[k] = v
    return ctx_en


def gerar_docx(contexto: dict, idioma: str = "pt") -> BytesIO:
    """Renderiza o template e retorna o arquivo em memória (sem salvar no disco)."""
    if idioma == "en":
        arquivo = ARQUIVO_MODELO_BILINGUE
    elif idioma == "es":
        arquivo = ARQUIVO_MODELO_BILINGUE_ES
    else:
        arquivo = ARQUIVO_MODELO

    if not os.path.exists(arquivo):
        raise FileNotFoundError(f"Arquivo modelo não encontrado: {arquivo}")

    doc = DocxTemplate(arquivo)
    doc.render(contexto)

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf


# =========================================================
# FORMULÁRIO — RENDERIZAÇÃO DE PARTE (PF / PJ)
# =========================================================
def renderizar_parte(rotulo: str, p: str, tipo: str) -> dict:
    """Renderiza os campos de uma parte contratual (locador ou locatário).

    Args:
        rotulo: Texto exibido no subheader (ex.: "Locador").
        p: Prefixo das chaves no session_state (ex.: "locador" ou "locatario").
        tipo: "Pessoa Física" ou "Pessoa Jurídica", definido fora do form.

    Returns:
        Dicionário com todos os valores preenchidos pelo usuário.
    """
    if tipo == "Pessoa Física":
        c1, c2 = st.columns(2)
        with c1:
            nome_pf           = st.text_input(f"Nome do {rotulo.lower()}", key=f"nome_{p}_pf")
            nacionalidade_pf  = st.text_input(f"Nacionalidade do {rotulo.lower()}", key=f"nacionalidade_{p}_pf")
            estado_civil_pf   = st.text_input(f"Estado civil do {rotulo.lower()}", key=f"estado_civil_{p}_pf")
            profissao_pf      = st.text_input(f"Profissão do {rotulo.lower()}", key=f"profissao_{p}_pf")
        with c2:
            cpf_pf      = st.text_input(f"CPF do {rotulo.lower()}", key=f"cpf_{p}_pf")
            rg_pf       = st.text_input(f"RG do {rotulo.lower()}", key=f"rg_{p}_pf")
            endereco_pf = st.text_area(f"Endereço do {rotulo.lower()}", height=100, key=f"endereco_{p}_pf")

        return {
            f"tipo_{p}": tipo,
            f"nome_{p}_pf": nome_pf,
            f"nacionalidade_{p}_pf": nacionalidade_pf,
            f"estado_civil_{p}_pf": estado_civil_pf,
            f"profissao_{p}_pf": profissao_pf,
            f"cpf_{p}_pf": cpf_pf,
            f"rg_{p}_pf": rg_pf,
            f"endereco_{p}_pf": endereco_pf,
            f"nome_empresa_{p}": "", f"cnpj_empresa_{p}": "", f"endereco_empresa_{p}": "",
            f"nome_representante_{p}": "", f"nacionalidade_representante_{p}": "",
            f"estado_civil_representante_{p}": "", f"profissao_representante_{p}": "",
            f"cpf_representante_{p}": "", f"rg_representante_{p}": "", f"endereco_representante_{p}": "",
        }
    else:
        st.markdown(f"**Empresa do {rotulo.lower()}**")
        c1, c2 = st.columns(2)
        with c1:
            nome_empresa    = st.text_input(f"Nome da empresa do {rotulo.lower()}", key=f"nome_empresa_{p}")
            cnpj_empresa    = st.text_input(f"CNPJ da empresa do {rotulo.lower()}", key=f"cnpj_empresa_{p}")
        with c2:
            endereco_empresa = st.text_area(f"Endereço da empresa do {rotulo.lower()}", height=100, key=f"endereco_empresa_{p}")

        st.markdown(f"**Representante da empresa {rotulo.lower()}a**")
        c3, c4 = st.columns(2)
        with c3:
            nome_rep          = st.text_input(f"Nome do representante do {rotulo.lower()}", key=f"nome_representante_{p}")
            nacionalidade_rep = st.text_input("Nacionalidade do representante", key=f"nacionalidade_representante_{p}")
            estado_civil_rep  = st.text_input("Estado civil do representante", key=f"estado_civil_representante_{p}")
            profissao_rep     = st.text_input("Profissão do representante", key=f"profissao_representante_{p}")
        with c4:
            cpf_rep      = st.text_input(f"CPF do representante do {rotulo.lower()}", key=f"cpf_representante_{p}")
            rg_rep       = st.text_input(f"RG do representante do {rotulo.lower()}", key=f"rg_representante_{p}")
            endereco_rep = st.text_area(f"Endereço do representante do {rotulo.lower()}", height=100, key=f"endereco_representante_{p}")

        return {
            f"tipo_{p}": tipo,
            f"nome_{p}_pf": "", f"nacionalidade_{p}_pf": "", f"estado_civil_{p}_pf": "",
            f"profissao_{p}_pf": "", f"cpf_{p}_pf": "", f"rg_{p}_pf": "", f"endereco_{p}_pf": "",
            f"nome_empresa_{p}": nome_empresa,
            f"cnpj_empresa_{p}": cnpj_empresa,
            f"endereco_empresa_{p}": endereco_empresa,
            f"nome_representante_{p}": nome_rep,
            f"nacionalidade_representante_{p}": nacionalidade_rep,
            f"estado_civil_representante_{p}": estado_civil_rep,
            f"profissao_representante_{p}": profissao_rep,
            f"cpf_representante_{p}": cpf_rep,
            f"rg_representante_{p}": rg_rep,
            f"endereco_representante_{p}": endereco_rep,
        }


# =========================================================
# INTERFACE
# =========================================================
_favicon_path = ARQUIVO_LOGO
st.set_page_config(
    page_title="Contrato Bahia Homes",
    page_icon=_favicon_path if os.path.exists(_favicon_path) else "🏠",
    layout="wide",
)

st.title("🏠 Gerador de Contrato Bahia Homes")
st.caption("Preencha os dados, confira os cálculos e gere o contrato em Word.")

with st.sidebar:
    if os.path.exists(ARQUIVO_LOGO):
        with open(ARQUIVO_LOGO, "rb") as _f:
            st.image(_f.read(), use_container_width=True)

# Abas de preenchimento das partes (fora do form para reatividade imediata)
aba_locador, aba_locatario = st.tabs(["👤 Locador", "👤 Locatário"])

with aba_locador:
    tipo_locador = st.selectbox(
        "Tipo do locador",
        ["Pessoa Física", "Pessoa Jurídica"],
        index=0,
        key="tipo_locador",
    )
    dados_locador = renderizar_parte("Locador", "locador", tipo_locador)

with aba_locatario:
    arquivo_json = st.file_uploader(
        "Importar dados do locatário (.json)",
        type=["json"],
        key="arquivo_json",
        help="Arquivo gerado pelo app Formulário do Locatário",
    )
    if arquivo_json is not None:
        try:
            dados_json = json.loads(arquivo_json.read().decode("utf-8"))
            for chave, valor in dados_json.items():
                if chave in ["nome_locatario_pf", "nacionalidade_locatario_pf",
                             "estado_civil_locatario_pf", "profissao_locatario_pf",
                             "cpf_locatario_pf", "rg_locatario_pf", "endereco_locatario_pf"]:
                    st.session_state[chave] = str(valor)
            if "quantidade_pessoas" in dados_json:
                st.session_state["quantidade_pessoas"] = str(dados_json["quantidade_pessoas"])
            st.success(f"Dados de **{dados_json.get('nome_locatario_pf', '')}** importados!")
            if dados_json.get("composicao_grupo"):
                st.caption(f"Grupo: {dados_json['composicao_grupo']}")
            if dados_json.get("observacoes"):
                st.info(f"Observações: {dados_json['observacoes']}")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

    tipo_locatario = st.selectbox(
        "Tipo do locatário",
        ["Pessoa Física", "Pessoa Jurídica"],
        index=0,
        key="tipo_locatario",
    )
    dados_locatario = renderizar_parte("Locatário", "locatario", tipo_locatario)

with st.form("form_contrato"):
    st.subheader("Configuração inicial")
    tem_taxa_servico = st.checkbox("Tem taxa de serviço?", value=False, key="tem_taxa_servico")
    idioma_contrato = st.selectbox(
        "Idioma do contrato",
        ["Português", "Bilíngue PT + EN", "Bilíngue PT + ES"],
        index=0,
        key="idioma_contrato",
    )

    st.subheader("Dados bancários")
    c_banco1, c_banco2 = st.columns(2)
    with c_banco1:
        banco_locador = st.text_area("Dados bancários do locador", height=120, key="banco_locador")

    with c_banco2:
        banco_corretora_opcao = st.selectbox(
            "Conta da corretora",
            list(CONTAS_CORRETORA.keys()),
            index=0,
            key="banco_corretora_opcao"
        )
        banco_corretora = CONTAS_CORRETORA[banco_corretora_opcao]
        st.text_area(
            "Dados bancários selecionados da corretora",
            value=banco_corretora,
            height=120,
            disabled=True,
            key="dados_bancarios_corretora"
        )

    st.subheader("Imóvel e hospedagem")
    c1, c2, c3 = st.columns(3)

    with c1:
        nome_imovel = st.text_input("Nome do imóvel", key="nome_imovel")
        link_imovel = st.text_input("Link do imóvel", key="link_imovel")
        cidade_imovel = st.text_input("Cidade / Distrito do imóvel", key="cidade_imovel")

    with c2:
        numero_suites = st.text_input("Número de suítes", key="numero_suites")
        ocupacao_maxima = st.text_input("Ocupação máxima", key="ocupacao_maxima")
        quantidade_pessoas = st.text_input("Quantidade de pessoas na hospedagem", key="quantidade_pessoas")

    with c3:
        quantidade_staff = st.text_input("Quantidade de staff", key="quantidade_staff")
        data_checkin = st.text_input("Data de check-in (dd/mm/aaaa)", key="data_checkin")
        data_checkout = st.text_input("Data de checkout (dd/mm/aaaa)", key="data_checkout")

    descricao_suites = st.text_area("Descrição das suítes", height=180, key="descricao_suites")
    descricao_staff = st.text_area("Descrição detalhada do staff", height=120, key="descricao_staff")

    st.subheader("Valores")
    c4, c5 = st.columns(2)
    with c4:
        valor_hospedagem = st.text_input("Valor total da hospedagem", key="valor_hospedagem")
    with c5:
        valor_caucao = st.text_input("Valor da caução", key="valor_caucao")

    gerar = st.form_submit_button("Gerar contrato", use_container_width=True)

if gerar:
    try:
        dados = {
            "tem_taxa_servico": tem_taxa_servico,
            **dados_locador,
            **dados_locatario,

            "banco_locador": banco_locador,
            "banco_corretora": banco_corretora,

            "nome_imovel": nome_imovel,
            "link_imovel": link_imovel,
            "cidade_imovel": cidade_imovel,
            "numero_suites": str_para_int(numero_suites, "Número de suítes"),
            "descricao_suites": descricao_suites,
            "ocupacao_maxima": str_para_int(ocupacao_maxima, "Ocupação máxima"),
            "quantidade_pessoas": str_para_int(quantidade_pessoas, "Quantidade de pessoas"),
            "quantidade_staff": str_para_int(quantidade_staff, "Quantidade de staff"),
            "descricao_staff": descricao_staff,

            "data_checkin": str_para_data(data_checkin),
            "data_checkout": str_para_data(data_checkout),
            "valor_hospedagem": valor_hospedagem,
            "valor_caucao": valor_caucao,
        }

        resultado = calcular_contexto(dados)
        contexto = resultado["contexto"]
        resumo = resultado["resumo"]

        nome_saida = nome_arquivo_seguro(
            f"Contrato - {nome_imovel or 'Contrato'} - {banco_corretora_opcao}"
        )
        if idioma_contrato == "Bilíngue PT + EN":
            with st.spinner("Traduzindo para inglês..."):
                contexto_trad = traduzir_contexto(contexto, idioma="en")
            docx_bytes = gerar_docx(contexto_trad, idioma="en")
        elif idioma_contrato == "Bilíngue PT + ES":
            with st.spinner("Traduzindo para espanhol..."):
                contexto_trad = traduzir_contexto(contexto, idioma="es")
            docx_bytes = gerar_docx(contexto_trad, idioma="es")
        else:
            docx_bytes = gerar_docx(contexto)

        st.success("Contrato gerado com sucesso!")

        r1, r2, r3 = st.columns(3)
        r1.metric("Proprietário", f"R$ {formatar_moeda(resumo['valor_proprietario'])}")
        r2.metric("Imobiliária", f"R$ {formatar_moeda(resumo['valor_imobiliaria'])}")
        r3.metric("Corretor", f"R$ {formatar_moeda(resumo['valor_corretor'])}")

        r4, r5, r6 = st.columns(3)
        r4.metric("Staff", f"R$ {formatar_moeda(resumo['valor_staff'])}")
        r5.metric("Diária", f"R$ {formatar_moeda(resumo['valor_diaria'])}")
        r6.metric("Multa", f"R$ {formatar_moeda(resumo['valor_multa'])}")

        st.subheader("Momento A / Momento B")
        m1, m2, m3 = st.columns(3)
        m1.write(f"**Proprietário A:** R$ {formatar_moeda(resumo['valor_momentoA_proprietario'])}")
        m1.write(f"**Proprietário B:** R$ {formatar_moeda(resumo['valor_momentoB_proprietario'])}")

        m2.write(f"**Bahia A:** R$ {formatar_moeda(resumo['valor_momentoA_bahia'])}")
        m2.write(f"**Bahia B:** R$ {formatar_moeda(resumo['valor_momentoB_bahia'])}")

        m3.write(f"**Corretor A:** R$ {formatar_moeda(resumo['valor_momentoA_corretor'])}")
        m3.write(f"**Corretor B:** R$ {formatar_moeda(resumo['valor_momentoB_corretor'])}")

        st.info(f"Momento B calculado automaticamente para: **{resumo['data_momento_b_extenso']}**")
        st.write(f"Noites calculadas: **{resumo['noites_numero']}**")

        st.download_button(
            label="Baixar contrato .docx",
            data=docx_bytes,
            file_name=f"{nome_saida}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    except Exception as e:
        st.error(f"Erro ao gerar contrato: {e}")
