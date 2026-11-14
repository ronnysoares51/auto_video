# Viral Shop Bot — pesquisa → análise → vídeo → Telegram

Projeto isolado em `auto_video/viral-shop-bot`; nenhum outro bot é modificado.
**Estado: código versionado no GitHub; NÃO instalado na VPS.**

## O que funciona neste estágio
- Recebe um feed JSON de produtos com **fotos com direito de uso confirmado**.
- Classifica candidatos por volume de visualizações, taxa de curtidas, vendas informadas e crescimento informado; não inventa métricas ausentes.
- Evita reenvios pela URL do produto (histórico persistente em `output/history.json`).
- Monta slideshow de 15 segundos, 1080x1920, usando FFmpeg e imagens originais.
- Envia o vídeo por bot do Telegram com link e score estimado.
- Agenda **uma geração em cada um dos horários 08h, 13h e 19h** (America/Sao_Paulo), salvo falha, falta de produtos ou credenciais. O registro do slot evita repetição por reinício.

## O que AINDA não funciona
- Mineração autônoma de TikTok Shop/Shopee: falta conectar fontes autorizadas com URLs, métricas e direitos de uso.
- Roteirização com IA, narração PT-BR, música, hashtags e legendas dinâmicas.
- Conexão direta ou implantação na VPS. Não há credenciais de Telegram nem de fontes comerciais no código.

## Preparar na VPS quando autorizado
```bash
git clone https://github.com/ronnysoares51/auto_video.git
cd auto_video/viral-shop-bot
cp .env.example .env
# Preencha TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID diretamente na VPS (nunca no GitHub)
mkdir -p output
sudo chown 10001:10001 output
docker compose up -d --build
docker compose logs -f bot
```
O serviço usa apenas imagens cadastradas no arquivo `data/products.json`. Com o exemplo vazio, nada é enviado. A VPS deve ter Docker Compose e acesso à internet.

## Executar uma vez / testar
```bash
docker compose run --rm bot python main.py
docker compose run --rm --no-deps --entrypoint python bot -m unittest discover -s tests
```
Para o teste de Python fora do contêiner, execute `python -m unittest discover -s tests` no diretório do bot. Testes ficam em `tests/` e a imagem de produção não os copia.

## Formato de entrada
```json
[
  {
    "name": "Produto exemplo",
    "product_url": "https://loja.exemplo.com/produto/123",
    "image_urls": ["https://cdn.exemplo.com/foto1.jpg"],
    "image_rights_confirmed": true,
    "views": 10000,
    "likes": 500,
    "sales": 22,
    "growth_pct": 45,
    "caption": "Conheça o produto"
  }
]
```
`views`, `likes`, `sales` e `growth_pct` são opcionais e devem ser dados verificáveis de uma fonte real. `image_rights_confirmed` não deve ser marcado como true sem permissão.

## Segurança
- Credenciais fora do controle de versão (`.env` ignorado).
- Links de imagens HTTPS, sem redirecionamentos e com validação prévia de IP público; para proteção de produção contra DNS rebinding, a rede da VPS também precisa bloquear egressos para endereços privados.
- Nenhuma postagem automática em TikTok ou Shopee.
- O score é **heurístico**, não uma previsão comprovada de vendas.

## Próximo trabalho
Conectar feeds oficiais/autorizados do TikTok Shop e Shopee, IA de roteiros, voz PT-BR e revisão de qualidade. A integração deve respeitar permissões e disponibilidade das APIs de cada plataforma.
