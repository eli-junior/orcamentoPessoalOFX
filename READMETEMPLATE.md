<div align="center" style="text-align: center;">
  <a href="#-sobre">Sobre</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#-tecnologias">Tecnologias</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#-recursos-disponiveis">Recursos</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#-iniciando-o-projeto">Iniciando o Projeto</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#-testes">Testes</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#-contribuindo">Contribuindo</a>&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;
  <a href="#-autores">Autores</a>
</div>

## 🤔 Sobre

O [**Orcamento 2026**](https://link) é um software de processamento Backend, que fornece **APIs** para...

## 🚀 Tecnologias

Esse projeto foi desenvolvido com as seguintes tecnologias:

***General***:

- [Django](https://pypi.org/project/fastapi/)
- [Python Decouple](https://pypi.org/project/python-decouple/)
- [DJ Database URL](https://pypi.org/project/dj-database-url/)
- [Django Extensions](https://pypi.org/project/django-extensions/)

## ✨ Recursos Disponiveis

Os recursos disponíveis da aplicação podem ser encontrados no  [swagger](https://swagger.io/). Para acessa-los, acrescente "/docs/" ao final da URL da aplicação.

## 🏃 Iniciando o Projeto

### **Sem Docker** 🖥️

Para iniciar essa aplicação sem o docker, você irá precisar de [python](https://www.python.org/), [virtualenv](https://virtualenv.pypa.io/en/latest/) instalados no seu computador.
Recomendamos fortemente o uso do [Pyenv](https://github.com/pyenv/pyenv) para o desenvolvimento de suas aplicações.
```bash
  # Crie o ambiente virtual para seu projeto python

  $ python -m venv .venv

  # Ative o environment

  $ source ./.venv/bin/activate

  # Instale as dependências

  $ make install

  # Inicie a aplicação

  $ make run

  # Para desativar a máquina virtual python (virtualenv):

  $ deactivate
```

## 🚨 Testes
### **Rodando os Testes** ✅

```bash
  ## Para rodar os testes unitários

  $ make test
```

### **Desenvolvendo com Testes** 🔥

O time utiliza a metologia [TDD](https://testdriven.io/blog/modern-tdd/) para implementação de novas funcionalidades, caso não possua conhecimento, é recomendável a leitura do artigo citado.

## 💁🏻 Contribuindo

1. **Clone** o projeto:
2. Crie sua **feature**/**fix** branch seguindo o padrão e faça suas modificações:

```bash
  $ git checkout -b feature/nome_da_branch
```


3. **Formate** os arquivos:
```bash
  ## Para formatar os arquivos

  $ make format
```
5. **Commit** suas modificações:

```bash
  # Padrão seguido (message downcase):
  #
  # feat: a new feature
  # fix: a bug fix
  # docs: documentation only changes
  # style: changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
  # refactor: a code change that neither fixes a bug nor adds a feature
  # perf: a code change that improves performance
  # test: adding missing or correcting existing tests
  # support: changes to the build process or auxiliary tools and libraries such
  # as documentation generation or continous integration configuration

  $ git commit -m 'feat: insert your message'
```

6. **Push** para a branch:

```bash
  $ git push origin feature/103574
```

7. Realize um **pull request** :D
8. Realize um merge local na branch master com as suas alterações, e em seguida a delete.

```bash
  $ git checkout master
  $ git merge feature/nome_da_branch
  $ git branch -d feature/nome_da_branch

## ✍️ Autores

[Melo Brothers](https://github.com/melo-brothers/)
