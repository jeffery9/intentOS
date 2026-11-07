/* ============================================================
 * IntentOS Web Console — Codex / Cursor inspired UX
 *  - 意图对话（流式步骤轨迹 + 打字机效果）
 *  - / 命令面板、快捷键、历史记录
 *  - 任务流视图、系统监控视图、右侧检查器
 * ============================================================ */
(() => {
  "use strict";

  const $ = (s) => document.querySelector(s);
  const HISTORY_KEY = "intentos_chat_history";
  const THEME_KEY = "intentos_theme";

  // ---------- API（经由 Web Console 服务端代理，浏览器零密钥） ----------
  async function api(method, path, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    let json;
    try { json = await res.json(); } catch { throw new Error(`HTTP ${res.status}`); }
    if (!res.ok || json.status === "error") {
      throw new Error(json.error || `HTTP ${res.status}`);
    }
    return json;
  }

  // ---------- Toast ----------
  function toast(text, kind = "") {
    const el = document.createElement("div");
    el.className = `toast ${kind}`;
    el.textContent = text;
    $("#toasts").appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity .3s"; }, 2600);
    setTimeout(() => el.remove(), 3000);
  }

  // ---------- Theme ----------
  function applyTheme(t) {
    document.documentElement.dataset.theme = t;
    localStorage.setItem(THEME_KEY, t);
  }
  applyTheme(localStorage.getItem(THEME_KEY) || "dark");
  $("#theme-toggle").addEventListener("click", () => {
    applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  });

  // ---------- View switching ----------
  const viewTitles = { chat: "意图对话", tasks: "任务流", monitor: "系统监控" };
  function switchView(name) {
    document.querySelectorAll(".ab-btn[data-view]").forEach((b) =>
      b.classList.toggle("active", b.dataset.view === name));
    document.querySelectorAll(".view").forEach((v) =>
      v.classList.toggle("active", v.id === `view-${name}`));
    $("#view-title").textContent = viewTitles[name];
    if (name === "monitor") refreshMonitor();
  }
  document.querySelectorAll(".ab-btn[data-view]").forEach((b) =>
    b.addEventListener("click", () => switchView(b.dataset.view)));

  // ---------- Connection status ----------
  async function ping() {
    const dot = $("#conn-pill .dot"), txt = $("#conn-text");
    try {
      await api("GET", "/web-api/health");
      dot.className = "dot online"; txt.textContent = "内核在线";
      return true;
    } catch (e) {
      dot.className = "dot offline"; txt.textContent = "离线";
      return false;
    }
  }
  setInterval(ping, 15000);
  ping();

  // ---------- Sidebar inspector ----------
  const appEl = $(".app");
  $("#sb-close").addEventListener("click", () => appEl.classList.remove("sb-open"));
  function inspect(record) {
    const body = $("#sb-body");
    body.innerHTML = "";
    const mk = (title, content) => {
      const sec = document.createElement("div");
      sec.className = "sb-section";
      const h = document.createElement("h4"); h.textContent = title;
      const pre = document.createElement("pre"); pre.className = "sb-pre mono";
      pre.textContent = content;
      sec.append(h, pre); body.appendChild(sec);
    };
    mk("意图 (Intent)", record.intent);
    mk("执行轨迹 (Steps)", record.steps.map((s, i) => `${i + 1}. ${s.label} — ${s.state}`).join("\n"));
    mk("响应 (Raw)", record.raw);
    mk("元数据", `时间: ${record.time}\n状态: ${record.ok ? "success" : "error"}\n耗时: ${record.ms} ms`);
    appEl.classList.add("sb-open");
  }

  // ---------- Chat state ----------
  const messagesEl = $("#messages");
  const scrollEl = $("#chat-scroll");
  let history = [];
  try { history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); } catch {}
  let busy = false;
  let lastRecord = null;

  function saveHistory() {
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-60))); } catch {}
  }

  function addUserMsg(text) {
    $("#welcome").style.display = "none";
    const div = document.createElement("div");
    div.className = "msg msg-user";
    const bub = document.createElement("div");
    bub.className = "bubble"; bub.textContent = text;
    div.appendChild(bub); messagesEl.appendChild(div);
    scrollBottom();
  }

  function addAgentMsg() {
    const div = document.createElement("div");
    div.className = "msg msg-agent";
    div.innerHTML = `
      <div class="avatar">◐</div>
      <div class="agent-body">
        <div class="agent-name">IntentOS · semantic-vm</div>
        <div class="steps"></div>
        <div class="answer caret"></div>
        <div class="meta-row" style="display:none">
          <span class="t-time"></span>
          <button class="link-btn btn-detail">详情 →</button>
          <button class="link-btn btn-copy">复制</button>
        </div>
      </div>`;
    messagesEl.appendChild(div);
    scrollBottom();
    return div;
  }

  function scrollBottom() { scrollEl.scrollTop = scrollEl.scrollHeight; }

  const STEP_DEFS = [
    { id: "parse", label: "解析意图 (Intent Parser)" },
    { id: "compile", label: "编译为 PEF (Semantic Compiler)" },
    { id: "execute", label: "语义 VM 执行 (LLM Processor)" },
    { id: "respond", label: "生成响应" },
  ];

  function setStep(root, id, state) {
    const stepsEl = root.querySelector(".steps");
    let el = stepsEl.querySelector(`[data-step="${id}"]`);
    if (!el) {
      el = document.createElement("div");
      el.className = "step"; el.dataset.step = id;
      el.innerHTML = `<i class="s-dot"></i><span>${STEP_DEFS.find((s) => s.id === id).label}</span>`;
      stepsEl.appendChild(el);
    }
    el.classList.remove("run", "done", "fail");
    if (state) el.classList.add(state);
    scrollBottom();
  }

  function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

  async function typeOut(el, text) {
    // 打字机效果：长文本按块输出，避免逐字符卡顿
    const chunk = Math.max(2, Math.ceil(text.length / 90));
    for (let i = 0; i < text.length; i += chunk) {
      el.textContent = text.slice(0, i + chunk);
      if (i % (chunk * 8) === 0) scrollBottom();
      await sleep(8);
    }
    el.textContent = text;
    el.classList.remove("caret");
    scrollBottom();
  }

  // ---------- Tasks registry ----------
  const tasksBody = $("#tasks-body");
  function renderTaskRow(rec) {
    $("#tasks-empty").style.display = "none";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="mono">#${rec.seq}</td>
      <td>${rec.time}</td>
      <td>${rec.intent.length > 42 ? rec.intent.slice(0, 42) + "…" : rec.intent}</td>
      <td><span class="badge ${rec.ok ? "ok" : "err"}">${rec.ok ? "成功" : "失败"}</span></td>
      <td>${rec.ms} ms</td>
      <td>${rec.raw.length > 70 ? rec.raw.slice(0, 70) + "…" : rec.raw}</td>`;
    tr.style.cursor = "pointer";
    tr.addEventListener("click", () => { switchView("chat"); inspect(rec); });
    tasksBody.prepend(tr);
  }
  $("#clear-tasks").addEventListener("click", () => {
    tasksBody.innerHTML = ""; $("#tasks-empty").style.display = "";
  });

  // ---------- Send / execute ----------
  const inputEl = $("#input");
  const sendBtn = $("#send");

  function autoGrow() {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 180) + "px";
    sendBtn.disabled = !inputEl.value.trim() || busy;
  }
  inputEl.addEventListener("input", () => { autoGrow(); updateCmdk(); });

  async function send(text) {
    text = (text ?? inputEl.value).trim();
    if (!text || busy) return;
    busy = true; sendBtn.disabled = true;
    inputEl.value = ""; autoGrow(); closeCmdk();

    addUserMsg(text);
    const root = addAgentMsg();
    const answerEl = root.querySelector(".answer");
    const metaEl = root.querySelector(".meta-row");
    const t0 = performance.now();

    setStep(root, "parse", "run");
    await sleep(220); setStep(root, "parse", "done");
    setStep(root, "compile", "run");
    await sleep(180); setStep(root, "compile", "done");
    setStep(root, "execute", "run");

    let raw, ok = true;
    try {
      const data = await api("POST", "/web-api/execute", { intent: text });
      // 兼容两种响应形态：网关 {result} / RPC 代理 {status, result}
      const result = data.result !== undefined ? data.result : data;
      raw = typeof result === "string" ? result : JSON.stringify(result, null, 2);
      if (/^❌/.test(raw)) ok = false;
    } catch (e) {
      ok = false; raw = `请求失败：${e.message}`;
      toast(e.message, "error");
    }

    const ms = Math.round(performance.now() - t0);
    setStep(root, "execute", ok ? "done" : "fail");
    setStep(root, "respond", "done");
    if (!ok) answerEl.classList.add("err");

    const rec = {
      seq: (history.filter((h) => h.role === "user").length),
      time: new Date().toLocaleTimeString(),
      intent: text, ok, ms, raw,
      steps: STEP_DEFS.map((s) => ({ label: s.label, state: ok || s.id !== "execute" ? (s.id === "execute" && !ok ? "failed" : "done") : "failed" })),
    };
    lastRecord = rec;
    history.push({ role: "user", content: text }, { role: "system", content: raw });
    saveHistory();
    renderTaskRow({ ...rec, seq: tasksBody.children.length + 1 });

    await typeOut(answerEl, raw);
    metaEl.style.display = "";
    metaEl.querySelector(".t-time").textContent = `${ms} ms`;
    root.querySelector(".btn-detail").addEventListener("click", () => inspect(rec));
    root.querySelector(".btn-copy").addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(raw); toast("已复制到剪贴板", "success"); }
      catch { toast("复制失败", "error"); }
    });

    busy = false; autoGrow(); inputEl.focus();
  }

  sendBtn.addEventListener("click", () => send());

  // ---------- 历史翻阅 (↑↓) ----------
  let histIdx = -1;
  const userHist = () => history.filter((h) => h.role === "user").map((h) => h.content);

  // ---------- 命令面板 ----------
  const CMDS = [
    { cmd: "/status", desc: "查看内核状态", run: () => send("查看系统状态") },
    { cmd: "/nodes", desc: "列出集群节点", run: () => switchView("monitor") },
    { cmd: "/tasks", desc: "打开任务流", run: () => switchView("tasks") },
    { cmd: "/clear", desc: "清空当前会话显示", run: clearChat },
    { cmd: "/theme", desc: "切换明暗主题", run: () => $("#theme-toggle").click() },
    { cmd: "/help", desc: "查看可用意图示例", run: showHelp },
  ];
  const cmdkEl = $("#cmdk"), cmdkList = $("#cmdk-list");
  let cmdkSel = 0, cmdkOpen = false;

  function updateCmdk() {
    const v = inputEl.value;
    if (!v.startsWith("/")) return closeCmdk();
    const q = v.slice(1).toLowerCase();
    const items = CMDS.filter((c) => c.cmd.slice(1).startsWith(q));
    if (!items.length) return closeCmdk();
    cmdkOpen = true; cmdkEl.hidden = false;
    cmdkSel = Math.min(cmdkSel, items.length - 1);
    cmdkList.innerHTML = "";
    items.forEach((c, i) => {
      const d = document.createElement("div");
      d.className = "cmdk-item" + (i === cmdkSel ? " sel" : "");
      d.innerHTML = `<span class="cmd mono">${c.cmd}</span><span>${c.desc}</span>`;
      d.addEventListener("mousedown", (e) => { e.preventDefault(); runCmd(c); });
      cmdkList.appendChild(d);
    });
    cmdkList._items = items;
  }
  function closeCmdk() { cmdkOpen = false; cmdkEl.hidden = true; cmdkSel = 0; }
  function runCmd(c) { closeCmdk(); inputEl.value = ""; autoGrow(); c.run(); }

  // ---------- helpers ----------
  function clearChat() {
    messagesEl.innerHTML = "";
    $("#welcome").style.display = "";
    history = []; saveHistory();
    toast("会话已清空", "success");
  }
  function showHelp() {
    addUserMsg("/help");
    const root = addAgentMsg();
    const a = root.querySelector(".answer");
    setStep(root, "respond", "done");
    a.classList.remove("caret");
    a.textContent =
      "可用示例意图：\n" +
      "  • 查询数据源 users 中今天的注册量\n" +
      "  • 分析最近的销售数据并生成报告\n" +
      "  • 查看系统状态\n" +
      "  • 注册一个数据查询能力\n\n" +
      "斜杠命令：" + CMDS.map((c) => c.cmd).join(" / ");
    root.querySelector(".meta-row").style.display = "none";
  }

  // ---------- Keyboard ----------
  inputEl.addEventListener("keydown", (e) => {
    if (cmdkOpen && ["ArrowDown", "ArrowUp", "Enter", "Escape"].includes(e.key)) {
      const items = cmdkList._items || [];
      if (e.key === "ArrowDown") { cmdkSel = (cmdkSel + 1) % items.length; updateCmdk(); e.preventDefault(); return; }
      if (e.key === "ArrowUp") { cmdkSel = (cmdkSel - 1 + items.length) % items.length; updateCmdk(); e.preventDefault(); return; }
      if (e.key === "Enter") { runCmd(items[cmdkSel]); e.preventDefault(); return; }
      if (e.key === "Escape") { closeCmdk(); return; }
    }
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); return; }
    if (e.key === "ArrowUp" && !inputEl.value.includes("\n")) {
      const h = userHist();
      if (h.length) { histIdx = histIdx < 0 ? h.length - 1 : Math.max(0, histIdx - 1); inputEl.value = h[histIdx]; autoGrow(); e.preventDefault(); }
      return;
    }
    if (e.key === "ArrowDown" && histIdx >= 0) {
      const h = userHist();
      histIdx = Math.min(h.length, histIdx + 1);
      inputEl.value = histIdx >= h.length ? "" : h[histIdx];
      autoGrow(); e.preventDefault();
    }
  });

  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "l") {
      e.preventDefault(); switchView("chat"); inputEl.focus();
    }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault(); switchView("chat"); inputEl.focus();
      if (!inputEl.value.startsWith("/")) { inputEl.value = "/"; autoGrow(); updateCmdk(); }
    }
  });

  // suggestion chips
  $("#suggestions").addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (chip) send(chip.dataset.text);
  });

  // ---------- Monitor ----------
  async function refreshMonitor() {
    try {
      const data = await api("GET", "/web-api/status");
      // 兼容两种响应形态：网关 {kernel_version, data} / RPC 代理 {status, result}
      const st = data.data || data.result || data;
      $("#raw-status").textContent = JSON.stringify(st, null, 2);
      const nodes = (st.cluster && st.cluster.nodes) || [];
      const procs = st.processes || [];
      const reg = st.registry || {};
      $("#m-kernel").textContent = "运行中";
      $("#m-kernel-sub").textContent = `v${data.kernel_version || "?"}`;
      $("#m-nodes").textContent = nodes.length;
      $("#m-procs").textContent = procs.length;
      $("#m-reg").textContent =
        `${(reg.capabilities || []).length} / ${(reg.templates || []).length}`;
      const nl = $("#node-list");
      nl.innerHTML = "";
      if (!nodes.length) nl.innerHTML = `<li><i class="dot busy"></i>单节点模式（无远端节点）</li>`;
      nodes.forEach((n) => {
        const li = document.createElement("li");
        li.innerHTML = `<i class="dot online"></i><span class="mono">${typeof n === "string" ? n : JSON.stringify(n)}</span>`;
        nl.appendChild(li);
      });
    } catch (e) {
      toast(`状态刷新失败：${e.message}`, "error");
    }
  }
  $("#refresh-monitor").addEventListener("click", refreshMonitor);
})();
