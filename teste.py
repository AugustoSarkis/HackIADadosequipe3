import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os
from dotenv import load_dotenv

# Configuração da Página
st.set_page_config(page_title="Analista de Reuniões Gemini", page_icon="📝")
load_dotenv()

# Configurar API Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash') # Flash é mais rápido e barato para resumos

def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

st.title("📝 Analista de Transcrições")
st.subheader("Transforme conversas em insights acionáveis")

# Sidebar para configurações
with st.sidebar:
    st.info("Faça o upload da transcrição da sua reunião em PDF.")

# Área de Upload
uploaded_file = st.file_uploader("Escolha o arquivo PDF da reunião", type="pdf")

# Área do Prompt
user_prompt = st.text_area(
    "O que você quer saber sobre essa reunião?",
    placeholder="Ex: Quais foram as decisões tomadas e os próximos passos para o João?"
)

if st.button("Analisar Reunião"):
    if uploaded_file and user_prompt:
        with st.spinner("O Gemini está analisando o arquivo..."):
            try:
                # 1. Extrair texto
                content = extract_pdf_text(uploaded_file)
                
                # 2. Montar o Contexto
                full_prompt = f"Com base na seguinte transcrição de reunião:\n\n{content}\n\nResponda ao seguinte pedido: {user_prompt}"
                
                # 3. Chamar a API
                response = model.generate_content(full_prompt)
                
                # 4. Exibir Resultado
                st.markdown("### ✨ Insights do Gemini")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")
    else:
        st.warning("Por favor, faça o upload do PDF e escreva um prompt.")