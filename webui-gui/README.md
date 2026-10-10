# Aether WebUI GUI

Interface web mínima (container separado) para o WebUI do SD-Core (`5gc-webui:rel-3.1.x`), que só expõe API.
Lista, visualiza, edita (JSON), cria e exclui slices, device groups e assinantes; lista gNBs e UPFs.

```bash
docker build -t aether-webui-gui .
docker run -d --name aether-webui-gui --restart unless-stopped -p 8088:8088 \
  -e WEBUI_URL=http://<ip-do-no>:30500 \
  -e GUI_USER=admin -e GUI_PASSWORD='<senha>' \
  aether-webui-gui
```

Abra `http://<host>:8088/`.

Documentação interativa da API: `http://<host>:8088/docs`. O documento
OpenAPI fica disponível em `http://<host>:8088/openapi.json`; o botão
**API Swagger** na GUI abre o Swagger UI. A interface Swagger carrega
seus recursos estáticos do unpkg, então o navegador precisa ter acesso a
`unpkg.com`. As operações são encaminhadas pelo proxy da GUI e respeitam
`GUI_USER`/`GUI_PASSWORD` e `READ_ONLY`.

| Variável | Padrão | Função |
|---|---|---|
| `WEBUI_URL` | `http://172.30.255.119:30500` | NodePort `urlport-http` do WebUI |
| `GUI_USER` / `GUI_PASSWORD` | vazio | Basic auth (desligado se vazio) |
| `READ_ONLY` | `false` | `true` bloqueia POST/PUT/DELETE |
| `PORT` | `8088` | Porta do container |

A API do WebUI não tem autenticação e devolve chaves de assinantes em texto claro. Use `GUI_USER`/`GUI_PASSWORD` e restrinja a porta por firewall.
