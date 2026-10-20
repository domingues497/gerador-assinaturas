// Execute tools/configurar_suplemento.py para preencher a URL HTTPS da API antes da publicação.
const GERADOR_API_BASE_URL = "https://CONFIGURE-ESTE-ENDERECO";
Office.actions.associate("onNewMessageComposeHandler", function(event) { event.completed(); });
