<div align="center" style="text-align: center;">
  <h1>Orçamento Pessoal</h1>
  <p>Backend para gerenciamento de orçamento pessoal, focado em processamento de arquivos OFX e categorização inteligente.</p>

  <p>
    <a href="#-sobre">Sobre</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
    <a href="#-tecnologias">Tecnologias</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
    <a href="#-recursos">Comandos</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
    <a href="#-iniciando-o-projeto">Instalação</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
    <a href="#-testes">Testes</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
    <a href="#-contribuindo">Contribuindo</a>
  </p>
</div>

## 🤔 Sobre

O **Orçamento Pessoal** é um sistema de backend desenvolvido em Django para auxiliar no controle financeiro pessoal. Ele permite a importação de extratos bancários (arquivos OFX), consolidação de transações e sugestão automática de categorias utilizando inteligência artificial.

## 🚀 Tecnologias

Esse projeto foi desenvolvido com as seguintes tecnologias:

- [Django](https://www.djangoproject.com/) - Framework Web de alto nível
- [PostgreSQL](https://www.postgresql.org/) - Banco de Dados Relacional
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) - Containerização
- [UV](https://github.com/astral-sh/uv) - Gerenciador de pacotes e projetos Python
- [Django Extensions](https://django-extensions.readthedocs.io/) - Extensões úteis para desenvolvimento

## ✨ Recursos e Comandos

O projeto possui diversos comandos de gerenciamento (`management commands`) para facilitar as operações do dia a dia:

### 📥 Importar OFX
Importa transações de arquivos OFX localizados no diretório configurado (padrão: `dados/ofx`).

```bash
docker compose run --rm app python manage.py importar
# ou localmente
python manage.py importar
```

### 🔄 Consolidar Transações
Processa as transações importadas, convertendo-as em despesas e aplicando regras de negócio.

```bash
docker compose run --rm app python manage.py consolidar
```

### 🤖 Sugerir Categorias (IA)
Utiliza IA para analisar transações pendentes e sugerir categorias e subcategorias prováveis.

```bash
docker compose run --rm app python manage.py sugerir
```

### 🌱 Popular Banco de Dados
Popula o banco de dados com dados iniciais, como contas padrão e árvore de categorias.

```bash
docker compose run --rm app python manage.py popular
```

## 🏃 Iniciando o Projeto

### **Com Docker (Recomendado)** 🐳

Certifique-se de ter o Docker e Docker Compose instalados.

1. **Subir os serviços**:
   ```bash
   docker compose up -d
   ```
   Isso iniciará a aplicação Django e o banco de dados PostgreSQL.

2. **Aplicar as migrações**:
   ```bash
   docker compose run --rm app python manage.py migrate
   ```

3. **Popular dados iniciais (opcional)**:
   ```bash
   docker compose run --rm app python manage.py popular
   ```

A aplicação estará disponível em `http://localhost:8000`.

### **Execução Local (Sem Docker)** 🖥️

Você precisará do [Python 3.14.6](https://www.python.org/) e [UV](https://github.com/astral-sh/uv) instalados.

1. **Subir a aplicação com PowerShell e UV**:
   ```powershell
   .\start.ps1
   ```

   O script valida o UV, cria o `.env` a partir de `.env-contrib` quando necessário,
   sincroniza as dependências travadas em `uv.lock`, executa as verificações e
   migrações do Django e inicia o servidor em `http://127.0.0.1:8000`.

   Para alterar endereço ou porta, ou pular etapas já executadas:
   ```powershell
   .\start.ps1 -BindAddress 0.0.0.0 -Port 8001
   .\start.ps1 -SkipSync -SkipMigrations
   ```

   Não é necessário ativar manualmente o ambiente virtual: todos os comandos
   Python são executados por `uv run`.

Também é possível usar o `Makefile` para atalhos:
- `make install`: Instala dependências
- `make run`: Roda o servidor
- `make format`: Formata o código

## 🚨 Testes

O projeto utiliza `pytest` para testes automatizados.

```bash
# Via Docker
docker compose run --rm app pytest

# Localmente
pytest
# ou
make test
```

## 💁🏻 Contribuindo

1. Faça um **Clone** do projeto.
2. Crie uma branch para sua feature (`git checkout -b feature/minha-feature`).
3. Faça suas alterações e commite (`git commit -m 'feat: Adiciona nova funcionalidade'`).
4. Envie para o repositório (`git push origin feature/minha-feature`).
5. Abra um Pull Request.

## ✍️ Autores

Desenvolvido por **Eli Júnior** e colaboradores.
