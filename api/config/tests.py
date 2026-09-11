"""Testes da task #3-4 (armazenamento de uploads em disco local).

Provam duas coisas:
1. que a configuracao de media aponta para o lugar combinado;
2. que o default_storage (contrato que a futura rota de upload da #3-3
   vai usar) salva, le e apaga arquivos de verdade.
"""

import tempfile  # pasta temporaria do SO: o teste nao suja a media/ real
from pathlib import Path

from django.core.files.base import ContentFile  # embrulha bytes como arquivo para o storage
from django.core.files.storage import default_storage  # storage configurado por MEDIA_ROOT/MEDIA_URL
from django.test import TestCase, override_settings


class ConfiguracaoMediaTests(TestCase):
    """Confere o combinado da configuracao, sem tocar em disco."""

    def test_media_root_padrao_aponta_para_pasta_media(self):
        from django.conf import settings

        # Prefixo publico usado para servir os uploads.
        self.assertEqual(settings.MEDIA_URL, '/media/')
        # Pasta fisica padrao dos uploads: api/media/ (Sprint 1 = disco local).
        self.assertEqual(Path(settings.MEDIA_ROOT).name, 'media')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ArmazenamentoLocalTests(TestCase):
    """Ciclo de vida completo de um upload via default_storage.

    O override_settings troca a pasta de gravacao por uma temporaria:
    o teste nunca escreve na media/ real do projeto.
    """

    def test_salva_le_e_remove_arquivo(self):
        # Simula um upload: grava conteudo binario e devolve o nome final no storage.
        nome = default_storage.save('uploads/exemplo.txt', ContentFile(b'conteudo de teste'))
        # Garantia de limpeza: mesmo se o teste falhar, o arquivo e apagado no final.
        self.addCleanup(default_storage.delete, nome)

        # O arquivo gravado existe...
        self.assertTrue(default_storage.exists(nome))
        # ...e o conteudo lido de volta e identico ao gravado.
        with default_storage.open(nome) as arquivo:
            self.assertEqual(arquivo.read(), b'conteudo de teste')

        # Apaga e confere que sumiu: o storage tambem precisa saber remover.
        default_storage.delete(nome)
        self.assertFalse(default_storage.exists(nome))