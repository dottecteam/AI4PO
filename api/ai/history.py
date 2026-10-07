def carregar_historico(conversa, max_msgs=8, max_chars=6000):
    """
    Janela deslizante: controla quanto do histórico vai pro prompt do Ollama.
    Limitado por quantidade E por tamanho total, é o tamanho do prompt que
    pesa na performance, não o banco.
    """
    historico = []
    total = 0
    for m in conversa.mensagens.order_by("-id")[:max_msgs]:
        total += len(m.conteudo)
        if total > max_chars:
            break
        historico.append({"role": m.papel, "content": m.conteudo})
    return historico[::-1]  # devolve em ordem cronológica