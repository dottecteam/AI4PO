"""Ações do chat: cadastros pedidos em linguagem natural e perguntas de esclarecimento.

Fluxo (o modelo nunca grava nada sozinho):
1. O modelo escolhe uma ferramenta (cadastrar_* ou perguntar_ao_usuario).
2. O servidor valida os argumentos com as MESMAS regras das telas. Faltou dado
   ou algo está inválido -> devolve uma pergunta objetiva ao usuário.
3. Dados válidos -> devolve uma ação "pendente", exibida como card com
   Confirmar/Cancelar. Só a confirmação (confirmar_acao) cria o registro, e
   ela revalida tudo e confere a permissão de novo.
"""
import logging
import secrets
import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from atividades.servico import registrar
from projects.models import Projeto
from users.models import Competencia, Funcionario
from users.views import validar_dados as validar_login
from users.views_funcionarios import validar_competencia, validar_profissional

logger = logging.getLogger(__name__)

User = get_user_model()

STATUS_PROJETO = [valor for valor, _ in Projeto.Status.choices]
TITULO_PROJETO_MAX = 255
MAX_OPCOES = 5

ROTULOS = {
    "projeto": "projeto",
    "profissional": "profissional",
    "competencia": "competência",
    "usuario": "login de PO",
}

# ==========================================
# FERRAMENTAS
# ==========================================
FERRAMENTAS_ACOES = [
    {
        "type": "function",
        "function": {
            "name": "cadastrar_projeto",
            "description": "Prepara o cadastro de um novo projeto do usuário logado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string", "description": "Nome do projeto."},
                    "descricao": {"type": "string", "description": "Do que se trata o projeto."},
                    "status": {"type": "string", "enum": STATUS_PROJETO, "description": "Padrão: Rascunho."},
                },
                "required": ["titulo", "descricao"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cadastrar_profissional",
            "description": "Prepara o cadastro de um profissional (membro da equipe) com suas competências.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string"},
                    "email": {"type": "string"},
                    "competencias": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Nomes das competências (ex.: Python, React).",
                    },
                },
                "required": ["nome", "email", "competencias"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cadastrar_competencia",
            "description": "Prepara o cadastro de uma competência no catálogo.",
            "parameters": {
                "type": "object",
                "properties": {"nome": {"type": "string"}},
                "required": ["nome"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cadastrar_usuario",
            "description": "Prepara o cadastro de um login de Product Owner na plataforma (apenas administradores).",
            "parameters": {
                "type": "object",
                "properties": {"nome": {"type": "string"}, "email": {"type": "string"}},
                "required": ["nome", "email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "perguntar_ao_usuario",
            "description": (
                "Faz UMA pergunta objetiva ao usuário quando falta informação ou o pedido é ambíguo. "
                "Use opções curtas quando houver poucas respostas possíveis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pergunta": {"type": "string"},
                    "opcoes": {"type": "array", "items": {"type": "string"}, "description": "Até 5 opções curtas."},
                },
                "required": ["pergunta"],
            },
        },
    },
]

PROMPT_ACOES = """Você é o assistente de cadastros da plataforma AI4PO. Ajude o usuário a cadastrar projetos, profissionais, competências e logins de PO.

Regras:
- Responda SEMPRE chamando exatamente UMA ferramenta.
- Use cadastrar_projeto, cadastrar_profissional, cadastrar_competencia ou cadastrar_usuario quando o usuário quiser cadastrar algo e você já tiver as informações obrigatórias.
- NUNCA invente dados (nome, e-mail, descrição, competências). Se algo obrigatório não foi dito pelo usuário nesta conversa, chame perguntar_ao_usuario pedindo exatamente o que falta, em uma única pergunta.
- Se o pedido for ambíguo (ex.: não está claro se é projeto ou profissional), chame perguntar_ao_usuario com opções curtas.
- "opcoes" são RESPOSTAS prontas que o usuário pode clicar (ex.: "Projeto", "Profissional"; "Rascunho", "Ativo"). Para dados livres (nome, e-mail, descrição, competências) NÃO envie opções; nunca use nomes de campos como opções.
- Obrigatórios: projeto = título e descrição (status opcional: Rascunho, Ativo ou Inativo); profissional = nome, e-mail e ao menos uma competência; competência = nome; login de PO = nome e e-mail (a senha é gerada pelo sistema; nunca peça senha).
- Use as respostas anteriores do usuário nesta conversa para completar os dados.
- Escreva em português."""


# ==========================================
# VALIDAÇÃO (sem gravar nada)
# ==========================================
def _texto(valor):
    return " ".join(valor.split()) if isinstance(valor, str) else ""


def _lista_de_textos(valor):
    if isinstance(valor, str):
        valor = valor.split(",")
    if not isinstance(valor, list):
        return []
    vistos, itens = set(), []
    for item in valor:
        nome = _texto(item) if isinstance(item, str) else ""
        if nome and nome.casefold() not in vistos:
            vistos.add(nome.casefold())
            itens.append(nome)
    return itens


def _primeiras(erros):
    return [mensagens[0] for mensagens in erros.values() if mensagens]


def _validar_projeto(args, usuario):
    titulo = _texto(args.get("titulo"))
    descricao = (args.get("descricao") or "").strip() if isinstance(args.get("descricao"), str) else ""
    status = _texto(args.get("status")).capitalize() or Projeto.Status.RASCUNHO.value
    faltando, problemas, opcoes = [], [], []
    if not titulo:
        faltando.append("o título do projeto")
    elif len(titulo) > TITULO_PROJETO_MAX:
        problemas.append(f"O título pode ter no máximo {TITULO_PROJETO_MAX} caracteres.")
    if not descricao:
        faltando.append("uma breve descrição do projeto")
    if status not in STATUS_PROJETO:
        problemas.append("O status precisa ser Rascunho, Ativo ou Inativo.")
        opcoes = STATUS_PROJETO
    dados = {"titulo": titulo, "descricao": descricao, "status": status}
    return dados, faltando, problemas, opcoes


def _validar_profissional(args, usuario):
    nome = _texto(args.get("nome"))
    email = _texto(args.get("email")).lower()
    nomes_comp = _lista_de_textos(args.get("competencias"))
    faltando, problemas = [], []

    if not nome:
        faltando.append("o nome do profissional")
    if not email:
        faltando.append("o e-mail do profissional")
    if not nomes_comp:
        faltando.append("ao menos uma competência")

    if nome or email:
        _, erros = validar_profissional({"nome": nome, "email": email, "competencias": [0]})
        erros.pop("competencias", None)
        if not nome:
            erros.pop("nome", None)
        if not email:
            erros.pop("email", None)
        problemas.extend(_primeiras(erros))

    existentes, novas = [], []
    for item in nomes_comp:
        achada = Competencia.objects.filter(nome__iexact=item).first()
        if achada:
            existentes.append(achada.nome)
        else:
            novas.append(item)

    dados = {"nome": nome, "email": email, "competencias": existentes, "competencias_novas": novas}
    return dados, faltando, problemas, []


def _validar_competencia(args, usuario):
    nome, erros = validar_competencia({"nome": args.get("nome")})
    faltando = ["o nome da competência"] if not nome else []
    problemas = [] if not nome else _primeiras(erros)
    return {"nome": nome}, faltando, problemas, []


def _validar_usuario(args, usuario):
    nome = _texto(args.get("nome"))
    email = _texto(args.get("email")).lower()
    faltando = []
    if not nome:
        faltando.append("o nome do PO")
    if not email:
        faltando.append("o e-mail do PO")
    presentes = {k: v for k, v in (("nome", nome), ("email", email)) if v}
    _, erros = validar_login(presentes, parcial=True)
    return {"nome": nome, "email": email}, faltando, _primeiras(erros), []


VALIDADORES = {
    "cadastrar_projeto": ("projeto", _validar_projeto),
    "cadastrar_profissional": ("profissional", _validar_profissional),
    "cadastrar_competencia": ("competencia", _validar_competencia),
    "cadastrar_usuario": ("usuario", _validar_usuario),
}


def _pode(tipo, usuario):
    return tipo != "usuario" or bool(usuario.is_staff)


# ==========================================
# RESPOSTA AO USUÁRIO
# ==========================================
def _pergunta(texto, opcoes=None):
    opcoes = [_texto(o) for o in (opcoes or []) if isinstance(o, str) and _texto(o)][:MAX_OPCOES]
    return {"texto": texto, "metadata": {"pergunta": {"texto": texto, "opcoes": opcoes}}}


def _juntar(itens):
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def resultado_da_ferramenta(nome, args, usuario):
    """Converte a chamada de ferramenta do modelo em resposta ao usuário: {texto, metadata}."""
    if nome == "perguntar_ao_usuario":
        pergunta = _texto(args.get("pergunta")) or "Pode detalhar um pouco mais o que você precisa?"
        return _pergunta(pergunta, args.get("opcoes"))

    if nome not in VALIDADORES:
        logger.warning("Ferramenta de ação desconhecida: %s", nome)
        return _pergunta(
            "Não entendi o que você quer cadastrar. Escolha uma opção:",
            ["Projeto", "Profissional", "Competência", "Login de PO"],
        )

    tipo, validar = VALIDADORES[nome]
    rotulo = ROTULOS[tipo]
    if not _pode(tipo, usuario):
        return {
            "texto": "Apenas administradores podem cadastrar logins de PO. Peça a um administrador da plataforma.",
            "metadata": None,
        }

    dados, faltando, problemas, opcoes = validar(args, usuario)
    if faltando or problemas:
        partes = []
        if faltando:
            partes.append(f"Para cadastrar o {rotulo}, preciso de {_juntar(faltando)}.")
        partes.extend(problemas)
        return _pergunta(" ".join(partes), opcoes)

    acao = {"id": uuid.uuid4().hex, "tipo": tipo, "dados": dados, "estado": "pendente"}
    nome_alvo = dados.get("titulo") or dados.get("nome")
    texto = f'Preparei o cadastro do {rotulo} "{nome_alvo}". Confira os dados e confirme.'
    return {"texto": texto, "metadata": {"acao": acao}}


def conduzir_acao(message, historico, usuario, chamar_ollama):
    """Uma rodada do agente de cadastros. Devolve {texto, metadata}."""
    messages = [
        {"role": "system", "content": PROMPT_ACOES},
        *historico,
        {"role": "user", "content": message},
    ]
    resposta = chamar_ollama(messages, ferramentas=FERRAMENTAS_ACOES)
    chamadas = resposta.get("tool_calls") or []
    if chamadas:
        funcao = chamadas[0].get("function", {})
        args = funcao.get("arguments") or {}
        if not isinstance(args, dict):
            args = {}
        logger.info("[AÇÃO] ferramenta '%s' args=%s", funcao.get("name"), args)
        return resultado_da_ferramenta(funcao.get("name"), args, usuario)

    texto = (resposta.get("content") or "").strip()
    if texto:
        return {"texto": texto, "metadata": None}
    return _pergunta(
        "O que você gostaria de cadastrar?",
        ["Projeto", "Profissional", "Competência", "Login de PO"],
    )


def aguardando_resposta(conversa):
    """True se a última resposta do assistente foi uma pergunta do fluxo de cadastros."""
    ultima = conversa.mensagens.filter(papel="assistant").order_by("-id").first()
    return bool(ultima and (ultima.metadata or {}).get("pergunta"))


# ==========================================
# CONFIRMAÇÃO / CANCELAMENTO
# ==========================================
class AcaoInvalida(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def _executar(tipo, dados, usuario):
    """Grava o registro. Revalida tudo, pois os dados podem ter mudado desde a proposta."""
    args = dict(dados)
    if tipo == "profissional":
        args["competencias"] = dados.get("competencias", []) + dados.get("competencias_novas", [])
    _, faltando, problemas, _ = VALIDADORES[f"cadastrar_{tipo}"][1](args, usuario)
    if faltando or problemas:
        raise AcaoInvalida(" ".join(problemas) or "Os dados do cadastro estão incompletos.")

    if tipo == "projeto":
        projeto = Projeto.objects.create(
            usuario_po=usuario, titulo=dados["titulo"], descricao=dados["descricao"], status=dados["status"]
        )
        registrar(usuario, "projeto_criado", projeto.titulo)
        return {"id": projeto.id, "link": f"/projetos/{projeto.id}"}, {}

    if tipo == "competencia":
        competencia = Competencia.objects.create(nome=dados["nome"])
        return {"id": competencia.id, "link": "/competencias"}, {}

    if tipo == "profissional":
        competencias = list(Competencia.objects.filter(nome__in=dados.get("competencias", [])))
        for nome in dados.get("competencias_novas", []):
            competencia = Competencia.objects.filter(nome__iexact=nome).first() or Competencia.objects.create(nome=nome)
            competencias.append(competencia)
        profissional = Funcionario.objects.create(nome=dados["nome"], email=dados["email"])
        profissional.competencias.set(competencias)
        return {"id": profissional.id, "link": f"/profissionais/{profissional.id}"}, {}

    if tipo == "usuario":
        # Senha temporária: devolvida só nesta resposta, nunca salva no histórico
        senha = secrets.token_urlsafe(12)
        novo = User.objects.create_user(email=dados["email"], nome=dados["nome"], password=senha)
        return {"id": novo.id_po, "link": "/admin/usuarios"}, {"senha_temporaria": senha}

    raise AcaoInvalida("Tipo de cadastro desconhecido.")


def decidir_acao(mensagem, usuario, confirmar):
    """Confirma ou cancela a ação pendente de uma mensagem do assistente.

    Devolve (acao_atualizada, extras). `extras` (ex.: senha temporária) não é persistido.
    """
    metadata = dict(mensagem.metadata or {})
    acao = dict(metadata.get("acao") or {})
    if not acao:
        raise AcaoInvalida("Esta mensagem não tem cadastro para confirmar.", status=404)
    if acao.get("estado") != "pendente":
        raise AcaoInvalida("Este cadastro já foi confirmado ou cancelado.", status=409)

    tipo, rotulo = acao["tipo"], ROTULOS[acao["tipo"]]
    nome_alvo = acao["dados"].get("titulo") or acao["dados"].get("nome")
    extras = {}
    if not confirmar:
        acao["estado"] = "cancelada"
        mensagem.conteudo = f'Cadastro do {rotulo} "{nome_alvo}" cancelado pelo usuário.'
    else:
        if not _pode(tipo, usuario):
            raise AcaoInvalida("Apenas administradores podem cadastrar logins de PO.", status=403)
        try:
            with transaction.atomic():
                resultado, extras = _executar(tipo, acao["dados"], usuario)
        except IntegrityError:
            raise AcaoInvalida("Já existe um cadastro com estes dados.")
        acao["estado"] = "confirmada"
        acao["resultado"] = resultado
        mensagem.conteudo = f'Cadastro do {rotulo} "{nome_alvo}" confirmado e salvo.'

    metadata["acao"] = acao
    mensagem.metadata = metadata
    mensagem.save(update_fields=["metadata", "conteudo"])
    return acao, extras
