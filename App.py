import streamlit as st
import os
from google import genai
from PyPDF2 import PdfReader

# --- 1. Configuração da Página ---
st.set_page_config(
    page_title="Assistente de Diagnóstico Comercial", 
    page_icon="💼", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Inicialização do Cliente API ---
@st.cache_resource
def inicializar_cliente():
    try:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
        return genai.Client()
    except KeyError:
        return None

client = inicializar_cliente()

# --- 3. Funções Modulares ---
def extrair_texto_pdf(arquivo):
    leitor_pdf = PdfReader(arquivo)
    texto = "".join([pagina.extract_text() or "" for pagina in leitor_pdf.pages])
    return texto.strip()

def gerar_prompt_multiplas_atas(texto_transcricao):
    return f"""
    Imagine que você é um revisor técnico de uma consultoria estratégica.

    Vou te enviar anotações brutas que PODEM conter transcrições de UMA OU MÚLTIPLAS reuniões comerciais diferentes (muitas vezes separadas por marcações como *AT NOME_DA_EMPRESA*, trocas de interlocutores ou mudanças completas de contexto).

    Sua tarefa tem duas etapas:
    1. Identifique e separe cada reunião distinta presente no texto.
    2. Para CADA reunião identificada, crie uma ata executiva separada e estruturada.

    Para CADA ata, você deve OBRIGATORIAMENTE usar o seguinte formato (em Markdown):

    ## 🏢 Ata de Reunião: [Nome da Empresa ou Cliente Identificado]

    **Rapport:**
    Contexto humano da reunião, nível de abertura do contato, clima da conversa e contexto da empresa.

    **Com quem eu estou falando:**
    Cargo da pessoa, área de atuação e papel no processo decisório.

    **O que o projeto está se encaminhando para ser:**
    Síntese da oportunidade de projeto. Qual problema pode ser resolvido e qual tipo de solução.

    **Fatores cruciais de mapeamento:**
    Elementos que impactam a viabilidade: sistemas, dados, cloud, processos atuais, maturidade digital e dores.

    **Próximo passo claro:**
    Próxima ação comercial objetiva (ex.: proposta, NDA, envio de bases, etc).

    ---
    Regras importantes:
    - Se você identificar 1 reunião, gere apenas 1 ata. Se identificar múltiplas reuniões diferentes, gere atas sequenciais usando o modelo acima.
    - Separe cada ata visualmente com uma linha (---).
    - Escreva em texto corrido (sem bullet points dentro das seções).
    - Seja curto, claro e objetivo.

    Transcrição Bruta a ser analisada:
    {texto_transcricao}
    """

# --- 4. Interface de Usuário (UI) e Configuração de Modelos ---
# Dicionário mapeando um nome amigável para o ID real do modelo na API
opcoes_modelos = {
    "🟡 Intermediário: Gemini 2.5 Flash (Padrão/Equilibrado)": "gemini-2.5-flash",
    "🔴 Pesado: Gemini 2.5 Pro (Maior raciocínio, mais lento)": "gemini-2.5-pro",
    "🔴 Pesado: Gemini 3.1 Pro Preview (Experimental)": "gemini-3.1-pro-preview",
    "🟢 Básico: Gemini 2.5 Flash Lite (Rápido, custo menor)": "gemini-2.5-flash-lite",
    "🟢 Básico: Gemma 3 27B IT (Modelo aberto)": "gemma-3-27b-it"
}

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2097/2097726.png", width=100)
    st.title("Configurações")
    
    # Dropdown para o usuário escolher o modelo
    modelo_selecionado_nome = st.selectbox(
        "🧠 Escolha o Modelo de IA:",
        options=list(opcoes_modelos.keys()),
        index=0, # Deixa o Gemini 2.5 Flash como padrão selecionado
        help="Modelos Pesados são melhores para textos muito complexos, mas demoram mais. Modelos Básicos são ultrarrápidos, mas podem perder nuances."
    )
    
    # Recupera a string real (ex: 'gemini-2.5-flash') com base na escolha
    modelo_id_real = opcoes_modelos[modelo_selecionado_nome]
    
    st.divider()
    st.markdown("### Como usar:")
    st.markdown("1. Ajuste o modelo de IA acima.\n2. Faça o upload dos PDFs.\n3. Processe e baixe as atas.")

st.title("💼 Assistente de Atas e Diagnóstico")
st.markdown("Processe múltiplos arquivos e gere insights adaptando o peso do processamento conforme a sua necessidade.")
st.divider()

if client is None:
    st.error("🚨 Chave de API não encontrada nos Secrets.")
    st.stop()

arquivos_pdf = st.file_uploader("📂 Faça o upload das transcrições (PDFs)", type=["pdf"], accept_multiple_files=True)

# --- 5. Fluxo de Execução Principal ---
if arquivos_pdf:
    with st.container():
        if st.button("🚀 Processar Todos os Arquivos", type="primary", use_container_width=True):
            
            for arquivo in arquivos_pdf:
                st.subheader(f"📄 Analisando: {arquivo.name} | Modelo: {modelo_id_real}")
                
                with st.status(f"Processando {arquivo.name}...", expanded=True) as status:
                    try:
                        st.write("Extraindo texto do PDF...")
                        texto_da_reuniao = extrair_texto_pdf(arquivo)
                        
                        if not texto_da_reuniao:
                            status.update(label=f"Falha na extração de {arquivo.name}", state="error")
                            st.warning("O PDF parece estar vazio ou não possui texto selecionável.")
                            continue
                        
                        st.write(f"Conectando ao {modelo_id_real} e estruturando atas...")
                        prompt_formatado = gerar_prompt_multiplas_atas(texto_da_reuniao)
                        
                        # Aqui injetamos a variável dinâmica com o modelo escolhido
                        resposta = client.models.generate_content(
                            model=modelo_id_real,
                            contents=prompt_formatado
                        )
                        
                        status.update(label=f"Diagnóstico de {arquivo.name} concluído!", state="complete", expanded=False)
                        
                        container_resposta = st.container(border=True)
                        with container_resposta:
                            st.markdown(resposta.text)
                        
                        st.download_button(
                            label=f"📥 Baixar Atas ({arquivo.name})",
                            data=resposta.text,
                            file_name=f"atas_{arquivo.name.replace('.pdf', '')}.txt",
                            mime="text/plain",
                            type="secondary",
                            key=f"download_{arquivo.name}"
                        )

                        with st.expander(f"🛠️ Ver Texto Original Extraído ({arquivo.name})"):
                            st.text_area("Texto bruto identificado pelo Python:", texto_da_reuniao, height=200, disabled=True, key=f"debug_{arquivo.name}")
                        
                        st.divider()
                        
                    except Exception as e:
                        status.update(label=f"Erro ao processar {arquivo.name}", state="error")
                        st.error(f"Falha na comunicação com a API usando o modelo {modelo_id_real}: {e}")