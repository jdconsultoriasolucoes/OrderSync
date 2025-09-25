const form = document.getElementById("formEmail");
const mensagem = document.getElementById("mensagem");

async function carregarConfiguracoes() {
  const resp = await fetch("/config_email");
  if (!resp.ok) return;

  const config = await resp.json();
  document.getElementById("emailPrincipal").value = config.email_principal || "";
  document.getElementById("emailsCopia").value = (config.email_copia || []).join(", ");
  document.getElementById("assuntoPadrao").value = config.assunto || "";
  document.getElementById("corpoPadrao").value = config.corpo || "";
}

form.addEventListener("submit", async function (e) {
  e.preventDefault();

  const payload = {
    email_principal: document.getElementById("emailPrincipal").value,
    email_copia: document.getElementById("emailsCopia").value.split(",").map(e => e.trim()).filter(Boolean),
    assunto: document.getElementById("assuntoPadrao").value,
    corpo: document.getElementById("corpoPadrao").value
  };

  const resp = await fetch("/config_email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (resp.ok) {
    mensagem.textContent = "Configurações salvas com sucesso!";
    mensagem.style.color = "green";
  } else {
    mensagem.textContent = "Erro ao salvar configurações.";
    mensagem.style.color = "red";
  }
});

carregarConfiguracoes();
