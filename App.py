import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# 1. Configuração da API
# Lógica: O Streamlit Cloud lida melhor com secrets nativos. 
# Certifique-se de colocar sua chave em "Advanced Settings" > "Secrets" no painel do Streamlit Cloud
    # Fallback de segurança caso esteja rodando localmente sem o secrets.toml
import os
chave_api = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=chave_api)

# Usando o modelo Flash, que é excelente e rápido para sumarização
modelo = genai.GenerativeModel('gemini-1.5-flash')

st.title("📝 Assistente de Atas e Diagnóstico")
st.write("Faça o upload da transcrição da reunião de diagnóstico para gerar a ata e identificar gargalos para a proposta.")

# 2. Upload do arquivo
arquivo_pdf = st.file_uploader("Faça o upload da transcrição (PDF)", type=["pdf"])

# 3. Bloco de Processamento com Botão e Spinner
if arquivo_pdf is not None:
    # O botão impede que o código rode sozinho a cada recarregamento da página
    if st.button("Gerar Ata e Diagnóstico"):
        
        # st.spinner cria uma animação de carregamento enquanto o bloco de código "with" é executado
        with st.spinner("Lendo o PDF e analisando a transcrição... Isso pode levar alguns segundos."):
            try:
                # Extração do PDF
                leitor_pdf = PdfReader(arquivo_pdf)
                texto_da_reuniao = ""
                
                for pagina in leitor_pdf.pages:
                    texto_extraido = pagina.extract_text()
                    if texto_extraido:
                        texto_da_reuniao += texto_extraido + "\n"
                
                # Construção do Prompt Estruturado
                prompt = f"""
                Você é um assistente comercial experiente. Analise a transcrição da reunião de diagnóstico abaixo e gere uma saída com duas partes distintas:
                
                1. ATA ESTRUTURADA: Resuma os principais pontos discutidos, organizando em tópicos claros e objetivos.
                2. INFORMAÇÕES FALTANTES (Gargalos): Identifique e liste estritamente quais informações essenciais não foram mapeadas na conversa e que precisam ser aprofundadas para que a equipe consiga dimensionar adequadamente a proposta de projeto.
                
                Transcrição:
                {texto_da_reuniao}
                """
                
                # Chamada da API
                resposta = modelo.generate_content(prompt)
                
                # Exibição dos resultados
                st.success("Análise concluída com sucesso!")
                st.markdown(resposta.text)
                
            except Exception as e:
                # Captura e exibe qualquer erro de forma amigável
                st.error(f"Ocorreu um erro durante o processamento: {e}")