# -*- coding: utf-8 -*-
import json
import smtplib
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ── Configuração de e-mail ────────────────────────────────────────────────────
EMAIL_REMETENTE = "tiagomaster1234@gmail.com"
EMAIL_SENHA     = "hkvlkuyvvnyqamis"
EMAIL_DESTINO   = "erikapla@bahiahomes.com.br"

def enviar_email(dados: dict):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📋 Novo formulário de locatário – {dados.get('nome_locatario_pf', '')}"
    msg["From"]    = EMAIL_REMETENTE
    msg["To"]      = EMAIL_DESTINO

    corpo = f"""
<html><body style="font-family:Arial,sans-serif;font-size:14px;color:#222;">
<h2 style="color:#457354;">🏠 Bahia Homes – Dados do Locatário</h2>

<h3>Dados pessoais</h3>
<table style="border-collapse:collapse;width:100%;">
  <tr><td style="padding:6px;font-weight:bold;width:200px;">Nome completo</td><td style="padding:6px;">{dados.get('nome_locatario_pf','')}</td></tr>
  <tr style="background:#f5f5f5;"><td style="padding:6px;font-weight:bold;">Nacionalidade</td><td style="padding:6px;">{dados.get('nacionalidade_locatario_pf','')}</td></tr>
  <tr><td style="padding:6px;font-weight:bold;">Estado civil</td><td style="padding:6px;">{dados.get('estado_civil_locatario_pf','')}</td></tr>
  <tr style="background:#f5f5f5;"><td style="padding:6px;font-weight:bold;">Profissão</td><td style="padding:6px;">{dados.get('profissao_locatario_pf','')}</td></tr>
  <tr><td style="padding:6px;font-weight:bold;">Tipo de documento</td><td style="padding:6px;">{dados.get('tipo_doc','')}</td></tr>
  <tr style="background:#f5f5f5;"><td style="padding:6px;font-weight:bold;">CPF / RG / Passaporte</td><td style="padding:6px;">{dados.get('cpf_locatario_pf','')} {dados.get('rg_locatario_pf','')}</td></tr>
  <tr><td style="padding:6px;font-weight:bold;">Endereço</td><td style="padding:6px;">{dados.get('endereco_locatario_pf','')}</td></tr>
  <tr style="background:#f5f5f5;"><td style="padding:6px;font-weight:bold;">E-mail</td><td style="padding:6px;">{dados.get('email_locatario','')}</td></tr>
  <tr><td style="padding:6px;font-weight:bold;">Telefone / WhatsApp</td><td style="padding:6px;">{dados.get('telefone_locatario','')}</td></tr>
</table>

<p style="margin-top:32px;color:#888;font-size:12px;">Enviado automaticamente pelo Formulário do Locatário – Bahia Homes</p>
</body></html>
"""

    msg.attach(MIMEText(corpo, "html"))

    json_bytes = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
    nome_arquivo = f"dados_{dados.get('nome_locatario_pf','locatario').split()[0].lower()}.json"
    anexo = MIMEBase("application", "octet-stream")
    anexo.set_payload(json_bytes)
    encoders.encode_base64(anexo)
    anexo.add_header("Content-Disposition", f'attachment; filename="{nome_arquivo}"')
    msg.attach(anexo)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_REMETENTE, EMAIL_SENHA)
        smtp.sendmail(EMAIL_REMETENTE, EMAIL_DESTINO, msg.as_string())


# ── Interface ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Formulário do Hóspede – Bahia Homes",
    page_icon="🏠",
    layout="centered",
)

st.markdown("""
<style>
[data-testid="stAppViewBlockContainer"] img[alt="user avatar"] { display: none; }
header[data-testid="stHeader"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
.stDeployButton { display: none; }
button[kind="userAvatar"] { display: none !important; }
[data-testid="userAvatar"] { display: none !important; }
iframe[title="streamlit_cloud_user_info"] { display: none !important; }
div[class*="ProfileButton"] { display: none !important; }
div[class*="userAvatar"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.image(
    "https://raw.githubusercontent.com/Tiagopydados/bahiahomes-contratos/main/Arquivos_necessarios/Logo_BH_vetorizada.png",
    width=250,
)
st.subheader("Formulário de dados do hóspede")
st.caption("Preencha seus dados abaixo. Ao finalizar, clique em **Enviar** — seus dados chegarão diretamente para a nossa equipe.")

st.divider()

st.subheader("Seus dados pessoais")

tipo_doc = st.selectbox(
    "Tipo de documento",
    ["CPF (brasileiro)", "Passaporte"],
    key="tipo_doc",
)

col1, col2 = st.columns(2)
with col1:
    nome          = st.text_input("Nome completo *", key="nome")
    nacionalidade = st.text_input("Nacionalidade *", key="nacionalidade")
    estado_civil  = st.selectbox(
        "Estado civil *",
        ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União estável"],
        key="estado_civil",
    )
    profissao = st.text_input("Profissão *", key="profissao")

with col2:
    if tipo_doc == "CPF (brasileiro)":
        cpf        = st.text_input("CPF *", placeholder="000.000.000-00", key="cpf")
        rg         = st.text_input("RG *", key="rg")
        passaporte = ""
    else:
        passaporte = st.text_input("Número do passaporte *", key="passaporte")
        cpf = ""
        rg  = ""

    email    = st.text_input("E-mail *", key="email")
    telefone = st.text_input("Telefone / WhatsApp *", placeholder="+55 11 99999-9999", key="telefone")

endereco = st.text_area("Endereço completo *", placeholder="Rua, número, cidade, estado, país, CEP", height=80, key="endereco")

st.divider()

# ── Envio ─────────────────────────────────────────────────────────────────────
campos_obrigatorios = [nome, nacionalidade, profissao, email, telefone, endereco]
if tipo_doc == "CPF (brasileiro)":
    campos_obrigatorios += [cpf, rg]
else:
    campos_obrigatorios += [passaporte]

if st.button("Enviar dados para a Bahia Homes", use_container_width=True, type="primary"):
    if not all(c.strip() for c in campos_obrigatorios):
        st.error("Por favor, preencha todos os campos obrigatórios (*) antes de continuar.")
    else:
        dados = {
            "tipo_locatario": "Pessoa Física",
            "tipo_doc": tipo_doc,
            "nome_locatario_pf": nome.strip(),
            "nacionalidade_locatario_pf": nacionalidade.strip(),
            "estado_civil_locatario_pf": estado_civil.lower(),
            "profissao_locatario_pf": profissao.strip(),
            "cpf_locatario_pf": cpf.strip(),
            "rg_locatario_pf": rg.strip() if rg else passaporte.strip(),
            "endereco_locatario_pf": endereco.strip(),
            "email_locatario": email.strip(),
            "telefone_locatario": telefone.strip(),
            # Campos para compatibilidade com app principal
            "nome_empresa_locatario": "",
            "cnpj_empresa_locatario": "",
            "endereco_empresa_locatario": "",
            "nome_representante_locatario": "",
            "nacionalidade_representante_locatario": "",
            "estado_civil_representante_locatario": "",
            "profissao_representante_locatario": "",
            "cpf_representante_locatario": "",
            "rg_representante_locatario": "",
            "endereco_representante_locatario": "",
        }

        try:
            enviar_email(dados)
            st.success("✅ Dados enviados com sucesso! A equipe da Bahia Homes entrará em contato em breve.")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao enviar. Tente novamente ou entre em contato pelo WhatsApp. (Detalhe: {e})")

        json_bytes = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="⬇️ Baixar cópia dos seus dados (.json)",
            data=json_bytes,
            file_name=f"dados_{nome.strip().split()[0].lower()}.json",
            mime="application/json",
            use_container_width=True,
        )
