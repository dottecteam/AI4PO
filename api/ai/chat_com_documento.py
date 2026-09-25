import numpy as np

from ai.extraction import extrair_texto
from ai.indexing import dividir_em_chunks, gerar_embeddings

from ai.models import ChunkDoc
from pgvector.django import CosineDistance

def responder_com_documento(texto_doc, pergunta):
    chunks = dividir_em_chunks(texto_doc)
    print(f"[DEBUG] {len(chunks)} chunks gerados:")
    for c in chunks:
        print(f"  - {c.caminho_heading}: {c.texto[:60]!r}")

    vetores = np.array(gerar_embeddings([c.texto_para_embedding for c in chunks]))
    vetor_pergunta = np.array(gerar_embeddings([pergunta])[0])

    sims = vetores @ vetor_pergunta / (
        np.linalg.norm(vetores, axis=1) * np.linalg.norm(vetor_pergunta)
    )
    top_k = np.argsort(sims)[::-1][:4]
    print(f"[DEBUG] top_k escolhidos: {[chunks[i].caminho_heading for i in top_k]}")

    contexto = "\n---\n".join(chunks[i].texto_para_embedding for i in top_k)
    return f"Contexto:\n{contexto}\n\nPergunta: {pergunta}"


def responder_com_base_vetorial(pergunta, projeto_id=None):
    # Transforma a pergunta do PO em um vetor usando o mesmo modelo (nomic-embed-text)
    vetores_pergunta = gerar_embeddings([pergunta])
    
    if not vetores_pergunta:
        return pergunta # Fallback de segurança se falhar a geração
        
    vetor_pergunta = vetores_pergunta[0]

    # Busca no banco usando o pgvector (ordena pela menor distância de cosseno)
    query = ChunkDoc.objects.order_by(CosineDistance('embedding', vetor_pergunta))

    # Filtra pelo projeto específico, se o ID for passado (muito recomendado para não misturar contextos)
    if projeto_id:
        query = query.filter(projeto_id=projeto_id)

    # Pega os 4 chunks mais parecidos com a pergunta (top_k = 4)
    top_chunks = query[:4]

    # --- INÍCIO DOS PRINTS DE DEBUG ---
    print("\n" + "="*50)
    print(f"[DEBUG RAG] Buscando contexto para a pergunta: '{pergunta}'")
    print(f"[DEBUG RAG] {len(top_chunks)} chunks encontrados no banco de dados.")
    
    for i, chunk in enumerate(top_chunks):
        # O [:100] limita o print aos primeiros 100 caracteres de cada chunk para não poluir demais
        print(f"  -> Chunk {i+1} (ID: {chunk.id}): {chunk.conteudo[:100]}...")
    # --- FIM DOS PRINTS ---

    # Concatena o conteúdo dos chunks encontrados para formar o contexto
    contexto = "\n---\n".join(c.conteudo for c in top_chunks)
    
    # Monta o prompt final
    prompt_final = f"Contexto dos documentos do projeto:\n{contexto}\n\nCom base exclusivamente no contexto acima, responda à pergunta do PO: {pergunta}"

    print("\n[DEBUG RAG] PROMPT FINAL ENVIADO AO OLLAMA:")
    print(prompt_final)
    print("="*50 + "\n")
    
    return prompt_final