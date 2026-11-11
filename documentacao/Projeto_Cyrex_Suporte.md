# Centro Universitário Filadélfia – UniFil

**Walter Hian Oliveira Barroso**

# Projeto Cyrex Suporte
## Sistema de Controle de Chamados e Equipamentos

Projeto de Desenvolvimento de Software I  
Arapongas – PR  
2026

## Sumário

1. Introdução  
2. Desenvolvimento  
   2.1 Escopo e tecnologias  
   2.2 Requisitos funcionais  
   2.3 Requisitos não funcionais  
   2.4 Atores e casos de uso  
   2.5 Modelo de dados  
   2.6 Diagrama de atividade  
   2.7 Diagrama de classes  
   2.8 Diagramas de sequência  
   2.9 Segurança e limitações  
3. Conclusão  
4. Referências

## 1 Introdução

O Cyrex Suporte é um sistema web para organizar solicitações de suporte de tecnologia da informação, o inventário de equipamentos e o histórico de atendimento. O sistema busca reunir em um só lugar os dados de solicitantes, técnicos, equipamentos e chamados, permitindo acompanhar cada solicitação desde a abertura até a conclusão.

A implementação acadêmica utiliza Python com Flask no servidor, SQLite como banco de dados relacional e páginas HTML, CSS e JavaScript na interface. O banco armazena senhas com hash, dados de pessoas, equipamentos, chamados, respostas e registros de atividade. O repositório também inclui a prévia visual interativa criada durante o desenvolvimento; ela está em `cyrex-preview/index.html` e usa o armazenamento local do navegador, enquanto a aplicação Flask é a versão conectada ao SQLite.

O objetivo é aplicar levantamento de requisitos, modelagem de dados, diagramas UML e operações de cadastro, consulta, atualização e inativação. O documento apresenta as regras de acesso, os fluxos de trabalho e as relações entre as entidades principais.

## 2 Desenvolvimento

### 2.1 Escopo e tecnologias

O sistema possui três perfis. O Solicitante cria uma conta pública, abre chamados e acompanha somente suas solicitações. O Técnico consulta e atende chamados, registra respostas, atualiza status e prioridade e informa a solução. O Administrador tem acesso total, gerencia pessoas e equipamentos e pode criar contas de Técnico e Administrador.

O cadastro público exige nome completo, e-mail, função ou cargo, setor, telefone, ramal e senha. A própria pessoa pode criar somente o perfil Solicitante. Contas de Técnico e Administrador são incluídas na área Pessoas por um Administrador. Pessoas são inativadas em vez de removidas, preservando seus chamados anteriores.
O painel Admin, visível somente ao perfil Administrador, centraliza os cadastros de tipos de equipamento, marcas, modelos e setores. As opções são usadas na inclusão de equipamentos; alterações também atualizam os registros vinculados e exclusões são bloqueadas enquanto houver uso. O mesmo painel permite personalizar logotipo, banner e cores do sistema, além de restaurar apenas a paleta padrão sem remover logotipo ou banner. As páginas de chamados, equipamentos e pessoas possuem pesquisa por seus dados principais. A auditoria global lista alterações de chamados, pessoas, equipamentos e aparência, identificando usuário, perfil, ação e data.

Ao abrir um chamado, o nome do solicitante vem da conta conectada. A lista de equipamentos disponíveis é limitada aos equipamentos ativos do setor da pessoa; o servidor também valida essa associação antes de gravar o chamado. O equipamento pode ter número de série e descrição opcional. O chamado registra assunto, descrição, prioridade, status, solicitante, equipamento, técnico responsável, solução, respostas e datas.

A aplicação principal é executada localmente com `python app.py`. A prévia `cyrex-preview/index.html` reproduz a interface visual interativa do site e funciona de forma autônoma no navegador; seus dados são locais e não são sincronizados com o banco da aplicação Flask.

### 2.2 Requisitos funcionais

| Código | Requisito |
|---|---|
| RF01 | Permitir a configuração inicial de uma conta Administrador com os dados pessoais obrigatórios. |
| RF02 | Permitir login e logout por e-mail e senha, armazenando senhas com hash. |
| RF03 | Permitir auto cadastro com nome, e-mail, função, setor, telefone, ramal e senha; esse cadastro deve criar somente perfil Solicitante. |
| RF04 | Permitir que Administrador crie, edite e inative pessoas nos perfis Solicitante, Técnico e Administrador. |
| RF05 | Impedir inativação do último Administrador ativo e preservar o histórico associado à pessoa. |
| RF06 | Permitir que Administrador cadastre, consulte, edite e exclua equipamentos, incluindo patrimônio, tipo, marca, modelo, número de série opcional, setor e descrição opcional. |
| RF07 | Permitir que Solicitante abra chamado com assunto, descrição, prioridade e equipamento do seu setor; o solicitante deve ser identificado pela conta autenticada. |
| RF08 | Permitir pesquisa e filtragem de chamados por número, assunto, patrimônio e status. |
| RF09 | Permitir que Solicitante consulte apenas os próprios chamados e seus detalhes. |
| RF10 | Permitir que Técnico e Administrador alterem status e prioridade, registrem respostas e informem solução para concluir o chamado. |
| RF11 | Exigir confirmação antes de salvar alterações de atendimento e exigir solução para concluir um chamado. |
| RF12 | Registrar usuário, perfil, data, ação e detalhes das alterações em pessoas, equipamentos e chamados. |
| RF13 | Preservar relações históricas entre chamados, pessoas e equipamentos por meio de chaves estrangeiras e regras de inativação. |

### 2.3 Requisitos não funcionais

| Código | Requisito |
|---|---|
| RNF01 | A interface deve adaptar-se a computadores e dispositivos móveis e apresentar textos legíveis. |
| RNF02 | O sistema deve utilizar SQLite e chaves estrangeiras para preservar a integridade relacional. |
| RNF03 | O servidor deve validar campos, perfis, status, unicidade e vínculos, sem depender apenas das validações do navegador. |
| RNF04 | Senhas não podem ser armazenadas em texto puro. |
| RNF05 | Pessoas e equipamentos vinculados a chamados não devem ser removidos de modo a apagar o histórico; deve-se preferir inativação. |
| RNF06 | A aplicação deve apresentar mensagens de erro compreensíveis e manter rotas, modelos e interface organizados. |
| RNF07 | O projeto deve ser executável localmente com dependências declaradas em `requirements.txt`. |
| RNF08 | A versão de produção deve configurar chave secreta forte, HTTPS, proteção contra CSRF, controle de tentativas de login, backups e servidor WSGI. |

### 2.4 Atores e casos de uso

**Solicitante:** realiza auto cadastro, abre chamados e acompanha os próprios registros.  
**Técnico:** atende chamados, registra respostas, atualiza prioridade e status e conclui solicitações.  
**Administrador:** gerencia pessoas, perfis e equipamentos e também pode executar as tarefas de atendimento.

Os cinco casos de uso principais são:

- **UC01 – Abrir e acompanhar chamado:** o Solicitante registra a solicitação e acompanha o próprio histórico.
- **UC02 – Gerenciar pessoas:** o Administrador cadastra, edita e inativa usuários, escolhendo o perfil e mantendo o histórico.
- **UC03 – Gerenciar equipamentos:** o Administrador mantém o inventário, incluindo serial, setor e descrição opcional.
- **UC04 – Atender chamado:** Técnico ou Administrador registra respostas, altera status e prioridade e conclui com uma solução.
- **UC05 – Consultar histórico e rastreabilidade:** cada perfil acessa os dados permitidos; alterações são identificadas por ator, data e ação.

O diagrama de casos de uso está em `docs/diagramas/casos_de_uso.dot`.

### 2.5 Modelo de dados

O DER contém três entidades centrais. Uma Pessoa pode abrir várias solicitações e pode ser responsável técnico por vários chamados. Cada Chamado possui exatamente um solicitante e um equipamento; a atribuição de Técnico é opcional. Um Equipamento pode aparecer em vários chamados. Respostas e registros de atividade pertencem ao chamado correspondente; uma pessoa pode ser autora de muitas respostas e ações.

**Pessoa:** identificador, nome, e-mail, hash da senha, perfil, função, setor, telefone, ramal, situação e data de cadastro.  
**Equipamento:** identificador, patrimônio, tipo, marca, modelo, número de série, descrição, localização/setor, situação e data de cadastro.  
**Chamado:** identificador, número, assunto, descrição, prioridade, status, datas, solução, solicitante, técnico e equipamento.  
**Resposta:** chamado, autor, perfil, mensagem e data.  
**RegistroAtividade:** ator, perfil, ação, entidade, identificador do registro, detalhes e data.

O código do DER está em `docs/diagramas/der.dot`.

### 2.6 Diagrama de atividade

O fluxo começa com o Solicitante autenticado preenchendo a solicitação. O servidor valida os dados e confirma que o equipamento está ativo e pertence ao setor da pessoa. Se os dados forem válidos, cria o chamado e registra a atividade. O Técnico analisa o pedido, pode registrar respostas e atualizar o status ou a prioridade. A conclusão exige uma solução; o sistema grava a data e mantém o histórico.

O diagrama está em `docs/diagramas/atividade.dot`.

### 2.7 Diagrama de classes

O diagrama concentra-se nas entidades Pessoa, Equipamento, Chamado, Resposta e RegistroAtividade. As associações mostram os vínculos e multiplicidades descritos no DER. O diagrama está em `docs/diagramas/classes.dot`.

### 2.8 Diagramas de sequência

Cada sequência apresenta o ator, a interface, a aplicação Flask e o banco SQLite:

1. `seq_uc01.dot` – abrir e acompanhar chamado;
2. `seq_uc02.dot` – gerenciar pessoas;
3. `seq_uc03.dot` – gerenciar equipamentos;
4. `seq_uc04.dot` – atender e concluir chamado;
5. `seq_uc05.dot` – consultar histórico e registrar rastreabilidade.

### 2.9 Segurança e limitações

A aplicação Flask valida permissões no servidor e mantém dados no SQLite. A configuração inicial cria o primeiro Administrador; depois disso, não há cadastro público de perfis privilegiados. O cadastro público sempre fixa o perfil como Solicitante. A interface estática de prévia serve para demonstração visual e mantém dados no navegador; ela não deve ser usada como armazenamento compartilhado nem como mecanismo de autenticação real.

A aplicação Flask usa o servidor de desenvolvimento para execução local. Uma implantação real exige configuração de produção, chave secreta protegida, HTTPS, proteção CSRF, política de bloqueio de tentativas, cópias de segurança e revisão das permissões.

## 3 Conclusão

O projeto reúne análise de requisitos, modelagem UML, implementação web e persistência relacional. A construção de perfis distintos mostrou a importância de validar permissões no servidor e de separar o auto cadastro de solicitantes da gestão administrativa de contas. A associação entre pessoas, setores, equipamentos e chamados também demonstrou como regras de negócio podem proteger a consistência dos registros e facilitar a recuperação do histórico.

A implementação permitiu praticar operações CRUD, autenticação com hash de senha, integridade referencial em SQLite e organização de rotas e telas com Flask. Os diagramas ajudam a explicar o fluxo do atendimento e a relação entre as entidades antes da evolução do sistema.

## 4 Referências

FLASK. **Flask Documentation**. Disponível em: https://flask.palletsprojects.com/. Acesso em: 10 nov. 2026.

OBJECT MANAGEMENT GROUP. **OMG Unified Modeling Language (OMG UML), Version 2.5.1**. 2017. Disponível em: https://www.omg.org/spec/UML/2.5.1. Acesso em: 10 nov. 2026.

PYTHON SOFTWARE FOUNDATION. **Python 3 Documentation**. Disponível em: https://docs.python.org/3/. Acesso em: 10 nov. 2026.

SQLITE. **SQLite Documentation**. Disponível em: https://www.sqlite.org/docs.html. Acesso em: 10 nov. 2026.
