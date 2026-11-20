from decouple import config

# Modelos com raciocínio (ex.: qwen3/qwen3.5) gastam os tokens de `num_predict`
# "pensando" e devolvem `content` vazio, quebrando o roteador (JSON) e os
# títulos. Com think=False eles respondem direto; modelos sem raciocínio ignoram.
THINK = config("OLLAMA_THINK", default=False, cast=bool)
