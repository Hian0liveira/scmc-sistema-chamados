# SCMC — Sistema de Controle de Chamados de Manutenção de Computadores

Aplicação web acadêmica para registrar equipamentos e acompanhar ordens de serviço. Stack: Python, Flask, SQLite, HTML e CSS.

## Requisitos
- Python 3.10 ou superior

## Executar localmente
```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Acesse http://127.0.0.1:5000. O arquivo SQLite `scmc.db` é criado automaticamente. Cadastre usuários e equipamentos antes de abrir ordens. A chave de sessão pode ser configurada pela variável de ambiente `SCMC_SECRET_KEY`; o valor padrão serve apenas para desenvolvimento local.

## Funcionalidades
- CRUD de usuários com perfis de Técnico e Solicitante; cadastro relacionado não pode ser removido, mas pode ser inativado.
- CRUD de equipamentos, com patrimônio único e inativação quando houver histórico.
- CRUD de ordens de serviço, com pesquisa, filtros, prioridade, técnico e encerramento com solução.
- Relacionamentos e chaves estrangeiras no SQLite.

## Estrutura
`app.py` contém rotas e acesso ao SQLite; `templates/` contém páginas HTML; `static/` contém estilos; o banco é local e não deve ser versionado.

## Observação acadêmica
Esta versão é um protótipo didático. Antes de publicar para uso real, configure uma chave secreta forte, autenticação e autorização, proteção CSRF, controle de acesso, cópias de segurança e implantação segura.
