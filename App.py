'''O codigo em PY que sera usado para se conectar com strimilish e autmatizar a producao das ATs'''
import google.generativeai as genai
import time

CHAVE_API = "COLOQUE_SUA_CHAVE_AQUI"
genai.configure(api_key=CHAVE_API)

caminho_do_arquivo = "relatorio_financeiro.pdf"
print(f"Fazendo upload de {caminho_do_arquivo}...")

arquivo_enviado = genai.upload_file(path=caminho_do_arquivo, display_name="Relatorio Financeiro Q3")

while arquivo_enviado.state.name == "PROCESSING":
    print("Processando arquivo no servidor do Google...")
    time.sleep(2)
    # Atualiza o status do arquivo
    arquivo_enviado = genai.get_file(arquivo_enviado.name)

if arquivo_enviado.state.name == "FAILED":
    raise ValueError("Erro no processamento do arquivo.")
    
print(f"Upload concluído! URI do arquivo: {arquivo_enviado.uri}")

# Flash é ótimo, mas para PDFs complexos de dezenas de páginas, o Pro pode ser mais preciso
modelo = genai.GenerativeModel(model_name="gemini-1.5-flash")

prompt = """
Analise este relatório financeiro e extraia as seguintes informações:
1. Qual foi a receita total do trimestre?
2. Quais foram os principais custos operacionais citados?
Por favor, seja direto.
"""

print("Analisando o documento...\n")

resposta = modelo.generate_content([arquivo_enviado, prompt])

