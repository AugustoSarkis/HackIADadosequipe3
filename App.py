import streamlit as st
import os
from google import genai
from PyPDF2 import PdfReader

# --- 1. Configuração da Página ---
st.set_page_config(page_title="Assistente de Diagnóstico", page_icon="📝", layout="centered")

# --- 2. Autenticação Segura ---
try:
    # A nova biblioteca busca a chave diretamente nas variáveis de ambiente do sistema operacional
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    # Inicializa o cliente na nova arquitetura
    client = genai.Client()
except KeyError:
    st.error("🚨 Chave de API não encontrada. Configure o arquivo '.streamlit/secrets.toml' localmente ou os 'Secrets' no Streamlit Cloud.")
    st.stop()

# --- 3. Funções Modulares ---
def extrair_texto_pdf(arquivo):
    leitor_pdf = PdfReader(arquivo)
    texto = ""
    for pagina in leitor_pdf.pages:
        texto_extraido = pagina.extract_text()
        if texto_extraido:
            texto += texto_extraido + "\n"
    return texto

# --- 4. Interface de Usuário (UI) ---
st.title("📝 Assistente de Atas e Diagnóstico")
st.markdown("Automatize a extração de *insights* e o mapeamento de gargalos para propostas de projetos.")

arquivo_pdf = st.file_uploader("Faça o upload da transcrição (PDF)", type=["pdf"])

# --- 5. Fluxo de Execução Principal ---
if arquivo_pdf is not None:
    if st.button("Gerar Ata e Diagnóstico", type="primary"):
        
        with st.spinner("Analisando a transcrição e conectando ao LLM. Isso pode levar alguns segundos..."):
            try:
                texto_da_reuniao = extrair_texto_pdf(arquivo_pdf)
                
                if not texto_da_reuniao.strip():
                    st.warning("Não foi possível ler o texto deste PDF. Verifique se ele não é uma imagem escaneada.")
                    st.stop()
                
                prompt = f"""
                Você atua como analista de projetos. Sua tarefa é analisar a transcrição de uma reunião de diagnóstico e estruturar as informações para a equipe.
                
                Gere uma saída com duas partes distintas:
                1. ATA ESTRUTURADA: Resuma os principais pontos discutidos, organizando em tópicos executivos claros.
                2. GARGALOS PARA A PROPOSTA: Liste estritamente quais informações essenciais (ex: escopo de dados, integrações, regras de negócio) não foram mapeadas na conversa e que precisam ser levantadas com o cliente para dimensionar adequadamente o projeto.
                
                Transcrição:
                {texto_da_reuniao}
                """
                
                # Chamada do Modelo usando a sintaxe da nova biblioteca
                # Apontando para um modelo validado na sua lista
                resposta = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                
                st.success("Análise concluída com sucesso!")
                
                aba_resultado, aba_texto_original = st.tabs(["📊 Diagnóstico Gerado", "📄 Texto Extraído (Debug)"])
                
                with aba_resultado:
                    st.markdown(resposta.text)
                    
                with aba_texto_original:
                    st.text_area("Valide o que o Python conseguiu ler do seu PDF:", texto_da_reuniao, height=250, disabled=True)
                
            except Exception as e:
                st.error(f"Ocorreu um erro durante o processamento da API: {e}")