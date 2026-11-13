# Instalação inicial — VPS Hostinger (Ubuntu 24.04)

Este repositório usa **automação de navegador** (Playwright) para Gemini, Google Flow e TikTok. A instalação na VPS **não garante** que os sites permitam a sessão remota nem que os seletores continuem funcionando. Faça o primeiro login de forma interativa, na sua conta, nunca enviando senhas ou cookies a terceiros.

## 1. Preparar servidor

Use um usuário Linux não-root para executar o bot. No terminal da VPS:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip xvfb libnss3 libatk-bridge2.0-0 libasound2t64
git clone https://github.com/ronnysoares51/auto_video.git
cd auto_video
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install --with-deps chromium
cp .env.example .env
chmod 600 .env
```

Não comite o arquivo `.env`. Edite-o somente na VPS e acrescente:

```dotenv
LOOP_COUNT=1
ENABLE_TIKTOK_PUBLISH=false
# Opcional:
# TELEGRAM_BOT_TOKEN=novo_token
# TELEGRAM_CHAT_ID=seu_chat_id
```

**Aviso de segurança:** a versão original tinha um token de bot do Telegram no `config.py`. O valor foi removido desta cópia, mas o histórico Git pode preservá-lo. Revogue aquele token no BotFather e crie outro, se usar Telegram. Não deixe sessões e perfis do navegador acessíveis publicamente.

## 2. Verificação sem postagem

O fluxo `main.py` exige uma sessão autenticada do Gemini e Google Flow no navegador persistente. A primeira execução precisa de acesso visual à sessão, por exemplo via desktop remoto seguro (não exponha VNC na internet). Um servidor sem interface visual não consegue completar essa etapa apenas com SSH.

Após autenticar as contas de modo seguro, execute:

```bash
cd ~/auto_video
ENABLE_TIKTOK_PUBLISH=false xvfb-run -a .venv/bin/python main.py
```

**Resultado esperado:** quando a geração funcionar, salva o arquivo MP4 em `downloads/` e **não publica** no TikTok. Revise o arquivo manualmente. Se a interface do Google mudar, seletores podem exigir ajustes.

## 3. Agendamento (somente após testes)

O script `run.sh` usa caminhos relativos ao próprio repositório e o ambiente virtual `.venv`. Em servidores sem monitor, o Chromium pode requerer `xvfb-run` e um perfil previamente autenticado. Não habilite um cron até confirmar o funcionamento da sessão. O controle de publicação é:

```dotenv
ENABLE_TIKTOK_PUBLISH=false
```

**Importante:** o projeto automatiza o site do TikTok pelo navegador, não o fluxo oficial TikTok Content Posting API. Não ative publicação não supervisionada sem revisar os requisitos e as regras da plataforma.

## 4. Estado atual

- Código copiado para o GitHub do proprietário.
- `main.py` e `auto_short_video_pipeline.py`: postagem desabilitada por padrão.
- `run.sh`: caminhos compatíveis com Linux.
- `config.py`: variáveis locais via dotenv, sem credenciais Telegram padrão.
- **Pendente:** instalar na VPS, login interativo, geração de teste, revisão de MP4, testes reais de compatibilidade.

