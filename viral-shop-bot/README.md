# Viral Shop Bot

Robô independente para pesquisar oportunidades de produtos em TikTok Shop/Shopee, montar vídeos verticais usando **imagens reais autorizadas** e entregar MP4 + legenda ao Telegram. Publicação final é manual.

## Estado
**Base inicial instalada no repositório, não executada na VPS.** Esta versão já contém um pipeline funcional para gerar vídeo a partir de produtos com URLs de imagens fornecidas em um feed JSON. A mineração automática em TikTok Shop e Shopee **ainda precisa de adaptadores de dados confiáveis**, e não é simulada como pronta.

## Como executar
1. Copie `.env.example` para `.env` e preencha TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
2. Cadastre produtos e URLs de fotos autorizadas no arquivo `data/products.json` (exemplo disponível). Cada item deve possuir `image_rights_confirmed: true`; só indique true após obter direito de uso.
3. Rode `docker compose up --build -d` **dentro deste diretório**. A execução de desenvolvimento é manual: `docker compose run --rm bot python main.py`.
4. Para produção, a automação de agendamento e a integração com dados reais serão ativadas após validar as fontes e as credenciais.

## Segurança e operação
- Não comitar credenciais. `.env` está no .gitignore.
- Os arquivos são separados do restante do repositório `auto_video`.
- A ferramenta **não** publica vídeos no TikTok ou na Shopee.
- Links de imagem são validados e bloqueiam endereços internos para evitar SSRF. Não use imagens de terceiros sem autorização.
- Não inclui integração com Claude, Gemini ou APIs de vídeo por enquanto. A montagem inicial é com FFmpeg.

## Próximas etapas
- Adaptadores oficiais ou autorizados para catálogo e métricas de TikTok Shop e Shopee;
- ranking por crescimento e evidências comerciais disponíveis, com deduplicação;
- geração original de roteiros e narração PT-BR;
- agendador para três entregas diárias, logs, alertas e painel.
