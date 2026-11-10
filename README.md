# Cyrex – Suporte (SCMC)

Sistema web de controle de chamados e inventário de TI. Implementado em Python, Flask, SQLite, HTML, CSS e JavaScript.

## Requisitos

- Python 3.10 ou superior
- Pip

## Executar no Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Se o PowerShell bloquear a ativação do ambiente virtual, execute os comandos de instalação sem ativá-lo:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Abra http://127.0.0.1:5000. Na primeira execução, crie a conta inicial de Administrador. O arquivo de banco `scmc.db` é criado localmente e não deve ser enviado ao GitHub.

## Perfis e cadastro

- O cadastro público exige nome, e-mail, função/cargo, setor, telefone, ramal e senha. Ele cria exclusivamente o perfil Solicitante.
- Somente um Administrador pode criar contas de Técnico e Administrador pela área Pessoas.
- Técnicos atendem e atualizam chamados. Administradores têm acesso total e gerenciam pessoas e inventário.
- Ao abrir chamado, o nome do solicitante vem da conta conectada. O seletor de equipamento mostra apenas equipamentos ativos do setor do solicitante, e o servidor valida essa associação.
- Inativar uma pessoa preserva os chamados relacionados.

## Funcionalidades

- Login, configuração inicial e senhas armazenadas com hash seguro.
- CRUD de pessoas, equipamentos e chamados.
- Campos de função, setor, telefone e ramal no cadastro de pessoas.
- Pesquisa e filtros de chamados, prioridades, status, atribuição de técnico e encerramento com solução.
- Banco SQLite com relacionamentos entre chamados, pessoas e equipamentos.

## Estrutura do projeto

- `app.py`: rotas Flask, autenticação, regras de perfil e acesso ao SQLite.
- `templates/`: telas HTML/Jinja.
- `static/`: estilos e scripts do navegador.
- `documentacao/` e `docs/`: documentação acadêmica e diagramas UML.

## Configuração de segurança

Para manter as sessões após reiniciar, defina uma chave forte na variável `SCMC_SECRET_KEY`. A aplicação usa o servidor de desenvolvimento do Flask; para publicar, configure um servidor WSGI, HTTPS, proteção CSRF, limitação de tentativas de login e backups.
