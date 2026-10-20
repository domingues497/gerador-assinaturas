# Gerador de Assinaturas de E-mail

Aplicação desktop para Windows (Flask + SQLite + PyInstaller) para criar,
configurar e gerar assinaturas HTML compatíveis com o Novo Outlook.

## 1. Rodando em modo desenvolvimento

Requer Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

O navegador abrirá automaticamente em `http://127.0.0.1:5000` (ou na
próxima porta livre, caso a 5000 esteja ocupada).

Em desenvolvimento (fora do `.exe`), o banco fica em:
`~/.geradorassinaturas/assinaturas.db` (Linux/Mac) ou
`%APPDATA%\GeradorAssinaturas\assinaturas.db` (Windows).

## 2. Gerando o executável (.exe)

```bash
pip install -r requirements.txt
pyinstaller build/build.spec
```

Comando equivalente "cru" (caso prefira sem o `.spec`):

```bash
pyinstaller --onefile --windowed --name GeradorAssinaturas ^
    --add-data "templates;templates" --add-data "static;static" app.py
```

O executável final fica em `dist/GeradorAssinaturas.exe`. Não é necessário
Python instalado na máquina do usuário final.

## 3. Onde os dados ficam salvos

```
%APPDATA%\GeradorAssinaturas\
├── assinaturas.db      (banco SQLite: empresa, colaboradores, modelos,
│                         redes sociais, assinaturas, configurações)
└── logs\
    └── app.log
```

Atualizar o `.exe` (substituir o arquivo) **não apaga** essa pasta, então as
configurações e assinaturas cadastradas são preservadas entre versões.

## 4. Fluxo de uso

1. Primeiro acesso → assistente de configuração inicial (dados da empresa).
2. Configurações → Redes sociais (opcional).
3. Colaboradores → cadastrar quem vai ter assinatura.
4. Modelos → usar o modelo padrão ("Assinatura Corporativa") ou criar outros.
5. Nova assinatura → escolher colaborador + modelo → pré-visualizar →
   Copiar assinatura (ou Copiar HTML / Exportar HTML) → colar no Novo Outlook.

## 5. Estrutura do projeto

```
gerador-assinaturas/
├── app.py                     # ponto de entrada (porta, navegador, logging)
├── requirements.txt
├── database/database.py       # conexão SQLite, schema, versionamento
├── models/                    # acesso a dados (empresa, colaborador, modelo, ...)
├── routes/                    # blueprints Flask (uma tela = uma rota)
├── services/
│   ├── config_resolver.py     # prioridade: assinatura > modelo > colaborador > empresa > padrão
│   ├── html_service.py        # geração do HTML compatível com Outlook (tabelas + CSS inline)
│   ├── assinatura_service.py  # orquestra a geração da assinatura
│   ├── url_service.py         # validação/teste de URLs de imagem (HTTPS)
│   ├── backup_service.py      # exportar/importar backup (.zip)
│   └── seeds.py                # modelo padrão criado no primeiro uso
├── templates/                 # HTML da aplicação (Bootstrap 5)
├── static/                    # CSS e JS da aplicação (cópia da assinatura, testes de imagem, preview ao vivo)
└── build/build.spec           # spec do PyInstaller
```

## Banner na criação de assinatura

Na tela **Nova assinatura**, marque **Ativar banner** e selecione uma imagem ou informe uma URL HTTPS alternativa. Quando um arquivo é selecionado, ele substitui a URL informada. A largura padrão é **300 px** e pode ser alterada; também é possível configurar link de clique e texto alternativo. O upload local é útil para pré-visualização no gerador, mas para exibição real nos e-mails a imagem precisa estar hospedada em uma URL HTTPS acessível aos destinatários (não use caminho relativo ou localhost).

## Importação de colaboradores por Excel

Na tela **Colaboradores**, utilize **Baixar modelo Excel** para obter a planilha-modelo e **Importar planilha** para cadastrar colaboradores em lote. As colunas obrigatórias são `Nome`, `Sobrenome` e `Cargo`; as demais são opcionais. O arquivo deve estar no formato `.xlsx`. A importação informa as linhas que apresentarem erros.

## 6. Regras importantes já implementadas

- Imagens sempre por **URL HTTPS externa** — nunca Base64, nunca caminho
  local (`C:\...` ou `file://`) na assinatura final.
- HTML da assinatura gerado **apenas com `<table>` e CSS inline** — sem
  Bootstrap, Flexbox, CSS Grid ou JavaScript no resultado exportado.
- Campos vazios do colaborador (ramal, celular, WhatsApp, redes sociais,
  foto etc.) simplesmente não aparecem na assinatura.
- Prioridade de configuração: assinatura específica → modelo → colaborador
  → empresa → padrão do sistema.
- Erros nunca mostram traceback ao usuário; detalhes técnicos vão para
  `logs\app.log`.
- Nenhuma credencial de e-mail/Outlook é armazenada.

## 7. Limitações desta primeira versão

Para manter a entrega enxuta e funcional, ficaram de fora (mas a
arquitetura em blueprints/services já comporta adicionar depois, conforme
previsto no requisito de arquitetura futura):

- Integração com Active Directory / Microsoft 365, gestão multiempresa e
  permissões de usuário.
- Upload de logo/foto para hospedagem própria (o app assume que a imagem já
  está hospedada em algum servidor HTTPS da empresa).
- Editor visual de modelo (o modelo é editado como HTML/Jinja em uma
  textarea, não em um construtor "arrastar e soltar").

## 8. Distribuição remota no Outlook clássico e novo Outlook

A integração foi acrescentada sem remover o fluxo local existente. Ela inclui:

- tela **Distribuição Outlook** (`/distribuicao-outlook/`);
- API protegida por access token do Microsoft Entra ID (`/api/outlook/signature`);
- suplemento Outlook com ativação baseada em evento `OnNewMessageCompose`, que cobre nova mensagem, resposta, responder a todos e encaminhamento, inclusive no Outlook clássico e no novo Outlook compatíveis com Mailbox 1.10;
- comando manual **Atualizar assinatura** no suplemento;
- geração da assinatura atual usando os dados/modelo atuais do Gerador de Assinaturas.

### Importante sobre a arquitetura

O executável continua sendo uma aplicação desktop local. Para que os Outlooks dos funcionários consultem a assinatura, o endpoint e os arquivos estáticos do suplemento precisam estar publicados em uma origem HTTPS alcançável pelas estações. Não exponha diretamente o servidor de desenvolvimento do Flask na Internet. Use um proxy HTTPS/servidor de produção e uma allowlist que publique somente os arquivos do suplemento e `/api/outlook/*`; bloqueie as telas administrativas (`/`, `/colaboradores`, `/modelos`, `/configuracoes`, etc.) para acesso externo. O processo que hospeda a API precisa permanecer disponível.

A implementação do suplemento usa SSO do Office Runtime e validação do token no servidor. Não há chave compartilhada embutida no JavaScript. Antes da produção, a equipe precisa registrar/configurar o aplicativo no Entra ID, conceder consentimento administrativo, configurar HTTPS e validar a audiência real do access token.

### Configurar o Microsoft Entra ID

1. No centro de administração do Entra, registre um aplicativo dedicado ao suplemento.
2. Configure o URI de recurso da API, normalmente `api://<APPLICATION_CLIENT_ID>`, e o escopo delegado necessário para o suplemento/SSO (`access_as_user`) conforme a documentação atual de SSO para suplementos do Outlook.
3. Configure o manifesto do suplemento com o mesmo Client ID e Resource URI. Conceda o consentimento administrativo exigido pela configuração do tenant.
4. Verifique em um ambiente de teste os claims `iss`, `aud`, `tid` e o claim de identidade (`preferred_username`, `upn` ou `email`) do access token emitido para o suplemento.
5. Configure as variáveis de ambiente no Windows que inicia o executável:

```powershell
[Environment]::SetEnvironmentVariable('GERADOR_ENTRA_TENANT_ID', '<TENANT_ID>', 'Machine')
[Environment]::SetEnvironmentVariable('GERADOR_ENTRA_CLIENT_ID', '<APPLICATION_CLIENT_ID>', 'Machine')
[Environment]::SetEnvironmentVariable('GERADOR_ENTRA_AUDIENCE', '<VALOR_EXATO_DO_CLAIM_AUD>', 'Machine')
# Opcional, se o emissor do token não for o padrão v2:
[Environment]::SetEnvironmentVariable('GERADOR_ENTRA_ISSUER', 'https://login.microsoftonline.com/<TENANT_ID>/v2.0', 'Machine')
```

O PowerShell deve ser executado como administrador para gravar variáveis no escopo Machine. Reinicie o executável depois de configurar. Não coloque segredos de cliente no manifesto nem no JavaScript.

### Gerar o manifesto para o seu domínio

Depois de ter uma URL HTTPS pública e o Client ID/Resource URI reais:

```powershell
python tools/configurar_suplemento.py `
  --base-url https://assinaturas.suaempresa.com.br `
  --client-id <APPLICATION_CLIENT_ID> `
  --resource-uri api://<APPLICATION_CLIENT_ID> `
  --output-dir deploy-outlook
```

O script valida a URL HTTPS, gera um GUID para o suplemento e grava `deploy-outlook/manifest.xml` e os arquivos estáticos configurados em `deploy-outlook/static/outlook_addin/`. Publique os arquivos estáticos na mesma origem HTTPS indicada por `--base-url` e valide o manifesto no validador de suplementos do Microsoft 365 antes da implantação. Se o próprio executável hospedar os arquivos, copie os arquivos estáticos gerados para `static/outlook_addin/` antes de reconstruir o executável; se usar um servidor web separado, publique-os nesse servidor e configure o proxy para encaminhar `/api/outlook/*` com segurança para o backend.

### Associação usuário → assinatura

O endpoint identifica o usuário pelo token Microsoft 365 e procura uma assinatura salva, ativa, ligada a um colaborador ativo cujo e-mail coincide com a identidade autenticada. Se houver mais de uma assinatura ativa para o mesmo e-mail, é escolhida a mais recentemente atualizada. Se não houver uma assinatura ativa, a API retorna `404` em vez de aplicar uma assinatura incorreta. A API regenera o HTML a partir do modelo e dos dados atuais; mudanças passam a valer na próxima composição de mensagem.

### Teste e implantação gradual

1. Rode `python -m unittest discover -s tests`.
2. Verifique `/api/outlook/health` e confirme `status: ok` depois de configurar o Entra ID.
3. Teste com uma conta piloto que tenha colaborador ativo, e-mail igual ao Microsoft 365 e assinatura salva/ativa.
4. Valide nova mensagem, responder, responder a todos, encaminhar, alternância entre contas, imagens HTTPS e formatação no Outlook clássico e novo Outlook.
5. Implante o suplemento em **Microsoft 365 Admin Center → Configurações → Aplicativos integrados**, primeiro para um grupo piloto e depois para os grupos restantes.

O suplemento não controla rascunhos antigos já abertos. `OnNewMessageCompose` não dispara ao editar um rascunho existente; para isso, o usuário pode usar o comando manual do suplemento.

## Gerar e editar assinaturas em lote

- Em **Assinaturas salvas**, use **Gerar todas as assinaturas** para criar uma assinatura para cada colaborador ativo que ainda não possua assinatura.
- Se marcar **Atualizar também as assinaturas existentes**, as assinaturas existentes serão regeneradas com o modelo selecionado. As opções personalizadas já salvas são preservadas, mas o modelo escolhido será aplicado a todos os colaboradores processados.
- Na página **Colaboradores**, use **Editar dados** para corrigir os dados cadastrais. As assinaturas ativas desse colaborador são regeneradas automaticamente após salvar.
- Na mesma página, use **Editar assinatura** para alterar modelo e opções específicas (como banner e telefone clicável), ou **Gerar assinatura** para colaboradores que ainda não possuem uma.
- A geração em lote não envia mensagens de e-mail; ela apenas salva/atualiza as assinaturas dentro do gerador.
