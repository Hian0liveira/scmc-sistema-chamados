# Banco de dados Cyrex

O arquivo `cyrex_demo.db` é o banco SQLite usado pelo projeto. Ele contém dados de demonstração inspirados nos registros padrão da interface Cyrex: oito pessoas (incluindo o Administrador inicial), quatro equipamentos, cinco chamados, dezessete itens de catálogo e registros de atividade. Os vínculos de chave estrangeira foram incluídos para facilitar a apresentação do modelo relacional.

## Primeiro acesso

Execute `python app.py` e acesse `http://127.0.0.1:5000/setup`. Configure o Administrador com seu próprio nome, e-mail e senha. O registro inicial `admin@scmc.local` não tem senha definida; a configuração inicial reaproveita esse registro, evitando uma credencial de demonstração fixa.

## Abrir e apresentar

Use um visualizador de SQLite, como DB Browser for SQLite, e abra `cyrex_demo.db`. Na aba **Estrutura do banco de dados**, mostre as tabelas; na aba **Browse Data**, selecione `users`, `equipment`, `service_orders`, `catalog_items` e `activity_log`. Para ver os relacionamentos, abra a visualização de relações ou consulte as chaves estrangeiras de `service_orders`.

## Tabelas principais

- `users`: pessoas, perfis, setor e autenticação.
- `equipment`: inventário, patrimônio, marca, modelo, série e localização.
- `service_orders`: chamados, prioridade, status e vínculos com solicitante, técnico e equipamento.
- `ticket_responses`: respostas registradas nos chamados.
- `activity_log`: trilha de auditoria.
- `catalog_items`: tipos, marcas, modelos e setores.
- `appearance_settings`: identidade visual.
- `cyrex_web_state`: estado da interface web e configurações visuais persistidas.
