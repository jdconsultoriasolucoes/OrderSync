document.querySelectorAll(".mini-card").forEach(card => {
  card.addEventListener("click", () => {
    const id = card.getAttribute("data-target");
    const panel = document.getElementById(id);
    if (panel) {
      panel.classList.remove("hidden");
      panel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
});

// fecha o painel
document.querySelectorAll("[data-close]").forEach(btn => {
  btn.addEventListener("click", () => {
    const panel = btn.closest(".panel");
    if (panel) panel.classList.add("hidden");
  });
});

async function fetchJSON(url) {
  const r = await fetch(url, { method: "GET", cache: "no-store" });
  if (!r.ok) throw new Error("Erro GET " + url);
  return await r.json();
}

async function putJSON(url, data) {
  const r = await fetch(url, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || "Erro PUT " + url);
  }
  return await r.json();
}

// ---------- carregar configs na tela ----------

async function carregarMensagem() {
  try {
    const data = await fetchJSON("/admin/config_email/mensagem");
    document.getElementById("destinatario_interno").value = data.destinatario_interno || "";
    document.getElementById("assunto_padrao").value = data.assunto_padrao || "";
    document.getElementById("corpo_html").value = data.corpo_html || "";
    document.getElementById("enviar_para_cliente").checked = !!data.enviar_para_cliente;
  } catch (e) {
    console.warn("Sem config de mensagem ainda?", e);
  }
}

async function carregarSMTP() {
  try {
    const data = await fetchJSON("/admin/config_email/smtp");
    document.getElementById("remetente_email").value = data.remetente_email || "";
    document.getElementById("smtp_host").value = data.smtp_host || "";
    document.getElementById("smtp_port").value = data.smtp_port || "";
    document.getElementById("smtp_user").value = data.smtp_user || "";
    document.getElementById("usar_tls").checked = !!data.usar_tls;
    // senha não volta por segurança
    document.getElementById("smtp_senha").value = "";
  } catch (e) {
    console.warn("Sem config smtp ainda?", e);
  }
}

// ---------- salvar configs ----------

document.getElementById("btnSalvarMensagem").addEventListener("click", async () => {
  const payload = {
    destinatario_interno: document.getElementById("destinatario_interno").value,
    assunto_padrao: document.getElementById("assunto_padrao").value,
    corpo_html: document.getElementById("corpo_html").value,
    enviar_para_cliente: document.getElementById("enviar_para_cliente").checked
  };
  try {
    await putJSON("/admin/config_email/mensagem", payload);
    alert("Configuração de mensagem salva.");
  } catch (e) {
    alert("Erro ao salvar mensagem: " + e.message);
  }
});

document.getElementById("btnSalvarSMTP").addEventListener("click", async () => {
  const payload = {
    remetente_email: document.getElementById("remetente_email").value,
    smtp_host: document.getElementById("smtp_host").value,
    smtp_port: parseInt(document.getElementById("smtp_port").value || "0", 10),
    smtp_user: document.getElementById("smtp_user").value,
    smtp_senha: document.getElementById("smtp_senha").value || null,
    usar_tls: document.getElementById("usar_tls").checked
  };
  try {
    await putJSON("/admin/config_email/smtp", payload);
    alert("Configuração SMTP salva.");
    // limpa o campo senha depois de salvar
    document.getElementById("smtp_senha").value = "";
  } catch (e) {
    alert("Erro ao salvar SMTP: " + e.message);
  }
});

// inicializa
carregarMensagem();
carregarSMTP();
