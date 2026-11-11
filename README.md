# Cyrex – Suporte

Repositório completo do projeto acadêmico de controle de chamados e equipamentos. Contém a implementação Python/Flask com banco SQLite, a documentação e a prévia interativa Cyrex refinada durante o trabalho no site.

## Executar a aplicação Flask com SQLite

Requisitos: Python 3.10 ou superior.

No Windows PowerShell, na pasta do projeto:

```powershell
python -m venv .venv
python -m pip install -r requirements.txt
python app.py
```

Se o comando `python` não apontar para a instalação correta, use o caminho completo do executável:

```powershell
& 'C:\Users\Walter\AppData\Local\Python\pythoncore-3.15-64\python.exe' -m pip install -r requirements.txt
& 'C:\Users\Walter\AppData\Local\Python\pythoncore-3.15-64\python.exe' app.py
```

Acesse http://127.0.0.1:5000. Na primeira execução, crie a conta inicial de Administrador. O banco SQLite `scmc.db` será criado localmente e não deve ser versionado.

## Perfis e regras

- O cadastro público exige nome, e-mail, função/cargo, setor, telefone, ramal e senha; cria exclusivamente o perfil Solicitante.
- Somente Administrador cria contas de Técnico e Administrador em Pessoas.
- Técnico atende chamados; Administrador gerencia pessoas e equipamentos e tem acesso total.
- Chamados abertos por Solicitante usam a identidade autenticada e só podem associar equipamento ativo do mesmo setor.
- Pessoas são inativadas para preservar chamados antigos.
- Equipamentos incluem patrimônio, tipo, marca, modelo, setor/localização, número de série e descrição opcional; tipo, marca, modelo e setor são escolhidos dos cadastros do painel Admin.
- Painel Admin com gerenciamento dos quatro cadastros, personalização de logo, banner e cores (com botão para restaurar somente as cores) e pesquisa em chamados, equipamentos e pessoas.
- Chamados mantêm status, prioridade, solução, respostas e histórico de atividade.

## Prévia visual do site

`cyrex-preview/index.html` contém a interface interativa do site Cyrex trabalhada durante o desenvolvimento. Ela pode ser aberta no navegador e seus dados ficam no armazenamento local desse navegador. A prévia visual não usa o banco SQLite da aplicação Flask.

Site publicado: https://scmc-central-suporte-preview.peppybamboo8.chatgpt.site

## Documentação

- `documentacao/Projeto_Cyrex_Suporte.docx` – versão editável.
- `documentacao/Projeto_Cyrex_Suporte.pdf` – versão para leitura e entrega.
- `documentacao/Projeto_Cyrex_Suporte.md` – versão fonte.
- `docs/diagramas/` – fontes DOT e imagens dos diagramas de caso de uso, DER, atividade, classes e cinco sequências.

## Estrutura

- `app.py`: rotas Flask, autenticação, permissões, validação e persistência SQLite.
- `templates/`: páginas Jinja do sistema Flask.
- `static/`: estilos responsivos e scripts.
- `cyrex-preview/`: interface visual interativa do site.
- `documentacao/`: relatório acadêmico em DOCX, PDF e Markdown.
- `docs/diagramas/`: diagramas UML e fontes editáveis.

## Segurança

A aplicação usa o servidor de desenvolvimento do Flask para execução local. Antes de disponibilizar para uso real, configure `SCMC_SECRET_KEY`, HTTPS, servidor WSGI, proteção CSRF, limitação de tentativas de login e backups.
