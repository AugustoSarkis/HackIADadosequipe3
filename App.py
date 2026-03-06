import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
import os

# 1. Configuração da API
# A lógica: tenta pegar a chave das variáveis de ambiente (onde o Streamlit Cloud guarda as Secrets)
chave_api = os.getenv("GEMINI_API_KEY") 
genai.configure(api_key=chave_api)

# Usamos o modelo Flash por ser mais rápido para textos longos e perfeitamente capaz dessa tarefa
modelo = genai.GenerativeModel('gemini-1.5-flash')

st.title("📝 Assistente de Atas e Diagnóstico")
st.write("Faça o upload da transcrição da reunião de diagnóstico para gerar a ata e identificar gargalos para a proposta.")

# 2. O usuário faz o upload do arquivo PDF direto na interface
arquivo_pdf = st.file_uploader("Faça o upload da transcrição (PDF)", type=["pdf"])

if arquivo_pdf is not None:
    st.info("Lendo o documento PDF...")
    
    # 3. Lemos o PDF diretamente da memória do Streamlit
    leitor_pdf = PdfReader(arquivo_pdf)
    texto_da_reuniao = ""
    
    # Iteramos por todas as páginas do PDF para extrair o texto completo
    for pagina in leitor_pdf.pages:
        # Verifica se há texto na página para evitar erros de concatenação
        texto_extraido = pagina.extract_text()
        if texto_extraido:
            texto_da_reuniao += texto_extraido + "\n"
    
    st.info("Analisando a transcrição e gerando a ata...")
    
    # 4. Construção do Prompt Estruturado
    prompt = f"""
    Você é um assistente comercial experiente. Analise a transcrição da reunião de diagnóstico abaixo e gere uma saída com duas partes distintas:
    
    1. ATA ESTRUTURADA: Resuma os principais pontos discutidos, organizando em tópicos claros e objetivos.
    2. INFORMAÇÕES FALTANTES (Gargalos): Identifique e liste estritamente quais informações essenciais não foram mapeadas na conversa e que precisam ser aprofundadas para que a equipe consiga dimensionar adequadamente a proposta de projeto.
    
    Transcrição:
    {texto_da_reuniao}
    """
    
    # 5. Chamada do modelo e exibição
    try:
        resposta = modelo.generate_content(prompt)
        st.success("Análise concluída!")
        
        # O st.markdown renderiza o texto preservando negritos, listas e quebras de linha que o Gemini gera
        st.markdown(resposta.text)
        
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar com a IA: {e}")