# Site Giulia Camacho

Site da fotógrafa Giulia Camacho, publicado em https://reachoutstudio.github.io/giulia-camacho/.

## Como funciona

- O conteúdo (séries, fotos, Sobre, contatos) fica no Sanity: https://giuliacamacho.sanity.studio/
- `gerador/build.py` lê o conteúdo publicado no Sanity e gera o site estático (PT na raiz, EN em `/en/`). Só usa a biblioteca padrão do Python.
- As fotos são servidas pelo CDN do Sanity, em 800px e 1400px.
- O workflow `.github/workflows/publicar.yml` gera e publica o site no GitHub Pages:
  - a cada 10 minutos, se algo foi publicado no Sanity desde o último deploy;
  - a cada push na branch `main`;
  - manualmente, em Actions → Publicar site → Run workflow;
  - por webhook do Sanity (`repository_dispatch` do tipo `sanity-publish`), se configurado.

## Gerar localmente

```
python3 gerador/build.py dist
```

Use `SITE_URL=https://seu-dominio/` para gerar com outro endereço.
