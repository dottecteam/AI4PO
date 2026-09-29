# Formatos e Limites de Upload de Documentos

## Para que serve este documento
Quando alguém envia um documento para a plataforma, o sistema precisa saber duas coisas antes de aceitar: **que tipos de arquivo ele aceita** e **qual o tamanho máximo**. Este documento define essas duas regras, para que a tela de upload, a rota que recebe o arquivo e a extração de texto sigam todas a mesma combinação.

## Formatos aceitos (primeira versão)
* A plataforma aceita arquivos **.md (Markdown)** e **.txt (texto puro)**.
* O motivo é simples: esses arquivos são texto "aberto". O sistema lê o conteúdo diretamente, sem precisar de programas ou bibliotecas extras.

O que fica de fora por enquanto:
* Arquivos como **.pdf** e **.docx**. Eles guardam o texto em formato "fechado", junto com layout, fontes e tabelas. Ler isso exige bibliotecas extras e um tratamento mais complicado. Podem entrar nas próximas sprints.

## Limite de tamanho
* **Máximo de 10 MB por arquivo.**
* Em termos práticos: um documento de texto normal tem algumas centenas de KB, então 10 MB é uma folga grande que não limita ninguém de verdade — mas impede que um arquivo enorme trave os passos seguintes (extrair o texto, dividir em pedaços e transformar em embeddings para o chatbot), que ficam mais lentos e pesados quanto maior for o arquivo.

## Como o upload deve conferir (#3-3)
Quando o usuário escolhe um arquivo, o sistema confere duas coisas antes de aceitar:
1. **A extensão:** o nome do arquivo termina em `.md` ou `.txt`?
2. **O tipo real do arquivo (MIME):** o conteúdo se declara como texto (`text/markdown` ou `text/plain`)?

Conferir as duas coisas impede que alguém renomeie um arquivo qualquer (por exemplo, um `.exe`) para `.txt` e ele passe despercebido. Se qualquer uma das duas checagens falhar, o upload é recusado com uma mensagem clara, como: *"Formato não suportado. Envie um arquivo .md ou .txt de até 10 MB."*

## Por que isso importa para o resto do sistema
* **Na task (#4-2)Extração de texto :** lê o arquivo como texto. Com `.md` e `.txt`, não precisa converter nada.
* **Na task (chunking, #4-3) Divisão em pedaços:** corta o texto em partes que cabem na "memória" do modelo de IA. O limite de tamanho mantém esse corte em um volume administrável.
* **Na task (#5)Chatbot:** só consegue responder com base no que passou por esses passos. Se o upload aceitar algo que a extração não sabe ler, o documento entra no sistema mas nunca chega ao chatbot um defeito silencioso, difícil de perceber.

## Decisões que ficam para depois
* Aceitar ou não `.pdf` e `.docx` em uma sprint futura.
* Definir ou não limite de quantidade de arquivos ou de tamanho total por projeto.