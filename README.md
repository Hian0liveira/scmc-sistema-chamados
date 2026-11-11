# Cyrex – Suporte

Repositório completo do projeto acadêmico de controle de chamados e equipamentos. Contém a implementação Python/Flask com banco SQLite, a documentação e a prévia interativa Cyrex refinada durante o trabalho no site.

## Executar o Cyrex Web com Flask e SQLite

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

Acesse http://127.0.0.1:5000. A interface visual do Cyrex é servida pelo Flask. Na primeira execução, crie a conta inicial de Administrador em `/setup`; depois, entre pela tela de login do Cyrex. O banco SQLite `scmc.db` é criado localmente. Chamados, equipamentos, catálogos, aparência, auditoria e contas ficam no servidor; as senhas são armazenadas com hash. O cadastro público cria somente perfil Solicitante.

## Perfis e regras

- O cadastro público exige nome, e-mail, função/cargo, setor, telefone, ramal e senha; cria exclusivamente o perfil Solicitante.
- Somente Administrador cria contas de Técnico e Administrador em Pessoas.
- Técnico atende chamados; Administrador gerencia pessoas e equipamentos e tem acesso total.
- Chamados abertos por Solicitante usam a identidade autenticada e só podem associar equipamento ativo do mesmo setor.
- Pessoas são inativadas para preservar chamados antigos.
- Equipamentos incluem patrimônio, tipo, marca, modelo, setor/localização, número de série e descrição opcional; tipo, marca, modelo e setor são escolhidos dos cadastros do painel Admin.
- Painel Admin com gerenciamento dos quatro cadastros, personalização de logo, banner e cores (com botão para restaurar somente as cores) e pesquisa em chamados, equipamentos e pessoas.
- Chamados mantêm status, prioridade, solução, respostas e histórico de atividade.

## Interface Web

`cyrex-preview/index.html` é a interface web integrada à aplicação Flask. O login, cadastro público de solicitantes, gerenciamento de pessoas, inventário, chamados, catálogos, auditoria e aparência usam a API Flask. Os dados são persistidos no SQLite local em `scmc.db`; o navegador não é a fonte principal dos dados.

A interface está preparada para celular e desktop. Para usá-la em outra máquina, publique o servidor Flask em uma hospedagem Python com banco persistente e configure a chave `SCMC_SECRET_KEY`.

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
