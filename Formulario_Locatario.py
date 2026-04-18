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

<h3 style="margin-top:24px;">Composição do grupo</h3>
<table style="border-collapse:collapse;width:100%;">
  <tr><td style="padding:6px;font-weight:bold;width:200px;">Casais</td><td style="padding:6px;">{dados.get('casais',0)}</td></tr>
  <tr style="background:#f5f5f5;"><td style="padding:6px;font-weight:bold;">Solteiros</td><td style="padding:6px;">{dados.get('solteiros',0)}</td></tr>
  <tr><td style="padding:6px;font-weight:bold;">Crianças</td><td style="padding:6px;">{dados.get('criancas',0)}</td></tr>
  <tr style="background:#f5f5f5;"><td style="padding:6px;font-weight:bold;">Babá(s)</td><td style="padding:6px;">{dados.get('baba',0)}</td></tr>
  <tr><td style="padding:6px;font-weight:bold;">Total de pessoas</td><td style="padding:6px;font-weight:bold;color:#457354;">{dados.get('quantidade_pessoas',0)}</td></tr>
</table>

{"<h3 style='margin-top:24px;'>Observações</h3><p>" + dados.get('observacoes','') + "</p>" if dados.get('observacoes') else ""}

<p style="margin-top:32px;color:#888;font-size:12px;">Enviado automaticamente pelo Formulário do Locatário – Bahia Homes</p>
</body></html>
"""

    msg.attach(MIMEText(corpo, "html"))

    # Anexar o .json
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

st.title("🏠 Bahia Homes")
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
    nome        = st.text_input("Nome completo *", key="nome")
    nacionalidade = st.text_input("Nacionalidade *", key="nacionalidade")
    estado_civil  = st.selectbox(
        "Estado civil *",
        ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "União estável"],
        key="estado_civil",
    )
    profissao = st.text_input("Profissão *", key="profissao")

with col2:
    if tipo_doc == "CPF (brasileiro)":
        cpf       = st.text_input("CPF *", placeholder="000.000.000-00", key="cpf")
        rg        = st.text_input("RG *", key="rg")
        passaporte = ""
    else:
        passaporte = st.text_input("Número do passaporte *", key="passaporte")
        cpf = ""
        rg  = ""

    email    = st.text_input("E-mail *", key="email")
    telefone = st.text_input("Telefone / WhatsApp *", placeholder="+55 11 99999-9999", key="telefone")

endereco = st.text_area("Endereço completo *", placeholder="Rua, número, cidade, estado, país, CEP", height=80, key="endereco")

st.divider()

st.subheader("Composição do grupo")
st.caption("Informe quantas pessoas de cada categoria virão na hospedagem.")

c1, c2, c3, c4 = st.columns(4)
with c1:
    casais    = st.number_input("Casais",    min_value=0, step=1, key="casais")
with c2:
    solteiros = st.number_input("Solteiros", min_value=0, step=1, key="solteiros")
with c3:
    criancas  = st.number_input("Crianças",  min_value=0, step=1, key="criancas")
with c4:
    baba      = st.number_input("Babá(s)",   min_value=0, step=1, key="baba")

total_pessoas = int(casais) * 2 + int(solteiros) + int(criancas) + int(baba)
if total_pessoas > 0:
    st.info(f"Total de pessoas: **{total_pessoas}**")

st.divider()

observacoes = st.text_area(
    "Observações ou necessidades especiais (opcional)",
    height=80,
    key="observacoes",
)

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
            "casais": int(casais),
            "solteiros": int(solteiros),
            "criancas": int(criancas),
            "baba": int(baba),
            "quantidade_pessoas": total_pessoas,
            "composicao_grupo": (
                f"{int(casais)} casal(is), {int(solteiros)} solteiro(s), "
                f"{int(criancas)} criança(s), {int(baba)} babá(s)"
            ),
            "observacoes": observacoes.strip(),
        }

        try:
            enviar_email(dados)
            st.success("✅ Dados enviados com sucesso! A equipe da Bahia Homes entrará em contato em breve.")
            st.balloons()
        except Exception as e:
            st.error(f"Erro ao enviar. Tente novamente ou entre em contato pelo WhatsApp. (Detalhe: {e})")

        # Download do json como backup
        json_bytes = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="⬇️ Baixar cópia dos seus dados (.json)",
            data=json_bytes,
            file_name=f"dados_{nome.strip().split()[0].lower()}.json",
            mime="application/json",
            use_container_width=True,
        )