# Contexto operacional do Google Maps Free Scraper

## Objetivo
Este repositório é um scraper local autorizado para listas de empresas. O fluxo padrão coleta Google Maps; o fluxo de bairro usa o script dedicado para manter a busca focada na área solicitada.

## Regra de decisão
Quando o usuário informar bairro + cidade + estado, não usar a busca genérica primeiro. Usar:

```bash
python3 scripts/scrape_neighborhood.py "<bairro>" --city "<cidade>" --state "<UF>" --radius 4000 --grid 5 --depth 5 --out results-<bairro>
```

Esse fluxo executa cinco centros controlados, três variações de consulta, deduplicação e filtro estrito por bairro. O CSV principal contém confirmados; `*-excluded.csv` contém resultados rejeitados para auditoria.

Quando o usuário informar apenas cidade/localidade, usar `scripts/scrape.py` ou os comandos Claude existentes.

## Mapa técnico
- `frontend/index.html`, `frontend/app.js`: UI de mapa, geocoding, jobs e resultados.
- `frontend/painel.html`, `frontend/painel.js`: painel e exportações.
- `scripts/scrape.py`: CLI genérica, batch, geocoding e polling.
- `scripts/scrape_neighborhood.py`: CLI focada por bairro.
- `docker-compose.yml`: scraper + proxy local, porta 8080.
- `nginx.conf`, `scraper-proxy.inc`: proxy da API e assets.
- `.claude/skills/google-maps-scraper/SKILL.md`: instruções operacionais para scraping.
- `examples/`: payloads e listas de keywords.
- `graphify-out/`: contexto estrutural gerado pelo Graphify quando o mapa estiver atualizado; não editar manualmente.

## Graphify obrigatório
Antes de responder perguntas sobre código:

1. verificar se `graphify-out/graph.json` ou um snapshot equivalente existe;
2. executar `graphify query "<pergunta>"` quando o grafo existir;
3. usar `graphify path` para relações entre arquivos/símbolos;
4. após alterar código, executar `graphify update .`;
5. nunca inventar conteúdo do grafo se ele estiver ausente.

Se `graphify-out/` não estiver versionado, gerar o mapa localmente no clone e decidir conscientemente se deve ser incluído no commit. O código continua sendo a fonte de verdade.

## Cartographer e REA
Cartographer é auxiliar de contexto, não substitui leitura do código. REA deve separar fato observado, evidência, inferência, hipótese e decisão. Registrar mudanças em `docs/` somente quando necessário.

## Segurança e operação
- Não usar o serviço de outro projeto; o app local de produção usa a porta 8080.
- Para testes isolados, usar porta/projeto Docker separados e endpoint explícito.
- Não publicar, gastar, criar credenciais ou alterar produção sem solicitação.
- Uma busca de cada vez; respeitar limites e legislação.
- Telefones e e-mails são dados pessoais; não despejar grandes CSVs no chat.

## Verificação
Antes de concluir: conferir `git status`, compilar scripts Python, validar payload/endpoint, registrar artefatos e dizer claramente se o teste foi executado ou apenas planejado.
