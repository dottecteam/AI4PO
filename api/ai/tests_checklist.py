"""Testes de regressão do checklist de conformidade (task #8-1).

Complementam a suíte principal: cada teste aqui trava uma correção da revisão
(regex, robustez, mensagens ou regra nova). SimpleTestCase: o checklist é
determinístico e não acessa o banco.
"""

import copy

from django.test import SimpleTestCase

from ai.checklist import resumo_validacao, validar_especificacao


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def especificacao_conforme() -> dict:
    """Especificação-modelo que satisfaz todas as regras do guia (sem erros
    e sem avisos)."""
    return {
        "epicos": [
            {
                "titulo": "Digitalizar o acompanhamento de solicitações",
                "descricao": "Experiência digital para clientes acompanharem solicitações.",
                "objetivo": "Reduzir contatos manuais e dar transparência ao andamento.",
                "escopo_macro": ["Consulta de solicitações", "Notificações"],
                "resultado_esperado": "Cliente acompanha solicitações sem atendimento manual.",
                "criterios_aceitacao": [
                    "Os dados alterados em um canal permanecem consistentes nos demais."
                ],
                "features": [
                    {
                        "titulo": "Consultar andamento de solicitações",
                        "descricao": "Cliente visualiza solicitações e o estágio atual.",
                        "objetivo": "Acompanhamento autônomo.",
                        "criterios_aceitacao": ["Listar somente solicitações autorizadas."],
                        "pbis": [
                            {
                                "titulo": "Consultar solicitação",
                                "historia": ("COMO UM cliente autenticado EU QUERO consultar "
                                             "os detalhes de uma solicitação PARA QUE eu possa "
                                             "acompanhar sua situação atual."),
                                "criterios_aceitacao": [],
                                "cenarios": [
                                    {"nome": "Exibir detalhes",
                                     "dado": "o cliente possua uma solicitação acessível",
                                     "quando": "selecionar a solicitação",
                                     "entao": "o sistema deve apresentar seus dados e status atual."},
                                    {"nome": "Acesso não autorizado",
                                     "dado": "a solicitação não pertença ao cliente",
                                     "quando": "ele tentar acessá-la",
                                     "entao": "o sistema deve impedir a consulta com erro de permissão."},
                                ],
                            },
                            {
                                "titulo": "Exportar histórico de solicitações",
                                "historia": ("COMO UM cliente autenticado EU QUERO exportar "
                                             "o histórico das minhas solicitações PARA QUE eu "
                                             "possa arquivá-las fora do sistema."),
                                "criterios_aceitacao": [],
                                "cenarios": [
                                    {"nome": "Exportar com filtros",
                                     "dado": "o cliente possua solicitações no período filtrado",
                                     "quando": "solicitar a exportação",
                                     "entao": "o sistema deve gerar o arquivo com os registros do período."},
                                    {"nome": "Nada no período",
                                     "dado": "não existirem solicitações no período",
                                     "quando": "solicitar a exportação",
                                     "entao": "o sistema deve informar a ausência de registros."},
                                ],
                            },
                        ],
                    }
                ],
            }
        ]
    }


def codigos(pendencias) -> set:
    """Códigos das regras que falharam."""
    return {p.regra for p in pendencias if not p.ok}


def mensagem_de(pendencias, regra: str) -> str:
    """Mensagem da primeira pendência reprovada da regra informada."""
    return next(p.mensagem for p in pendencias if p.regra == regra and not p.ok)


def cenarios_basicos(entao_alternativo: str, dado_principal: str = "o cliente esteja autenticado",
                     entao_principal: str = "o sistema deve exibir os dados.") -> list:
    """Dois cenários estruturados: caminho principal + um alternativo."""
    return [
        {"nome": "Principal", "dado": dado_principal,
         "quando": "consultar a solicitação", "entao": entao_principal},
        {"nome": "Alternativo", "dado": "ocorra uma condição alternativa",
         "quando": "consultar a solicitação", "entao": entao_alternativo},
    ]


class _BaseChecklistTests(SimpleTestCase):
    """Atalhos para alterar um nível da especificação-modelo."""

    def _epico(self, **alteracao):
        dados = especificacao_conforme()
        dados["epicos"][0].update(alteracao)
        return dados

    def _feature(self, **alteracao):
        dados = especificacao_conforme()
        dados["epicos"][0]["features"][0].update(alteracao)
        return dados

    def _pbi(self, **alteracao):
        dados = especificacao_conforme()
        dados["epicos"][0]["features"][0]["pbis"][0].update(alteracao)
        return dados


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

class ChecklistDetalheDeTelaTests(_BaseChecklistTests):
    def test_botao_singular_no_criterio_do_epico_gera_aviso(self):
        # "botão" (sem "campo"/"clique") precisa casar sozinho.
        dados = self._epico(criterios_aceitacao=["O botão deve abrir o relatório."])
        self.assertIn("EPICO-CRITERIO-MACRO", codigos(validar_especificacao(dados)))

    def test_botoes_plural_no_criterio_do_epico_gera_aviso(self):
        dados = self._epico(criterios_aceitacao=["Os botões devem abrir o relatório."])
        self.assertIn("EPICO-CRITERIO-MACRO", codigos(validar_especificacao(dados)))

    def test_campos_plural_gera_aviso(self):
        dados = self._epico(criterios_aceitacao=["Preencher os campos obrigatórios."])
        self.assertIn("EPICO-CRITERIO-MACRO", codigos(validar_especificacao(dados)))

    def test_detalhe_de_tela_no_escopo_macro_gera_aviso(self):
        dados = self._epico(escopo_macro=["Consulta de solicitações", "Aba de notificações"])
        resultado = resumo_validacao(dados)
        self.assertTrue(resultado["conforme"])  # aviso não bloqueia
        self.assertIn("EPICO-CRITERIO-MACRO", codigos(validar_especificacao(dados)))

    def test_criterio_do_epico_como_string_unica_e_avaliado(self):
        # str não pode ser iterada caractere a caractere (regra passaria muda).
        dados = self._epico(criterios_aceitacao="O botão deve abrir o relatório.")
        self.assertIn("EPICO-CRITERIO-MACRO", codigos(validar_especificacao(dados)))

    def test_detalhe_de_tela_no_criterio_da_feature_gera_aviso(self):
        dados = self._feature(criterios_aceitacao=["Exibir um link para o histórico."])
        resultado = resumo_validacao(dados)
        self.assertTrue(resultado["conforme"])  # §4.5: aviso, não bloqueia
        self.assertIn("FEATURE-CRITERIO-NIVEL", codigos(validar_especificacao(dados)))


class ChecklistInfinitivoTests(_BaseChecklistTests):
    def test_preposicao_por_nao_e_verbo(self):
        # `\w*por` aceitaria "por" sozinho.
        dados = self._pbi(titulo="Por usuário")
        self.assertIn("PBI-TITULO-INFINITIVO", codigos(validar_especificacao(dados)))

    def test_substantivo_terminado_em_por_reprova(self):
        dados = self._pbi(titulo="Vapor de água")
        self.assertIn("PBI-TITULO-INFINITIVO", codigos(validar_especificacao(dados)))

    def test_verbos_derivados_de_por_passam(self):
        for titulo in ("Propor orçamento", "Repor estoque", "Expor dados do cliente",
                       "Compor carrinho de compras"):
            with self.subTest(titulo=titulo):
                self.assertNotIn("PBI-TITULO-INFINITIVO",
                                 codigos(validar_especificacao(self._pbi(titulo=titulo))))

    def test_verbos_comuns_do_guia_passam(self):
        for titulo in ("Cadastrar usuário", "Editar perfil", "Consultar histórico",
                       "Filtrar resultados", "Recuperar senha", "Aprovar solicitação",
                       "Exportar dados", "Cancelar pedido"):
            with self.subTest(titulo=titulo):
                self.assertNotIn("PBI-TITULO-INFINITIVO",
                                 codigos(validar_especificacao(self._pbi(titulo=titulo))))

    def test_substantivos_da_lista_de_recusa_reprovam(self):
        for titulo in ("Celular do cliente", "Mulher cadastrada", "Lugar de entrega"):
            with self.subTest(titulo=titulo):
                self.assertIn("PBI-TITULO-INFINITIVO",
                              codigos(validar_especificacao(self._pbi(titulo=titulo))))

    def test_titulo_nao_textual_reprova_sem_quebrar(self):
        dados = self._pbi(titulo=123)
        self.assertIn("PBI-TITULO-INFINITIVO", codigos(validar_especificacao(dados)))


class ChecklistTermosVagosTests(_BaseChecklistTests):
    def test_flexoes_de_numero_e_genero_sao_detectadas(self):
        for texto in ("Os resultados devem ser rápidos.", "As telas devem ser intuitivas.",
                      "Os dados devem estar corretos.", "A tela deve ser bonita."):
            with self.subTest(texto=texto):
                dados = self._epico(descricao=texto)
                self.assertIn("GERAL-SEM-TERMO-VAGO", codigos(validar_especificacao(dados)))

    def test_requisito_legal_nao_e_termo_vago(self):
        dados = self._epico(descricao="Atender ao requisito legal de retenção de dados.")
        self.assertNotIn("GERAL-SEM-TERMO-VAGO", codigos(validar_especificacao(dados)))

    def test_mensagem_indica_onde_esta_o_termo_vago(self):
        dados = self._feature(criterios_aceitacao=["A tela deve ser bonita."])
        mensagem = mensagem_de(validar_especificacao(dados), "GERAL-SEM-TERMO-VAGO")
        self.assertIn("bonita", mensagem)
        self.assertIn("Feature 'Consultar andamento de solicitações'", mensagem)


class ChecklistCoberturaDeErrosTests(_BaseChecklistTests):
    def _cobertura_ok(self, entao_alternativo: str) -> bool:
        dados = self._pbi(cenarios=cenarios_basicos(entao_alternativo))
        return "PBI-COBERTURA-ERROS" not in codigos(validar_especificacao(dados))

    def test_flexoes_de_estados_de_falha_sao_reconhecidas(self):
        casos = [
            "o sistema deve informar erros de validação.",
            "o sistema deve rejeitar dados inválidos.",
            "o sistema deve informar permissão negada.",
            "o sistema deve informar que o registro está bloqueado.",
            "o sistema deve informar que a sessão está expirada.",
            "o sistema deve informar falhas de integração.",
            "o sistema deve informar que o campo obrigatório está vazio.",
        ]
        for caso in casos:
            with self.subTest(caso=caso):
                self.assertTrue(self._cobertura_ok(caso))

    def test_subjuntivo_impeca_e_reconhecido(self):
        self.assertTrue(self._cobertura_ok("o sistema impeça o acesso."))

    def test_impedir_no_infinitivo_e_reconhecido(self):
        self.assertTrue(self._cobertura_ok("o sistema deve impedir o acesso."))

    def test_formato_e_sessao_ativa_nao_contam_como_erro(self):
        # Palavras do caminho feliz não podem mascarar a falta de cenário de erro.
        dados = self._pbi(cenarios=cenarios_basicos(
            entao_alternativo="o sistema deve gerar o arquivo no formato PDF.",
            dado_principal="a sessão do cliente esteja ativa"))
        self.assertIn("PBI-COBERTURA-ERROS", codigos(validar_especificacao(dados)))

    def test_cenario_unico_gera_aviso_mesmo_com_erro(self):
        dados = self._pbi(cenarios=[
            {"nome": "Erro", "dado": "o serviço esteja indisponível",
             "quando": "consultar", "entao": "o sistema deve informar o erro."},
        ])
        resultado = resumo_validacao(dados)
        self.assertTrue(resultado["conforme"])  # aviso não bloqueia
        self.assertIn("PBI-COBERTURA-ERROS", codigos(validar_especificacao(dados)))


# ---------------------------------------------------------------------------
# Cenários
# ---------------------------------------------------------------------------

class ChecklistCenariosEmTextoTests(_BaseChecklistTests):
    def test_varios_cenarios_no_mesmo_texto_contam_separadamente(self):
        dados = self._pbi(cenarios=[], criterios_aceitacao=[
            "DADO que o cliente tenha solicitações QUANDO abrir a lista ENTÃO o sistema "
            "deve exibi-las. DADO que a sessão tenha expirado QUANDO abrir a lista "
            "ENTÃO o sistema deve pedir novo login."
        ])
        achados = codigos(validar_especificacao(dados))
        self.assertNotIn("PBI-CRITERIO-CENARIO", achados)
        self.assertNotIn("PBI-COBERTURA-ERROS", achados)  # 2 cenários + estado expirado

    def test_erro_dentro_do_entao_do_cenario_em_texto_e_encontrado(self):
        dados = self._pbi(cenarios=[], criterios_aceitacao=[
            "DADO que haja solicitações QUANDO abrir a lista ENTÃO o sistema deve exibi-las.",
            "DADO que o cliente esteja autenticado QUANDO abrir a lista "
            "ENTÃO o sistema deve impedir o acesso indevido.",
        ])
        self.assertNotIn("PBI-COBERTURA-ERROS", codigos(validar_especificacao(dados)))

    def test_texto_livre_sem_marcadores_nao_e_cenario(self):
        dados = self._pbi(cenarios=[], criterios_aceitacao=["O sistema deve listar as solicitações."])
        achados = codigos(validar_especificacao(dados))
        self.assertIn("PBI-CRITERIO-CENARIO", achados)
        self.assertNotIn("PBI-CAMPO-CRITERIOS", achados)  # há critério, só não é cenário

    def test_cenario_incompleto_cita_o_nome_do_cenario(self):
        dados = self._pbi(cenarios=[
            {"nome": "Sem resultado", "dado": "cliente autenticado", "quando": "consultar"},
            {"nome": "Principal", "dado": "cliente autenticado", "quando": "consultar",
             "entao": "sistema exibe dados"},
        ])
        pendencias = validar_especificacao(dados)
        self.assertIn("PBI-CENARIO-COMPLETEZA", codigos(pendencias))
        self.assertIn("Sem resultado", mensagem_de(pendencias, "PBI-CENARIO-COMPLETEZA"))

    def test_cenario_vazio_nao_conta_para_a_cobertura(self):
        # Dois dicts vazios não podem "inflar" a contagem mínima de cenários.
        dados = self._pbi(criterios_aceitacao=[], cenarios=[{}, {}])
        achados = codigos(validar_especificacao(dados))
        self.assertIn("PBI-CAMPO-CRITERIOS", achados)
        self.assertIn("PBI-COBERTURA-ERROS", achados)
        self.assertNotIn("PBI-CENARIO-COMPLETEZA", achados)


# ---------------------------------------------------------------------------
# Regras de Feature e de duplicação
# ---------------------------------------------------------------------------

class ChecklistFeatureCorrecoesTests(_BaseChecklistTests):
    def test_feature_sem_pbis_nao_dispara_aviso_de_pbi_unico(self):
        achados = codigos(validar_especificacao(self._feature(pbis=[])))
        self.assertIn("FEATURE-DECOMPOSICAO-PBIS", achados)
        self.assertNotIn("FEATURE-PBIS-INSUFICIENTES", achados)

    def test_feature_com_um_pbi_dispara_apenas_o_aviso(self):
        dados = especificacao_conforme()
        feature = dados["epicos"][0]["features"][0]
        feature["pbis"] = feature["pbis"][:1]
        achados = codigos(validar_especificacao(dados))
        self.assertIn("FEATURE-PBIS-INSUFICIENTES", achados)
        self.assertNotIn("FEATURE-DECOMPOSICAO-PBIS", achados)

    def test_feature_com_dois_pbis_nao_dispara_aviso(self):
        self.assertNotIn("FEATURE-PBIS-INSUFICIENTES",
                         codigos(validar_especificacao(especificacao_conforme())))

    def test_titulo_generico_de_feature_gera_aviso_e_nao_bloqueia(self):
        for titulo in ("Ajustes no cadastro", "Melhorias gerais"):
            with self.subTest(titulo=titulo):
                dados = self._feature(titulo=titulo)
                self.assertTrue(resumo_validacao(dados)["conforme"])
                self.assertIn("FEATURE-TITULO-NAO-GENERICO", codigos(validar_especificacao(dados)))

    def test_feature_nao_exige_vinculo_artificial_com_epico_sem_titulo(self):
        # O vínculo é estrutural (aninhamento); não deve duplicar o erro do Épico.
        dados = self._epico(titulo="")
        achados = codigos(validar_especificacao(dados))
        self.assertIn("EPICO-CAMPO-TITULO", achados)
        self.assertFalse([c for c in achados if c.startswith("FEATURE-VINCULO")])


class ChecklistDuplicacaoTests(_BaseChecklistTests):
    def test_especificacao_distinta_nao_gera_aviso_de_duplicacao(self):
        self.assertNotIn("GERAL-DUPLICACAO-NIVEIS",
                         codigos(validar_especificacao(especificacao_conforme())))

    def test_feature_com_descricao_identica_a_do_epico(self):
        dados = especificacao_conforme()
        dados["epicos"][0]["features"][0]["descricao"] = dados["epicos"][0]["descricao"]
        self.assertIn("GERAL-DUPLICACAO-NIVEIS", codigos(validar_especificacao(dados)))

    def test_feature_com_descricao_quase_identica_a_do_epico(self):
        dados = especificacao_conforme()
        dados["epicos"][0]["features"][0]["descricao"] = (
            "Experiência digital para os clientes acompanharem solicitações!")
        self.assertIn("GERAL-DUPLICACAO-NIVEIS", codigos(validar_especificacao(dados)))

    def test_feature_com_objetivo_identico_ao_do_epico(self):
        dados = especificacao_conforme()
        dados["epicos"][0]["features"][0]["objetivo"] = dados["epicos"][0]["objetivo"]
        self.assertIn("GERAL-DUPLICACAO-NIVEIS", codigos(validar_especificacao(dados)))

    def test_feature_com_criterio_identico_ao_do_epico(self):
        dados = especificacao_conforme()
        dados["epicos"][0]["features"][0]["criterios_aceitacao"] = list(
            dados["epicos"][0]["criterios_aceitacao"])
        self.assertIn("GERAL-DUPLICACAO-NIVEIS", codigos(validar_especificacao(dados)))

    def test_pbi_com_criterio_identico_ao_da_feature(self):
        dados = especificacao_conforme()
        feature = dados["epicos"][0]["features"][0]
        feature["pbis"][0]["criterios_aceitacao"] = list(feature["criterios_aceitacao"])
        pendencias = validar_especificacao(dados)
        self.assertIn("GERAL-DUPLICACAO-NIVEIS", codigos(pendencias))
        self.assertIn("Consultar solicitação",
                      mensagem_de(pendencias, "GERAL-DUPLICACAO-NIVEIS"))

    def test_duplicacao_e_aviso_e_nao_bloqueia(self):
        dados = especificacao_conforme()
        dados["epicos"][0]["features"][0]["descricao"] = dados["epicos"][0]["descricao"]
        self.assertTrue(resumo_validacao(dados)["conforme"])


class ChecklistImplementacaoCorrecoesTests(_BaseChecklistTests):
    def test_termos_de_negocio_no_epico_nao_disparam(self):
        dados = self._epico(objetivo=("Permitir escolher o método de pagamento e a "
                                      "função do usuário na classe de atendimento."))
        self.assertNotIn("GERAL-SEM-DETALHE-IMPLEMENTACAO", codigos(validar_especificacao(dados)))

    def test_implementacao_na_feature_gera_aviso(self):
        dados = self._feature(descricao="Expor um endpoint REST para consulta.")
        resultado = resumo_validacao(dados)
        self.assertTrue(resultado["conforme"])
        self.assertIn("GERAL-SEM-DETALHE-IMPLEMENTACAO", codigos(validar_especificacao(dados)))

    def test_implementacao_no_pbi_e_ignorada(self):
        dados = self._pbi(cenarios=cenarios_basicos(
            "o sistema deve informar o erro.",
            entao_principal="o sistema deve exibir o resumo em tabela."))
        self.assertNotIn("GERAL-SEM-DETALHE-IMPLEMENTACAO", codigos(validar_especificacao(dados)))


# ---------------------------------------------------------------------------
# Mensagens, códigos e contrato do resumo
# ---------------------------------------------------------------------------

class ChecklistMensagensTests(_BaseChecklistTests):
    def test_rotulo_do_epico_e_legivel(self):
        dados = self._epico(descricao="Interface intuitiva para o cliente.")
        mensagem = mensagem_de(validar_especificacao(dados), "GERAL-SEM-TERMO-VAGO")
        self.assertIn("Épico 'Digitalizar o acompanhamento de solicitações'", mensagem)
        self.assertNotIn("EPICO", mensagem)

    def test_excesso_de_ocorrencias_e_resumido(self):
        dados = especificacao_conforme()
        epico = dados["epicos"][0]
        modelo = epico["features"][0]
        epico["features"] = []
        for letra in "ABCDEF":
            feature = copy.deepcopy(modelo)
            feature["titulo"] = f"Consultar andamento {letra}"
            feature["criterios_aceitacao"] = [f"A tela {letra} deve ser bonita."]
            epico["features"].append(feature)
        mensagem = mensagem_de(validar_especificacao(dados), "GERAL-SEM-TERMO-VAGO")
        self.assertIn("(+2)", mensagem)

    def test_codigos_de_regra_sao_ascii(self):
        dados = self._epico(objetivo="", descricao="")
        for p in validar_especificacao(dados):
            with self.subTest(regra=p.regra):
                self.assertTrue(p.regra.isascii())
        self.assertIn("EPICO-CAMPO-OBJETIVO", codigos(validar_especificacao(dados)))

    def test_mensagem_vazia_para_regras_aprovadas(self):
        for p in validar_especificacao(especificacao_conforme()):
            if p.ok:
                self.assertEqual(p.mensagem, "", msg=p.regra)

    def test_erro_bloqueia_a_conformidade_e_aparece_formatado(self):
        dados = self._pbi(historia="O cliente quer ver a solicitação.")
        resultado = resumo_validacao(dados)
        self.assertFalse(resultado["conforme"])
        self.assertTrue(any(e.startswith("[pbi] Consultar solicitação:")
                            for e in resultado["erros"]), msg=str(resultado["erros"]))

    def test_resumo_serializa_pendencias_como_dicts(self):
        resultado = resumo_validacao(especificacao_conforme())
        self.assertTrue(resultado["pendencias"])
        chaves = {"regra", "nivel", "item", "ok", "mensagem", "severidade"}
        for pendencia in resultado["pendencias"]:
            self.assertIsInstance(pendencia, dict)
            self.assertEqual(set(pendencia), chaves)

    def test_avisos_nao_entram_em_erros(self):
        dados = self._epico(descricao="Interface intuitiva para o cliente.")
        resultado = resumo_validacao(dados)
        self.assertTrue(resultado["conforme"])
        self.assertEqual(resultado["erros"], [])
        self.assertTrue(resultado["avisos"])


# ---------------------------------------------------------------------------
# Robustez
# ---------------------------------------------------------------------------

class ChecklistRobustezTests(_BaseChecklistTests):
    def test_valores_nao_textuais_em_cenarios_nao_quebram(self):
        dados = self._pbi(cenarios=[
            {"nome": 7, "dado": 3, "quando": None, "entao": ["x"]},
            {},
            "texto solto",
            None,
        ], criterios_aceitacao=[1, None, {"a": "b"}])
        self.assertTrue(validar_especificacao(dados))

    def test_titulos_nao_textuais_nao_quebram(self):
        dados = especificacao_conforme()
        epico = dados["epicos"][0]
        epico["titulo"] = 123
        epico["features"][0]["titulo"] = None
        epico["features"][0]["pbis"][0]["titulo"] = ["lista"]
        self.assertTrue(validar_especificacao(dados))

    def test_itens_fora_de_estrutura_sao_ignorados(self):
        dados = especificacao_conforme()
        dados["epicos"].append("epico solto")
        dados["epicos"][0]["features"].append(42)
        dados["epicos"][0]["features"][0]["pbis"].append(["lista"])
        resultado = resumo_validacao(dados)
        self.assertTrue(resultado["conforme"], msg=str(resultado["erros"]))

    def test_features_como_string_equivale_a_ausencia(self):
        dados = self._epico(features="não é lista")
        self.assertIn("EPICO-DECOMPOSICAO-FEATURES", codigos(validar_especificacao(dados)))

    def test_epicos_como_dict_equivale_a_ausencia(self):
        dados = {"epicos": {"titulo": "Épico solto"}}
        self.assertIn("GERAL-TEM-EPICO", codigos(validar_especificacao(dados)))

    def test_especificacao_sem_a_chave_epicos(self):
        self.assertIn("GERAL-TEM-EPICO", codigos(validar_especificacao({})))