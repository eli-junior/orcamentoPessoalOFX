from invoke import task


@task
def popular(c):
    """Popula as categorias iniciais do banco"""
    c.run("uv run manage.py makemigrations")
    c.run("uv run manage.py migrate")
    c.run("uv run manage.py popular")


@task
def importar(c):
    """Importa arquivos OFX: inv importar --conta=1 --mes=2026-02"""
    c.run("uv run manage.py importar", pty=True)


@task
def sugerir(c):
    """Sugere categorias para as transações"""
    c.run("uv run manage.py sugerir")


@task
def consolidar(c):
    """Consolida as transações"""
    c.run("uv run manage.py consolidar")


@task
def runserver(c):
    """Roda o servidor"""
    c.run("uv run manage.py collectstatic --noinput")
    c.run("uv run manage.py runserver 0.0.0.0:8000")


@task
def test(c):
    """Executa os testes com pytest"""
    c.run("uv run pytest")
