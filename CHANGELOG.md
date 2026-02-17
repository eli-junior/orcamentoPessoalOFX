# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Não liberado]

### Adicionado
- Docker e Docker Compose para containerização da aplicação e banco de dados.
- Comandos de gerenciamento (`management commands`):
    - `importar`: Importação de arquivos OFX.
    - `consolidar`: Processamento de transações importadas.
    - `sugerir`: Sugestão de categorias para transações via IA.
    - `popular`: Carga inicial de dados (contas e categorias).
- Testes unitários para modelos e serviços de importação OFX.
- Configuração do `uv` para gerenciamento de dependências.

### Modificado
- Reformulação do `README.md` com instruções atualizadas de instalação e uso.
- Melhorias na administração do Django (Django Admin) para transações e despesas.
