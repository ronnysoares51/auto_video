# Bot Telegram — controle de vídeos

O arquivo `telegram_bot.py` permite gerar um vídeo pelo pipeline do Gemini + Google Flow, consultar o estado da execução e receber os MP4 para revisão dentro do Telegram.

## Configuração

1. No Telegram, fale com o bot oficial **@BotFather** e use `/newbot`. Guarde o token de forma privada.
2. Abra uma conversa privada com seu novo bot e envie `/start`.
3. Descubra seu `chat_id` usando o endpoint `getUpdates` do **seu novo bot**, depois de enviar uma mensagem. Não compartilhe o token ou a resposta integral.
4. Na VPS, execute `cp .env.example .env` se ainda não houver `.env` e edite nele:
   ```dotenv
   TELEGRAM_BOT_TOKEN=SEU_TOKEN_PRIVADO
   TELEGRAM_CHAT_ID=SEU_CHAT_ID
   ENABLE_TIKTOK_PUBLISH=false
   LOOP_COUNT=1
   ```
5. Dentro da pasta do projeto, com o ambiente virtual instalado:
   ```bash
   .venv/bin/python telegram_bot.py
   ```
6. No Telegram, experimente `/status` e `/gerar`.

## Comandos

- `/start`, `/ajuda`: lista os comandos.
- `/status`: indica se o processo está em execução e o último resultado.
- `/gerar`: cria **um** vídeo com as configurações existentes. O vídeo fica em `downloads/` e é enviado ao chat autorizado quando possível.
- `/ultimos`: envia até três MP4 recentes da pasta `downloads/`.

O bot **não publica** no TikTok, ainda que outras configurações do processo indiquem o contrário, e só atende ao `TELEGRAM_CHAT_ID`. O envio de MP4 usa o limite de tamanho da API Bot em nuvem (50 MB por `sendVideo`). Vídeos maiores permanecem na VPS.

## Execução na VPS

O processo principal usa Playwright e navegador Chromium **com interface visual** (`HEADLESS=False`). Para uma VPS sem desktop é necessário configurar um display virtual e autenticar a sessão do Google com acesso visual seguro. Veja `HOSTINGER_SETUP.md`. O comando `/gerar` não funcionará sem essa configuração.

O bot usa **long polling** (getUpdates), portanto execute **somente uma instância** desse bot por token. Caso exista um webhook previamente configurado no mesmo token, desative-o antes do polling.

Este código foi incluído no GitHub, mas **não foi implantado ou testado em uma VPS**. O comando `/gerar` pode falhar se o Google Flow mudar a interface, se os logins expirarem ou se as dependências não estiverem prontas. Veja `logs/telegram_generation.log`.

**Segurança:** a versão original do projeto tinha um token do Telegram no histórico Git. Revogue qualquer token antigo no BotFather; gere um novo token. Nunca salve credenciais no repositório público.
