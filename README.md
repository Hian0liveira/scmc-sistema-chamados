# Cyrex – Suporte

Este pacote serve pelo Flask a mesma interface Cyrex da prévia web. A tela e as interações do sistema estão em `cyrex-preview/index.html`.

## Requisitos

- Python 3.10 ou superior
- Acesso à internet na primeira instalação das dependências

## Executar no Windows PowerShell

Abra o terminal do VS Code na pasta extraída e rode:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Se `python` não estiver no PATH, use o caminho completo do executável, por exemplo:

```powershell
& 'C:\Users\Walter\AppData\Local\Python\pythoncore-3.15-64\python.exe' -m pip install -r requirements.txt
& 'C:\Users\Walter\AppData\Local\Python\pythoncore-3.15-64\python.exe' app.py
```

Acesse http://127.0.0.1:5000.

## Acesso inicial

A tela de login mostra o acesso de demonstração do administrador. Também é possível criar uma conta pelo botão **Criar cadastro de solicitante**. O cadastro público cria somente solicitantes; perfis de Técnico e Administrador são gerenciados pela área Pessoas.

## Dados e funcionamento

Para manter a mesma implementação da prévia web, as interações e os dados desta versão são armazenados no armazenamento local do navegador. Eles não são compartilhados entre navegadores ou computadores. O Flask entrega a página; esta edição não configura banco de dados no servidor.

Prévia online: https://scmc-central-suporte-preview.peppybamboo8.chatgpt.site
