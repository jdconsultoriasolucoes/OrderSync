console.info("[config_email] build tab-9 carregado");

// ================== AUTO-DETECÇÃO DE ENDPOINTS ==================
const CANDIDATES = [
  "/admin/config_email",
  "/config/email",
  "/admin_config_email",
  "/admin/config_email",
  "/api/config/email",
  "/email/config",
  "/config_email"
];

let ENDPOINTS = null;

async function probeBase(base) {
  try {
    const u1 = `${base}/mensagem`;
    const u2 = `${base}/smtp`;
    const [r1, r2] = await Promise.allSettled([
      fetch(u1, { cache: "no-store" }),
      fetch(u2, { cache: "no-store" }),
    ]);
    const ok1 = r1.status === "fulfilled" && (r1.value.status === 200 || r1.value.status === 204);
    const ok2 = r2.status === "fulfilled" && (r2.value.status === 200 || r2.value.status === 204);
    return ok1 && ok2;
  } catch { return false; }
}

async function detectEndpoints() {
  // 1) Se o HTML já definiu, usa e sai
  if (window.CONFIG_EMAIL_ENDPOINTS) {
    ENDPOINTS = window.CONFIG_EMAIL_ENDPOINTS;
    console.info("[config_email] endpoints forçados via HTML:", ENDPOINTS);
    return;
  }

  // 2) Caso não tenha sido forçado, roda o autodetector como fallback
  try {
    for (const base of CANDIDATES) {
      const ok = await probeBase(base);
      if (ok) {
        ENDPOINTS = {
          mensagem:    `${base}/mensagem`,
          smtp:        `${base}/smtp`,
          testarEnvio: `${base}/teste_envio`,
          // OBS: não há /smtp/teste no seu backend
        };
        console.info("[config_email] autodetect:", ENDPOINTS);
        return;
      }
    }
  } catch (e) {
    console.error("[config_email] detect erro:", e);
  }

  console.error("[config_email] Nenhum endpoint válido encontrado. Ajuste CONFIG_EMAIL_ENDPOINTS no HTML.");
  alert("Não foi possível localizar os endpoints da Configuração de E-mail.");
}

// === Tabs ========================================================
function initTabs(){
  document.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.tab;
      document.querySelectorAll(".tab").forEach(b => b.classList.toggle("active", b === btn));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("active", p.id === id));
    });
  });
}

// === Helpers =====================================================
async function getJSON(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (r.status === 204) return null;
  if (!r.ok) throw new Error(`HTTP ${r.status} em GET ${url}`);
  return await r.json();
}
async function putJSON(url, data) {
  const r = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  if (!r.ok) throw new Error(`HTTP ${r.status} em PUT ${url}`);
  return await r.json().catch(() => ({}));
}
function setVal(id, v)   { const el = document.getElementById(id); if (el) el.value = v ?? ""; }
function setCheck(id, v) { const el = document.getElementById(id); if (el) el.checked = !!v; }
function getVal(id)      { return (document.getElementById(id)?.value ?? "").trim(); }
function getCheck(id)    { return !!document.getElementById(id)?.checked; }
function toast(ok, msg)  { alert(msg || (ok ? "Salvo!" : "Falhou")); }
function normalizeAppPassword(pwd) { return (pwd || "").replace(/\s+/g, ""); }

// === Fluxo principal =============================================
async function init() {
  initTabs();
  await detectEndpoints();
  if (!ENDPOINTS) return;

  // Normalizador da senha (sem variáveis globais)
  const senhaEl = document.getElementById("smtp_senha");
  if (senhaEl) {
    senhaEl.addEventListener("input", (e) => {
      const cur = e.target.selectionStart;
      e.target.value = normalizeAppPassword(e.target.value);
      e.target.setSelectionRange(cur, cur);
    });
  }

  // Bind botões
  document.getElementById("btnSalvarMensagem").addEventListener("click", salvarMensagem);
  document.getElementById("btnTestarEnvio").addEventListener("click", testarEnvio);
  document.getElementById("btnSalvarSMTP").addEventListener("click", salvarSMTP);
  document.getElementById("btnTestarSMTP").addEventListener("click", testarSMTP);

  // Carregar dados
  await Promise.allSettled([carregarMensagem(), carregarSMTP()]);
}

// === Mensagem ====================================================
async function carregarMensagem() {
  try {
    const d = await getJSON(ENDPOINTS.mensagem);
    setVal("destinatario_interno", d?.destinatario_interno || "");
    setVal("assunto_padrao", d?.assunto_padrao || "Novo pedido {{pedido_id}}");
    setVal("corpo_html", d?.corpo_html || "");
    setCheck("enviar_para_cliente", d?.enviar_para_cliente ?? false);
  } catch (e) { console.error("Erro ao carregar mensagem:", e); }
}

async function salvarMensagem() {
  const payload = {
    destinatario_interno: getVal("destinatario_interno"),
    assunto_padrao: getVal("assunto_padrao"),
    corpo_html: getVal("corpo_html"),
    enviar_para_cliente: getCheck("enviar_para_cliente")
  };
  try {
    await putJSON(ENDPOINTS.mensagem, payload);
    toast(true, "Mensagem salva.");
  } catch (e) {
    console.error(e);
    toast(false, "Falha ao salvar mensagem.");
  }
}

async function testarEnvio() {
  try {
    const r = await fetch(ENDPOINTS.testarEnvio, { method:"POST" });
    const ok = r.ok;
    const t  = await r.text().catch(()=> "");
    toast(ok, ok ? "E-mail de teste enviado." : `Falha no teste de envio. ${t}`);
  } catch(e){
    console.error(e);
    toast(false, "Erro ao testar envio (ver console).");
  }
}

// === SMTP ========================================================
async function carregarSMTP() {
  try {
    const d = await getJSON(ENDPOINTS.smtp);
    setVal("remetente_email", d?.remetente_email || "");
    setVal("smtp_host", d?.smtp_host || "");
    setVal("smtp_port", d?.smtp_port ?? 587);
    setVal("smtp_user", d?.smtp_user || "");
    setVal("smtp_senha", d?.smtp_senha || "");
    setCheck("usar_tls", d?.usar_tls ?? true);
  } catch (e) { console.error("Erro ao carregar SMTP:", e); }
}

async function salvarSMTP() {
  const payload = {
    remetente_email: getVal("remetente_email"),
    smtp_host: getVal("smtp_host"),
    smtp_port: Number(getVal("smtp_port")) || 587,
    smtp_user: getVal("smtp_user"),
    smtp_senha: normalizeAppPassword(getVal("smtp_senha")),
    usar_tls: getCheck("usar_tls")
  };
  try {
    await putJSON(ENDPOINTS.smtp, payload);
    toast(true, "Configuração SMTP salva.");
  } catch (e) {
    console.error(e);
    toast(false, "Falha ao salvar SMTP.");
  }
}

async function testarSMTP() {
  try {
    const host = getVal("smtp_host");
    const port = Number(getVal("smtp_port")) || 587;

    if (!host) throw new Error("Informe o host SMTP.");
    if (!window.NETDIAG_BASE) throw new Error("NETDIAG_BASE não definido no HTML.");

    const url = `${window.NETDIAG_BASE}/netcheck?host=${encodeURIComponent(host)}&port=${port}&timeout=10`;
    const r = await fetch(url, { cache: "no-store" });

    if (!r.ok) {
      const t = await r.text().catch(() => "");
      throw new Error(`HTTP ${r.status} – ${t || "falha no netcheck"}`);
    }
    toast(true, "Conexão SMTP OK (netcheck).");
  } catch (e) {
    console.error(e);
    toast(false, `Falha no teste SMTP: ${e.message || e}`);
  }
}

document.addEventListener("DOMContentLoaded", init);
