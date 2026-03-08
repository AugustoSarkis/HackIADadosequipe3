import streamlit as st
import os
from google import genai
from PyPDF2 import PdfReader

# --- 1. Configuração da Página ---
# Alterado para 'wide' para aproveitar melhor o espaço da tela, ideal para leitura de relatórios.
st.set_page_config(
    page_title="Assistente de Diagnóstico Comercial", 
    page_icon="💼", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Inicialização do Cliente API ---
# Usamos st.cache_resource para evitar que o cliente seja recriado a cada interação na tela.
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
    """Extrai o texto de um arquivo PDF carregado."""
    leitor_pdf = PdfReader(arquivo)
    texto = "".join([pagina.extract_text() or "" for pagina in leitor_pdf.pages])
    return texto.strip()

def gerar_prompt(texto_transcricao):
    """Isola a lógica do prompt, mantendo o fluxo principal limpo."""
    return f"""
    Imagine que você é um revisor técnico de uma consultoria estratégica.

    Vou te enviar anotações brutas de uma reunião comercial. Elas podem estar desorganizadas, incompletas, informais ou fora de ordem. Sua tarefa é interpretar essas anotações e transformá-las em uma ata executiva curta.

    Estruture obrigatoriamente a resposta nos seguintes tópicos, em texto corrido (sem bullet points):

    Rapport:
    Contexto humano da reunião e nível de abertura do contato. Clima da conversa, interesse demonstrado, contexto da empresa.

    Com quem eu estou falando:
    Cargo da pessoa, área de atuação e papel no processo decisório.

    O que o projeto está se encaminhando para ser:
    Síntese da oportunidade de projeto. Qual problema pode ser resolvido e qual tipo de solução pode ser proposta.

    Fatores cruciais de mapeamento:
    Elementos que impactam a viabilidade: sistemas, dados, cloud, processos atuais, maturidade digital, limitações e dores operacionais.

    Próximo passo claro:
    Próxima ação comercial objetiva (ex.: proposta, NDA, validação interna).

    Regras importantes:
    - Escreva em texto corrido, sem listas.
    - Seja curto, claro e objetivo.
    - Priorize dor do cliente, maturidade digital e oportunidade de projeto.
    - Elimine informações irrelevantes.

    Transcrição da Reunião:
    {texto_transcricao}
    """

# --- 4. Interface de Usuário (UI) ---

# Sidebar para instruções e configurações visuais
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2097/2097726.png", width=100) # Ícone genérico, substitua pela logo do seu núcleo se desejar
    st.title("Sobre a Ferramenta")
    st.info(
        "Este assistente utiliza o modelo **Gemini 2.5 Flash** para processar transcrições "
        "brutas e gerar atas estruturadas, focando no avanço comercial e mapeamento técnico."
    )
    st.divider()
    st.markdown("### Como usar:")
    st.markdown("1. Faça o upload da transcrição em PDF.\n2. Clique em 'Gerar Diagnóstico'.\n3. Exporte o resultado.")

# Corpo principal
st.title("💼 Assistente de Atas e Diagnóstico")
st.markdown("Transforme anotações brutas em **insights estratégicos** e propostas de projetos estruturadas.")
st.divider()

if client is None:
    st.error("🚨 Chave de API não encontrada nos Secrets. Configure `.streamlit/secrets.toml`.")
    st.stop()

# Layout em colunas para a área de upload ficar mais elegante
col1, col2 = st.columns([2, 1])

with col1:
    arquivo_pdf = st.file_uploader("📂 Faça o upload da transcrição (formato PDF)", type=["pdf"])

# --- 5. Fluxo de Execução Principal ---
if arquivo_pdf is not None:
    # Usando st.container para agrupar visualmente o botão e o status
    with st.container():
        if st.button("🚀 Gerar Ata e Diagnóstico", type="primary", use_container_width=True):
            
            # st.status fornece um feedback visual muito mais rico que apenas o spinner
            with st.status("Processando documento...", expanded=True) as status:
                try:
                    st.write("📄 Extraindo texto do PDF...")
                    texto_da_reuniao = extrair_texto_pdf(arquivo_pdf)
                    
                    if not texto_da_reuniao:
                        status.update(label="Falha na extração", state="error")
                        st.warning("O PDF parece estar vazio ou é uma imagem escaneada (sem texto selecionável).")
                        st.stop()
                    
                    st.write("🧠 Conectando ao modelo LLM e estruturando diagnóstico...")
                    prompt_formatado = gerar_prompt(texto_da_reuniao)
                    
                    resposta = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt_formatado
                    )
                    
                    status.update(label="Diagnóstico concluído com sucesso!", state="complete", expanded=False)
                    
                    # Exibição dos resultados
                    st.divider()
                    st.subheader("📊 Resultado do Diagnóstico")
                    
                    # Coloca a resposta em um container com destaque
                    container_resposta = st.container(border=True)
                    with container_resposta:
                        st.markdown(resposta.text)
                    
                    # Funcionalidade extra: Botão de Download
                    st.download_button(
                        label="📥 Baixar Ata como TXT",
                        data=resposta.text,
                        file_name="ata_diagnostico.txt",
                        mime="text/plain",
                        type="secondary"
                    )

                    # Debug escondido em um expander (melhor UX do que abas para dados secundários)
                    with st.expander("🛠️ Ver Texto Original Extraído (Debug)"):
                        st.text_area("Texto bruto identificado pelo Python:", texto_da_reuniao, height=200, disabled=True)
                    
                except Exception as e:
                    status.update(label="Erro no processamento", state="error")
                    st.error(f"Falha na comunicação com a API: {e}")