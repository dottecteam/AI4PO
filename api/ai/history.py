def carregar_historico(conversa, max_msgs=8, max_chars=6000):
    """
    Janela deslizante: as N mensagens mais recentes AINDA NÃO resumidas, limitadas
    também por tamanho total (o tamanho do prompt é o que pesa no Ollama).
    O que veio antes de `conversa.resumido_ate_id` está em `conversa.resumo`,
    que a view injeta no prompt de sistema.
    Deve ser chamada ANTES de salvar a mensagem atual, que é anexada à parte.
    """
    historico = []
    total = 0
    recentes = (
        conversa.mensagens
        .filter(id__gt=conversa.resumido_ate_id)
        .order_by("-id")[:max_msgs]
    )
    for m in recentes:
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