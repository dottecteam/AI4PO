def carregar_historico(conversa, max_msgs=8, max_chars=6000):
    """
    Janela deslizante: as N mensagens mais recentes da conversa, limitadas
    também por tamanho total (o tamanho do prompt é o que pesa no Ollama).
    Deve ser chamada ANTES de salvar a mensagem atual, que é anexada à parte.
    """
    historico = []
    total = 0
    for m in conversa.mensagens.order_by("-id")[:max_msgs]:
        conteudo = m.conteudo
        if m.anexo_nome:
            # o texto do anexo não é persistido; deixa ao menos o rastro dele
            conteudo += f"\n[Anexo enviado nesta mensagem: {m.anexo_nome}]"
        total += len(conteudo)
        if total > max_chars:
            break
        historico.append({"role": m.papel, "content": conteudo})

    historico.reverse()  # ordem cronológica

    # A janela nunca deve abrir com resposta do assistente sem a pergunta
    while historico and historico[0]["role"] != "user":
        historico.pop(0)

    return historico