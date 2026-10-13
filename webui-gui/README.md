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

Pelo Makefile da raiz (constrói a imagem e recria o container):

```bash
make aether-webui-gui-start
make aether-webui-gui-start WEBUI_GUI_UPSTREAM=http://<ip-do-no>:30500 \
  WEBUI_GUI_USER=admin WEBUI_GUI_PASSWORD='<senha>' WEBUI_GUI_READ_ONLY=true
make aether-webui-gui-logs   # acompanha os logs
make aether-webui-gui-stop   # remove o container
```

Variáveis: `WEBUI_GUI_UPSTREAM`, `WEBUI_GUI_PORT` (8088), `WEBUI_GUI_USER`,
`WEBUI_GUI_PASSWORD`, `WEBUI_GUI_READ_ONLY`, `WEBUI_GUI_IMAGE`, `WEBUI_GUI_CONTAINER`.

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
