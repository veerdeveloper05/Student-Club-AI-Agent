/**
 * Student Club Information AI Agent - Frontend Controller
 * Premium redesign with Tailwind CSS + Lucide Icons
 */

document.addEventListener("DOMContentLoaded", () => {
  // ---------------------------------------------------------------
  // Elements
  // ---------------------------------------------------------------
  const chatMessages     = document.getElementById("chatMessages");
  const chatForm         = document.getElementById("chatForm");
  const userInput        = document.getElementById("userMessageInput");
  const sendBtn          = document.getElementById("sendBtn");
  const clearChatBtn     = document.getElementById("clearChatBtn");
  const btnQuickClear    = document.getElementById("btnQuickClear");
  const sampleChips      = document.getElementById("sampleChips");
  const clubSearchInput  = document.getElementById("clubSearchInput");
  const clearSearchBtn   = document.getElementById("clearSearchBtn");
  const resetFilterBtn   = document.getElementById("resetFilterBtn");
  const noClubsFound     = document.getElementById("noClubsFound");
  const clubsList        = document.getElementById("clubsList");
  const catChips         = document.getElementById("categoryFilterChips");
  const clubCounterBadge = document.getElementById("clubCounterBadge");
  const toggleDirBtn     = document.getElementById("toggleDirectoryBtn");
  const clubsSidebar     = document.getElementById("clubsSidebar");
  const chatViewport     = document.getElementById("chatViewport");
  const tabShowClubs     = document.getElementById("tabShowClubs");
  const tabShowChat      = document.getElementById("tabShowChat");
  const modal            = document.getElementById("clubDetailModal");
  const closeModalBtn    = document.getElementById("closeModalBtn");
  const modalClosebtn    = document.getElementById("modalCloseActionBtn");
  const modalAskBtn      = document.getElementById("modalAskAIActionBtn");
  const heroExploreBtn   = document.getElementById("heroExploreBtn");
  const heroAskAIBtn     = document.getElementById("heroAskAIBtn");

  let currentCategory = "all";
  let currentSearch   = "";
  let clubsCache      = {};
  let activeClub      = null;

  // Init
  setInitialTime();
  fetchAllClubs();
  setupListeners();
  applyClubColors();
  reinitLucide();

  // ---------------------------------------------------------------
  // Apply dynamic club colors from data-color attribute
  // (avoids Jinja2 inside CSS style attributes which confuse linters)
  // ---------------------------------------------------------------
  function applyClubColors() {
    document.querySelectorAll(".club-item-card").forEach((card) => {
      const color = card.dataset.color;
      if (!color) return;

      // Accent bar — solid club color
      const bar = card.querySelector(".club-accent-bar");
      if (bar) bar.style.background = color;

      // Icon bubble — light tinted background + border
      const icon = card.querySelector(".club-icon-bubble");
      if (icon) {
        icon.style.background = color + "18";
        icon.style.border = "1.5px solid " + color + "35";
      }

      // Alias / short name badge
      const badge = card.querySelector(".club-alias-badge");
      if (badge) {
        badge.style.background = color + "15";
        badge.style.color = color;
        badge.style.border = "1px solid " + color + "30";
      }

      // Fee pill
      const fee = card.querySelector(".club-fee-pill");
      if (fee) {
        fee.style.background = color + "12";
        fee.style.color = color;
        fee.style.border = "1px solid " + color + "28";
      }
    });
  }

  // ---------------------------------------------------------------
  // Lucide re-init helper (call after DOM mutations)
  // ---------------------------------------------------------------
  function reinitLucide() {
    if (typeof lucide !== "undefined") {
      try { lucide.createIcons(); } catch(e) {}
    }
  }

  // ---------------------------------------------------------------
  // Timestamp
  // ---------------------------------------------------------------
  function setInitialTime() {
    const el = document.getElementById("initialTime");
    if (el) el.textContent = getTime();
  }

  function getTime() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  // ---------------------------------------------------------------
  // Listeners
  // ---------------------------------------------------------------
  function setupListeners() {
    // Chat form submit
    if (chatForm) chatForm.addEventListener("submit", (e) => { e.preventDefault(); handleSend(); });

    // Enter key
    if (userInput) {
      userInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
      });
      userInput.addEventListener("input", () => {
        // Auto-grow
        userInput.style.height = "auto";
        userInput.style.height = Math.min(userInput.scrollHeight, 128) + "px";
        // Clear button visibility
        if (btnQuickClear) {
          const hasText = userInput.value.trim().length > 0;
          btnQuickClear.style.opacity = hasText ? "1" : "0";
          btnQuickClear.style.pointerEvents = hasText ? "auto" : "none";
        }
      });
    }

    // Clear input
    if (btnQuickClear) {
      btnQuickClear.addEventListener("click", () => {
        userInput.value = "";
        userInput.style.height = "auto";
        btnQuickClear.style.opacity = "0";
        btnQuickClear.style.pointerEvents = "none";
        userInput.focus();
      });
    }

    // Clear chat
    if (clearChatBtn) clearChatBtn.addEventListener("click", clearChat);

    // Suggested chips
    if (sampleChips) {
      sampleChips.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip-btn");
        if (chip && chip.dataset.query) {
          sendDirectQuery(chip.dataset.query);
          switchMobileView("chat");
        }
      });
    }

    // Hero prompt chips
    document.querySelectorAll(".hero-prompt-chip").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (btn.dataset.query) {
          sendDirectQuery(btn.dataset.query);
          switchMobileView("chat");
          document.getElementById("chatViewport")?.scrollIntoView({ behavior: "smooth" });
        }
      });
    });

    // Hero CTA buttons
    if (heroExploreBtn) {
      heroExploreBtn.addEventListener("click", () => {
        if (window.innerWidth <= 1023) switchMobileView("clubs");
        clubsSidebar?.scrollIntoView({ behavior: "smooth" });
      });
    }
    if (heroAskAIBtn) {
      heroAskAIBtn.addEventListener("click", () => {
        switchMobileView("chat");
        chatViewport?.scrollIntoView({ behavior: "smooth" });
        setTimeout(() => userInput?.focus(), 300);
      });
    }

    // Welcome cards
    if (chatMessages) {
      chatMessages.addEventListener("click", (e) => {
        const card = e.target.closest(".welcome-club-chip");
        if (card && card.dataset.query) sendDirectQuery(card.dataset.query);
      });
    }

    // Search input
    if (clubSearchInput) {
      clubSearchInput.addEventListener("input", (e) => {
        currentSearch = e.target.value.toLowerCase().trim();
        if (clearSearchBtn) clearSearchBtn.style.display = currentSearch ? "flex" : "none";
        applyFilters();
      });
    }

    // Clear search
    if (clearSearchBtn) {
      clearSearchBtn.addEventListener("click", () => {
        clubSearchInput.value = "";
        currentSearch = "";
        clearSearchBtn.style.display = "none";
        applyFilters();
        clubSearchInput.focus();
      });
    }

    // Reset filter
    if (resetFilterBtn) {
      resetFilterBtn.addEventListener("click", () => {
        clubSearchInput.value = "";
        currentSearch = "";
        currentCategory = "all";
        if (clearSearchBtn) clearSearchBtn.style.display = "none";
        updateCatPills("all");
        applyFilters();
      });
    }

    // Category pills
    if (catChips) {
      catChips.addEventListener("click", (e) => {
        const pill = e.target.closest(".cat-pill");
        if (pill && pill.dataset.category) {
          currentCategory = pill.dataset.category;
          updateCatPills(currentCategory);
          applyFilters();
        }
      });
    }

    // Club list: Ask AI + View Details
    if (clubsList) {
      clubsList.addEventListener("click", (e) => {
        const askBtn = e.target.closest(".ask-club-btn");
        if (askBtn && askBtn.dataset.query) {
          sendDirectQuery(askBtn.dataset.query);
          switchMobileView("chat");
          return;
        }
        const detBtn = e.target.closest(".view-details-btn");
        if (detBtn && detBtn.dataset.clubId) openModal(detBtn.dataset.clubId);
      });
    }

    // Mobile tabs
    if (tabShowClubs) tabShowClubs.addEventListener("click", () => switchMobileView("clubs"));
    if (tabShowChat)  tabShowChat.addEventListener("click",  () => switchMobileView("chat"));

    // Toggle dir button
    if (toggleDirBtn) {
      toggleDirBtn.addEventListener("click", () => {
        if (window.innerWidth <= 1023) switchMobileView(clubsSidebar?.classList.contains("mobile-hidden") ? "clubs" : "chat");
        else clubsSidebar?.scrollIntoView({ behavior: "smooth" });
      });
    }

    // Modal close
    if (closeModalBtn) closeModalBtn.addEventListener("click", closeModal);
    if (modalClosebtn) modalClosebtn.addEventListener("click", closeModal);
    if (modal) modal.addEventListener("click", (e) => { if (e.target === modal) closeModal(); });
    if (modalAskBtn) {
      modalAskBtn.addEventListener("click", () => {
        if (activeClub) {
          closeModal();
          sendDirectQuery(`Tell me all about ${activeClub.name}`);
          switchMobileView("chat");
        }
      });
    }
  }

  // ---------------------------------------------------------------
  // Category pill state management
  // ---------------------------------------------------------------
  function updateCatPills(activeCategory) {
    if (!catChips) return;
    catChips.querySelectorAll(".cat-pill").forEach((pill) => {
      if (pill.dataset.category === activeCategory) {
        pill.style.background = "#FF7A1A";
        pill.style.color = "#fff";
        pill.style.borderColor = "#FF7A1A";
      } else {
        pill.style.background = "#f8fafc";
        pill.style.color = "#475569";
        pill.style.borderColor = "#e2e8f0";
      }
    });
  }

  // ---------------------------------------------------------------
  // Search & Filter
  // ---------------------------------------------------------------
  function applyFilters() {
    if (!clubsList) return;
    const cards = clubsList.querySelectorAll(".club-item-card");
    let visible = 0;

    cards.forEach((card) => {
      const name    = card.querySelector(".club-name-text")?.textContent.toLowerCase() || "";
      const tagline = card.querySelector(".club-tagline-text")?.textContent.toLowerCase() || "";
      const cat     = card.dataset.category || "";
      const id      = card.dataset.clubId || "";

      const catOk   = currentCategory === "all" || cat.toLowerCase() === currentCategory.toLowerCase();
      const searchOk = !currentSearch || name.includes(currentSearch) || tagline.includes(currentSearch)
                     || cat.toLowerCase().includes(currentSearch) || id.includes(currentSearch);

      if (catOk && searchOk) {
        card.style.display = "";
        visible++;
      } else {
        card.style.display = "none";
      }
    });

    if (clubCounterBadge) clubCounterBadge.textContent = `${visible} Active`;
    if (noClubsFound) {
      noClubsFound.style.display = visible === 0 ? "flex" : "none";
    }
  }

  // ---------------------------------------------------------------
  // Mobile view switching
  // ---------------------------------------------------------------
  function switchMobileView(view) {
    if (window.innerWidth > 1023) return;

    if (view === "clubs") {
      tabShowClubs?.classList.add("active");
      tabShowChat?.classList.remove("active");
      clubsSidebar?.classList.remove("mobile-hidden");
      chatViewport?.classList.add("mobile-hidden");

      // Update tab styles
      if (tabShowClubs) { tabShowClubs.style.color="#FF7A1A"; tabShowClubs.style.borderColor="#FF7A1A"; }
      if (tabShowChat)  { tabShowChat.style.color="#94a3b8"; tabShowChat.style.borderColor="transparent"; }
    } else {
      tabShowChat?.classList.add("active");
      tabShowClubs?.classList.remove("active");
      chatViewport?.classList.remove("mobile-hidden");
      clubsSidebar?.classList.add("mobile-hidden");

      if (tabShowChat)  { tabShowChat.style.color="#FF7A1A"; tabShowChat.style.borderColor="#FF7A1A"; }
      if (tabShowClubs) { tabShowClubs.style.color="#94a3b8"; tabShowClubs.style.borderColor="transparent"; }
      userInput?.focus();
    }
  }

  // ---------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------
  async function fetchAllClubs() {
    try {
      const res = await fetch("/api/clubs");
      if (res.ok) {
        const data = await res.json();
        if (data.clubs) data.clubs.forEach((c) => { clubsCache[c.id] = c; });
      }
    } catch (e) { console.warn("Pre-fetch clubs failed:", e); }
  }

  // ---------------------------------------------------------------
  // Chat
  // ---------------------------------------------------------------
  async function handleSend() {
    const text = userInput.value.trim();
    if (!text) return;
    userInput.value = "";
    userInput.style.height = "auto";
    if (btnQuickClear) { btnQuickClear.style.opacity = "0"; btnQuickClear.style.pointerEvents = "none"; }
    userInput.focus();
    await sendDirectQuery(text);
  }

  async function sendDirectQuery(text) {
    appendUserMsg(text);
    const typing = appendTyping();
    scrollBottom();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });

      typing?.remove();

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `HTTP ${res.status}`);
      }

      const data = await res.json();
      appendAgentMsg(data.reply, data.suggestions, data.club_id);
      if (data.club_id) highlightCard(data.club_id);

    } catch (err) {
      typing?.remove();
      appendAgentMsg(
        `&#x26A0;&#xFE0F; **Connection Error**: Unable to reach the assistant (${err.message}). Ensure the Flask server is running on \`http://127.0.0.1:5000\`.`,
        ["What clubs are available?", "How to join Coding Club?"]
      );
    }
    scrollBottom();
  }

  // ---------------------------------------------------------------
  // Message rendering
  // ---------------------------------------------------------------
  function appendUserMsg(text) {
    const row = document.createElement("div");
    row.className = "message-row user-row flex items-start gap-3";
    row.style.flexDirection = "row-reverse";
    row.innerHTML = `
      <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5" style="background:linear-gradient(135deg,#FF7A1A,#E86500);">
        <i data-lucide="user-round" class="w-4 h-4 text-white"></i>
      </div>
      <div style="max-width:80%;">
        <div class="message-header" style="flex-direction:row-reverse;">
          <span class="text-xs font-bold text-slate-700">You</span>
          <span class="text-[10px] text-slate-400">${getTime()}</span>
        </div>
        <div class="message-bubble px-4 py-3 text-sm" style="background:#0B1220; color:#f1f5f9; border-radius:18px 18px 4px 18px; border:1px solid rgba(255,255,255,0.08);">
          <div class="message-text"><p>${escHtml(text)}</p></div>
        </div>
      </div>
    `;
    chatMessages.appendChild(row);
    reinitLucide();
  }

  function appendAgentMsg(md, suggestions = [], clubId = null) {
    const row = document.createElement("div");
    row.className = "message-row agent-row flex items-start gap-3";

    let sugHtml = "";
    if (suggestions && suggestions.length > 0) {
      sugHtml = `<div class="follow-up-group">
        ${suggestions.map(s => `<button class="follow-up-btn" data-query="${escHtml(s)}">${escHtml(s)}</button>`).join("")}
      </div>`;
    }

    row.innerHTML = `
      <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5" style="background:linear-gradient(135deg,#0B1220,#162440); border:1px solid #e2e8f0;">
        <i data-lucide="bot" class="w-4 h-4" style="color:#FF7A1A;"></i>
      </div>
      <div style="max-width:88%;">
        <div class="message-header">
          <span class="text-xs font-bold text-slate-700">CampusClub AI</span>
          <span class="text-[10px] text-slate-400">${getTime()}</span>
        </div>
        <div class="message-bubble bg-slate-50 border border-slate-200 px-4 py-3.5 text-sm text-slate-700" style="border-radius:4px 18px 18px 18px;">
          <div class="message-text">${fmtMarkdown(md)}</div>
          ${sugHtml}
        </div>
      </div>
    `;

    row.querySelectorAll(".follow-up-btn").forEach((btn) => {
      btn.addEventListener("click", () => sendDirectQuery(btn.dataset.query));
    });

    chatMessages.appendChild(row);
    reinitLucide();
  }

  function appendTyping() {
    const row = document.createElement("div");
    row.className = "message-row agent-row typing-row flex items-start gap-3";
    row.innerHTML = `
      <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5" style="background:linear-gradient(135deg,#0B1220,#162440); border:1px solid #e2e8f0;">
        <i data-lucide="bot" class="w-4 h-4" style="color:#FF7A1A;"></i>
      </div>
      <div class="message-bubble bg-slate-50 border border-slate-200 px-4 py-3.5" style="border-radius:4px 18px 18px 18px;">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    chatMessages.appendChild(row);
    reinitLucide();
    return row;
  }

  function scrollBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function clearChat() {
    chatMessages.innerHTML = `
      <div class="message-row agent-row flex items-start gap-3" style="animation: sc-fadeUp 0.4s ease both;">
        <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 mt-0.5" style="background:linear-gradient(135deg,#0B1220,#162440); border:1px solid #e2e8f0;">
          <i data-lucide="bot" class="w-4 h-4" style="color:#FF7A1A;"></i>
        </div>
        <div style="max-width:88%;">
          <div class="message-header">
            <span class="text-xs font-bold text-slate-700">CampusClub AI</span>
            <span class="text-[10px] text-slate-400">${getTime()}</span>
          </div>
          <div class="message-bubble bg-slate-50 border border-slate-200 px-4 py-3.5 text-sm text-slate-700" style="border-radius:4px 18px 18px 18px;">
            <div class="message-text">
              <p>&#x1F9F9; <strong>Chat session reset.</strong></p>
              <p>How can I help you? Ask about meeting schedules, activities, fees, or how to join any of our 5 official clubs!</p>
            </div>
          </div>
        </div>
      </div>
    `;
    userInput.value = "";
    userInput.focus();
    scrollBottom();
    reinitLucide();
  }

  // ---------------------------------------------------------------
  // Highlight club card
  // ---------------------------------------------------------------
  function highlightCard(clubId) {
    const card = clubsList?.querySelector(`[data-club-id="${clubId}"]`);
    if (!card) return;
    card.scrollIntoView({ behavior: "smooth", block: "nearest" });
    const prev = card.style.outline;
    card.style.outline = "2.5px solid #FF7A1A";
    card.style.outlineOffset = "2px";
    setTimeout(() => { card.style.outline = prev || ""; card.style.outlineOffset = ""; }, 2600);
  }

  // ---------------------------------------------------------------
  // Markdown formatter
  // ---------------------------------------------------------------
  function fmtMarkdown(text) {
    if (!text) return "";
    let lines = text.split("\n");
    let html = [];
    let inList = false;

    lines.forEach((raw) => {
      let line = raw.trim();
      line = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
      line = line.replace(/\*(.*?)\*/g, "<em>$1</em>");
      line = line.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
      line = line.replace(/`(.*?)`/g, "<code>$1</code>");

      if (line.startsWith("• ") || line.startsWith("- ")) {
        if (!inList) { html.push("<ul>"); inList = true; }
        html.push(`<li>${line.substring(2)}</li>`);
      } else {
        if (inList) { html.push("</ul>"); inList = false; }
        if (line === "") html.push("<br/>");
        else html.push(`<p>${line}</p>`);
      }
    });
    if (inList) html.push("</ul>");
    return html.join("");
  }

  function escHtml(str) {
    if (!str) return "";
    return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
  }

  // ---------------------------------------------------------------
  // Modal
  // ---------------------------------------------------------------
  async function openModal(clubId) {
    let club = clubsCache[clubId];
    if (!club) {
      try {
        const res = await fetch(`/api/clubs/${clubId}`);
        const data = await res.json();
        if (data.success) { club = data.club; clubsCache[clubId] = club; }
      } catch (e) { console.error("Modal load failed:", e); return; }
    }
    if (!club) return;
    activeClub = club;

    document.getElementById("modalClubEmoji").textContent = club.icon || "&#x1F3DB;&#xFE0F;";
    document.getElementById("modalClubName").textContent = club.name;
    document.getElementById("modalClubCategory").textContent = club.category;
    document.getElementById("modalClubTagline").textContent = `"${club.tagline}"`;
    document.getElementById("modalClubDesc").textContent = club.description;
    document.getElementById("modalClubSchedule").textContent = `${club.meeting_schedule.day}, ${club.meeting_schedule.time}`;
    document.getElementById("modalClubVenue").textContent = club.meeting_schedule.venue;
    document.getElementById("modalClubFee").textContent = club.membership.fee;
    document.getElementById("modalClubLead").textContent = club.lead.president;

    // Activities
    const actUl = document.getElementById("modalClubActivities");
    actUl.innerHTML = "";
    (club.activities || []).forEach((a) => {
      const li = document.createElement("li"); li.textContent = a; actUl.appendChild(li);
    });

    // Events
    const evCon = document.getElementById("modalClubEvents");
    evCon.innerHTML = "";
    (club.events || []).forEach((ev) => {
      const d = document.createElement("div");
      d.className = "modal-event-card";
      d.innerHTML = `
        <h5>${escHtml(ev.title)}</h5>
        <div class="modal-event-meta">
          <span>🗓️ ${escHtml(ev.date)}</span>
          <span>📍 ${escHtml(ev.venue)}</span>
        </div>
        <p class="modal-event-desc">${escHtml(ev.description)}</p>
      `;
      evCon.appendChild(d);
    });

    // Registration
    document.getElementById("modalClubRegistration").innerHTML = `
      <strong>Process:</strong> ${escHtml(club.registration.process)}<br>
      <strong>Deadline:</strong> ${escHtml(club.registration.deadline)}<br>
      <strong>Orientation:</strong> ${escHtml(club.registration.orientation)}<br>
      <strong>Portal:</strong> <a href="${escHtml(club.registration.link)}" target="_blank" rel="noopener" style="color:#c2410c; text-decoration:underline;">${escHtml(club.registration.link)}</a>
    `;

    modal.classList.add("open");
    document.body.style.overflow = "hidden";
    reinitLucide();
  }

  function closeModal() {
    modal.classList.remove("open");
    document.body.style.overflow = "";
    activeClub = null;
  }
});
