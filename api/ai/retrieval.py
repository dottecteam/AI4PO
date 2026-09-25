import numpy as np

from ai.extraction import extrair_texto
from ai.indexing import dividir_em_chunks, gerar_embeddings

from ai.models import ChunkDoc
from pgvector.django import CosineDistance

def responder_com_documento(texto_doc, pergunta):
    # 'pergunta' aqui é a palavra-chave ou frase que a IA decidiu usar para filtrar o documento
    chunks = dividir_em_chunks(texto_doc)
    
    if not chunks:
        return "Aviso: O documento fornecido está vazio ou não contém texto legível."
        
    print(f"\n[DEBUG IN-MEMORY RAG] {len(chunks)} chunks gerados do documento anexado.")
    
    # Gera vetores do documento e do termo de busca
    vetores = np.array(gerar_embeddings([c.texto_para_embedding for c in chunks]))
    vetores_pergunta = gerar_embeddings([pergunta])
    
    if not vetores_pergunta:
        return "Erro: Falha ao gerar vetor de busca para analisar o documento."
        
    vetor_pergunta = np.array(vetores_pergunta[0])
    
    # Cálculo de similaridade de cosseno usando NumPy
    sims = vetores @ vetor_pergunta / (
        np.linalg.norm(vetores, axis=1) * np.linalg.norm(vetor_pergunta)
    )
    
    # Pega os 4 trechos mais relevantes (protegido caso o documento seja menor que 4 chunks)
    k = min(4, len(chunks))
    top_k = np.argsort(sims)[::-1][:k]
    
    # Retorna APENAS os dados brutos para o Ollama ler como ferramenta
    contexto = "\n---\n".join(chunks[i].texto_para_embedding for i in top_k)
    
    return f"Conteúdo relevante extraído do documento enviado pelo usuário:\n{contexto}"

# ai/retrieval.py

def responder_com_base_vetorial(pergunta, projeto_id=None):
    # 'pergunta' agora é apenas a palavra-chave gerada pela IA (ex: "projetos")
    vetores_pergunta = gerar_embeddings([pergunta])
    
    if not vetores_pergunta:
         # Fallback amigável para o Agent ler caso falhe
        return "Não foi possível buscar no banco de dados. Avise o usuário sobre o erro."
        
    vetor_pergunta = vetores_pergunta[0]
    
    # Busca no banco usando o pgvector
    query = ChunkDoc.objects.order_by(CosineDistance('embedding', vetor_pergunta))
    
    if projeto_id:
        query = query.filter(projeto_id=projeto_id)
        
    top_chunks = query[:4]
    
    print("\n" + "="*50)
    print(f"[DEBUG RAG] Buscando contexto com o termo: '{pergunta}'")
    print(f"[DEBUG RAG] {len(top_chunks)} chunks encontrados.")
    print("="*50 + "\n")
    
    # Concatena o conteúdo dos chunks
    contexto = "\n---\n".join(c.conteudo for c in top_chunks)
    
    # Se não achar nada, avisa a IA em texto puro
    if not contexto.strip():
        return "Nenhum documento ou contexto encontrado para este termo no banco de dados."
    
    # Retorna APENAS os dados para o Ollama ler como ferramenta, sem forçar um prompt
    return f"Contexto encontrado nos documentos:\n{contexto}"