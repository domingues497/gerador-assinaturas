# Publicar no Git e executar no Ubuntu (sem .exe)

## Antes de publicar no Git

1. Revise `.gitignore`: bancos SQLite, `.env`, logs, `.venv`, `.exe` e uploads de usuários ficam fora do repositório.
2. Não comite dados pessoais de colaboradores, banco de produção, tokens, chaves ou o arquivo real de ambiente.
3. Se precisar levar os banners/logos já enviados e referenciados pelo banco atual, faça backup e transfira `static/uploads/` separadamente para o servidor. Eles não são enviados ao Git.
4. O diretório de dados SQLite no Ubuntu é `~/.geradorassinaturas/assinaturas.db` para o usuário que executa o serviço. Faça backup antes de migrações ou atualizações.

## Dependências e execução local no Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
cd /opt/gerador-assinaturas
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m unittest discover -s tests
```

O projeto é servido por Gunicorn usando `wsgi:app`; não execute `python app.py` em produção, pois esse modo é voltado à execução local e tenta abrir o navegador.

## Serviço systemd

O exemplo `deploy/gerador-assinaturas.service.example` espera o código em `/opt/gerador-assinaturas`, um usuário Linux `gerador`, e escuta apenas em `127.0.0.1:8017` para que o Nginx ou outro proxy reverso existente possa encaminhar as requisições. Ajuste caminhos/usuário/porta conforme o servidor.

Crie o arquivo de ambiente fora do Git: `/etc/gerador-assinaturas.env`. Gere uma chave aleatória para `GERADOR_SECRET_KEY`, por exemplo com `python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`. Defina permissões restritas no arquivo. Configure `GERADOR_ENTRA_TENANT_ID`, `GERADOR_ENTRA_CLIENT_ID` e `GERADOR_ENTRA_AUDIENCE` apenas quando o aplicativo Entra ID estiver configurado.

Copie o serviço para `/etc/systemd/system/gerador-assinaturas.service`, depois execute:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now gerador-assinaturas
sudo systemctl status gerador-assinaturas
sudo journalctl -u gerador-assinaturas -n 100 --no-pager
curl -i http://127.0.0.1:8017/api/outlook/health
```

## Atualizar depois de um `git push`

```bash
cd /opt/gerador-assinaturas
git pull
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests
sudo systemctl restart gerador-assinaturas
sudo systemctl status gerador-assinaturas
```

## Proxy HTTPS e segurança

Configure o domínio e HTTPS no proxy reverso existente. A API do Outlook e os arquivos do suplemento precisam ser acessíveis por HTTPS. Não exponha diretamente o Flask/Gunicorn na Internet.

**Importante:** as telas administrativas deste projeto não têm autenticação de usuário implementada nesta versão. Não publique as telas de administração na Internet aberta. Restrinja-as à rede interna/VPN ou por controle de acesso no proxy até implementar autenticação. Publique externamente apenas as rotas/arquivos estritamente necessários para o suplemento, depois de validar a configuração Entra ID e as regras de proxy.

## Banco de dados e uploads

A inicialização WSGI cria as tabelas e o modelo padrão se o banco estiver vazio. Isso não migra automaticamente o banco que está no computador Windows. Para preservar colaboradores/modelos, faça backup pelo recurso de backup do aplicativo e planeje a restauração no servidor; não comite o `.db` no Git. Os uploads ficam em `static/uploads/`, fora do Git, e precisam de cópia separada se forem necessários.
