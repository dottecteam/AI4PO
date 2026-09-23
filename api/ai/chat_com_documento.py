import numpy as np

from ai.extraction import extrair_texto
from ai.indexing import dividir_em_chunks, gerar_embeddings


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