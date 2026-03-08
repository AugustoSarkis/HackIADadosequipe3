import streamlit as st
import os
from google import genai
from PyPDF2 import PdfReader
from docx import Document
import io

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

# --- 3. Controle de Estado (Session State) ---
# O Streamlit recarrega a página a cada interação. O session_state garante 
# que as respostas da IA, os tokens e as edições manuais não sumam da tela.
if "resultados_processados" not in st.session_state:
    st.session_state.resultados_processados = {}

def limpar_memoria():
    st.session_state.resultados_processados = {}

# --- 4. Funções Modulares ---
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

    Para CADA ata, você deve OBRIGATORIAMENTE usar o seguinte formato:

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

def criar_docx(texto_markdown):
    """
    Lê o texto gerado (que tem formatação simples em Markdown) e o converte
    para elementos nativos do Microsoft Word.
    """
    doc = Document()
    doc.add_heading('Diagnóstico Comercial - Relatório Gerado', 0)
    
    # Lógica simples de conversão de Markdown para Word
    linhas = texto_markdown.split('\n')
    for linha in linhas:
        linha = linha.strip()
        if not linha:
            continue
            
        if linha.startswith('## '):
            doc.add_heading(linha.replace('## ', ''), level=2)
        elif linha.startswith('**') and linha.endswith('**'):
            p = doc.add_paragraph()
            p.add_run(linha.replace('**', '')).bold = True
        elif linha == '---':
            doc.add_page_break() # Quebra de página entre diferentes atas
        else:
            doc.add_paragraph(linha)
            
    # Salva o documento em memória (BytesIO) para o botão de download do Streamlit
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()

# --- 5. Interface de Usuário (UI) ---
opcoes_modelos = {
    "🟢 Básico: Gemini 2.5 Flash Lite (Rápido, custo menor)": "gemini-2.5-flash-lite",
    "🟡 Intermediário: Gemini 2.5 Flash (Padrão/Equilibrado)": "gemini-2.5-flash",
    "🔴 Pesado: Gemini 2.5 Pro (Maior raciocínio, mais lento)": "gemini-2.5-pro",
}

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2097/2097726.png", width=100)
    st.title("Configurações")
    
    modelo_selecionado_nome = st.selectbox(
        "🧠 Escolha o Modelo de IA:",
        options=list(opcoes_modelos.keys()),
        index=0, 
        help="Modelos Pesados são melhores para textos muito complexos, mas demoram mais. Modelos Básicos são ultrarrápidos, mas podem perder nuances."
    )
    modelo_id_real = opcoes_modelos[modelo_selecionado_nome]
    
    st.divider()
    if st.button("🧹 Limpar Dados da Sessão", on_click=limpar_memoria):
        st.success("Memória limpa!")

st.title("💼 Assistente de Atas e Diagnóstico")
st.markdown("Processe múltiplos arquivos, valide os resultados, avalie os custos de processamento e exporte os entregáveis em `.docx`.")
st.divider()

if client is None:
    st.error("🚨 Chave de API não encontrada nos Secrets.")
    st.stop()

arquivos_pdf = st.file_uploader("📂 Faça o upload das transcrições (PDFs)", type=["pdf"], accept_multiple_files=True)

# --- 6. Fluxo de Execução Principal (Chamada à API) ---
if arquivos_pdf and st.button("🚀 Processar Todos os Arquivos", type="primary"):
    with st.container():
        for arquivo in arquivos_pdf:
            st.subheader(f"📄 Analisando: {arquivo.name}")
            
            with st.status(f"Processando {arquivo.name}...", expanded=True) as status:
                try:
                    st.write("Extraindo texto...")
                    texto_da_reuniao = extrair_texto_pdf(arquivo)
                    
                    if not texto_da_reuniao:
                        status.update(label=f"Falha: {arquivo.name} sem texto.", state="error")
                        continue
                    
                    st.write(f"Iniciando inferência com {modelo_id_real}...")
                    prompt_formatado = gerar_prompt_multiplas_atas(texto_da_reuniao)
                    
                    resposta = client.models.generate_content(
                        model=modelo_id_real,
                        contents=prompt_formatado
                    )
                    
                    # Extração de Metadados (Tokens) para o Dashboard
                    tokens_in = resposta.usage_metadata.prompt_token_count if resposta.usage_metadata else 0
                    tokens_out = resposta.usage_metadata.candidates_token_count if resposta.usage_metadata else 0
                    
                    # Salvando no session_state
                    st.session_state.resultados_processados[arquivo.name] = {
                        "texto_original": texto_da_reuniao,
                        "texto_gerado": resposta.text,
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out
                    }
                    
                    status.update(label="Concluído!", state="complete")
                    
                except Exception as e:
                    status.update(label="Erro", state="error")
                    st.error(f"Erro na API ({modelo_id_real}): {e}")
                    
    st.rerun() # Força a página a recarregar para exibir os resultados armazenados

# --- 7. Exibição, Edição e Governança (Lendo do State) ---
if st.session_state.resultados_processados:
    st.divider()
    st.header("🎯 Resultados, Validação e Exportação")
    
    for nome_arquivo, dados in st.session_state.resultados_processados.items():
        with st.expander(f"⚙️ Gerenciar: {nome_arquivo}", expanded=True):
            
            # --- Governança (Dashboard de Tokens) ---
            st.markdown("##### 📈 Consumo da API (Governança)")
            col_t1, col_t2, col_t3 = st.columns(3)
            col_t1.metric("Tokens de Entrada (Prompt)", f"{dados['tokens_in']:,}")
            col_t2.metric("Tokens de Saída (Resposta)", f"{dados['tokens_out']:,}")
            col_t3.metric("Custo Total de Tokens", f"{(dados['tokens_in'] + dados['tokens_out']):,}")
            st.caption("*Use esta métrica para monitorar a eficiência do modelo escolhido frente ao tamanho da transcrição.*")
            
            # --- Validação in-app ---
            st.markdown("##### 📝 Validação e Edição")
            st.info("Valide a ata abaixo. Qualquer alteração feita aqui será refletida diretamente no arquivo exportado.")
            
            texto_editado = st.text_area(
                label="Área de edição:",
                value=dados['texto_gerado'],
                height=400,
                key=f"edit_{nome_arquivo}",
                label_visibility="collapsed"
            )
            
            # --- Exportação Corporativa (.docx e .txt) ---
            st.markdown("##### 📥 Exportar Entregáveis")
            docx_file = criar_docx(texto_editado)
            
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button(
                    label="📄 Exportar para Word (.docx)",
                    data=docx_file,
                    file_name=f"Atas_Diagnostico_{nome_arquivo.replace('.pdf', '')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"docx_{nome_arquivo}",
                    use_container_width=True
                )
            with col_d2:
                st.download_button(
                    label="📝 Exportar Texto Bruto (.txt)",
                    data=texto_editado,
                    file_name=f"Atas_Diagnostico_{nome_arquivo.replace('.pdf', '')}.txt",
                    mime="text/plain",
                    key=f"txt_{nome_arquivo}",
                    use_container_width=True
                )