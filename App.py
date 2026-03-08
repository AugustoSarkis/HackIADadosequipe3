import streamlit as st
import os
from google import genai
from PyPDF2 import PdfReader

st.set_page_config(page_title="Assistente de Diagnóstico0", page_icon="📝", layout="centered")

# Puxa o Secret do Streamlit e injeta no ambiente do servidor
try:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    client = genai.Client()
except KeyError:
    st.error("🚨 Chave de API não encontrada nos Secrets do Streamlit Cloud.")
    st.stop()

# ... (resto do seu código, lembrando de usar client.models.generate_content) ...

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
                Imagine que você é um revisor técnico.

Vou te enviar anotações brutas de uma reunião comercial. Elas podem estar desorganizadas, incompletas, informais ou fora de ordem.

Sua tarefa é interpretar essas anotações e transformá-las em uma ata executiva curta, como um consultor faria após uma reunião com cliente.

A ata deve destilar apenas o que é estrategicamente relevante para o avanço comercial do projeto.

Estruture obrigatoriamente a resposta nos seguintes tópicos, sem subtópicos e sem bullet points:

Rapport:



Contexto humano da reunião e nível de abertura do contato. Inclua elementos que ajudem no relacionamento comercial (clima da conversa, interesse demonstrado, contexto da empresa ou momento interno relevante).

Com quem eu estou falando:



Cargo da pessoa, área de atuação e qual é seu papel no processo decisório (decision maker, influenciador, gatekeeper ou ponte para outras áreas).

O que o projeto está se encaminhando para ser (Solução + Resumo rápido):



Síntese da oportunidade de projeto identificada. Descreva de forma clara qual problema pode ser resolvido e qual tipo de solução pode ser proposta.

Fatores cruciais de mapeamento:



Descreva apenas os elementos que impactam diretamente a viabilidade do projeto: sistemas existentes, estrutura de dados, ferramentas utilizadas, cloud, processos atuais, nível de maturidade digital, limitações técnicas e principais dores operacionais.

Próximo passo claro:



Próxima ação comercial objetiva (ex.: envio de proposta, assinatura de NDA, conexão com outro time, nova reunião ou validação interna do cliente).

Regras importantes:



Escreva em texto corrido, sem listas.

A ata deve ser curta, clara e objetiva.

Priorize dor do cliente, maturidade digital e oportunidade de projeto.

Elimine informações irrelevantes que não ajudam a avançar comercialmente.

Quando necessário, reorganize e interprete as anotações para torná-las claras e estratégicas.

Se houver múltiplas informações técnicas ou ferramentas, resuma sem perder o essencial.

Agora transforme as seguintes anotações na ata padrão.
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