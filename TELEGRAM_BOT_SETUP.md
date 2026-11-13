# Publicação automática no Telegram

1. Crie um bot no **@BotFather** e adicione-o como administrador do canal com permissão para publicar mensagens.
2. Defina as variáveis no ambiente do processo ou no arquivo privado `.env` da raiz do projeto:

   ```dotenv
   TELEGRAM_BOT_TOKEN=SEU_TOKEN_PRIVADO
   TELEGRAM_CHANNEL_ID=@seu_canal
   ENABLE_TIKTOK_PUBLISH=false
   ```

   Para canal privado, use o ID numérico do canal, por exemplo `-1001234567890`. Use sempre o mesmo identificador para o mesmo canal. Deixe `TELEGRAM_CHANNEL_ID` vazio para desativar a publicação automática.
3. Execute `python main.py` com o ambiente virtual do projeto. O agendamento existente com `run.sh` usa o mesmo fluxo. Cada MP4 gerado com sucesso é enviado com a legenda do ciclo.

O histórico fica em `logs/telegram_publications.sqlite3`. Preserve esse arquivo entre execuções. A proteção usa o conteúdo do MP4 e o identificador do canal, inclusive em execuções concorrentes que compartilham o banco. O pipeline repete timeouts de conexão e respostas de limite de taxa com espera de até 60 segundos. Se o envio ficar sem confirmação, confira o canal e os logs antes de reenviar manualmente. O MP4 permanece em `downloads/`.

## Controle privado opcional

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
- `/gerar`: cria **um** vídeo com as configurações existentes. Com um canal configurado, o pipeline publica nele. Com o canal vazio, o bot envia o vídeo ao chat autorizado para revisão quando possível.
- `/ultimos`: envia até três MP4 recentes da pasta `downloads/`.

O bot **não publica** no TikTok, ainda que outras configurações do processo indiquem o contrário, e só atende ao `TELEGRAM_CHAT_ID`. O envio de MP4 usa o limite de tamanho da API Bot em nuvem (50 MB por `sendVideo`). Vídeos maiores permanecem na VPS.

## Execução na VPS

O processo principal usa Playwright e navegador Chromium **com interface visual** (`HEADLESS=False`). Para uma VPS sem desktop é necessário configurar um display virtual e autenticar a sessão do Google com acesso visual seguro. Veja `HOSTINGER_SETUP.md`. O comando `/gerar` não funcionará sem essa configuração.

O bot usa **long polling** (getUpdates), portanto execute **somente uma instância** desse bot por token. Caso exista um webhook previamente configurado no mesmo token, desative-o antes do polling.

Este código foi incluído no GitHub, mas **não foi implantado ou testado em uma VPS**. O comando `/gerar` pode falhar se o Google Flow mudar a interface, se os logins expirarem ou se as dependências não estiverem prontas. Veja `logs/telegram_generation.log`.

**Segurança:** a versão original do projeto tinha um token do Telegram no histórico Git. Revogue qualquer token antigo no BotFather; gere um novo token. Nunca salve credenciais no repositório público.
