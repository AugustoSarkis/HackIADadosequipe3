import streamlit as st
import google.generativeai as genai

# ... (suas configurações de API e do modelo) ...

# 1. O usuário faz o upload do arquivo de texto
arquivo_enviado = st.file_uploader("Faça o upload da transcrição", type=["txt"])

if arquivo_enviado is not None:
    # 2. Lemos o texto diretamente da memória do Streamlit
    texto_da_reuniao = arquivo_enviado.getvalue().decode("utf-8")
    
    st.write("Analisando a transcrição...")
    
    # 3. Injetamos o texto diretamente no prompt, sem usar upload_file
    prompt = f"""
    Você é um assistente comercial. Analise a transcrição abaixo e gere uma ata estruturada.
    Aponte também as informações essenciais que não foram mapeadas.
    
    Transcrição:
    {texto_da_reuniao}
    """
    
    # 4. Chamamos o modelo de forma direta
    resposta = modelo.generate_content(prompt)
    
    # 5. Exibimos o resultado
    st.write(resposta.text)