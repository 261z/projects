const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-button");
const messages = document.querySelector("#messages");
const template = document.querySelector("#message-template");

function safeMarkdown(text) {
  if (window.marked && window.DOMPurify) {
    return DOMPurify.sanitize(marked.parse(text));
  }
  const wrapper = document.createElement("div");
  wrapper.textContent = text;
  return wrapper.innerHTML;
}

function appendMessage(role, content, payload = {}) {
  const fragment = template.content.cloneNode(true);
  const article = fragment.querySelector(".message");
  const avatar = fragment.querySelector(".avatar");
  const bubble = fragment.querySelector(".bubble");
  const artifacts = fragment.querySelector(".artifacts");

  article.classList.add(role);
  avatar.textContent = role === "user" ? "You" : "AI";
  bubble.innerHTML = safeMarkdown(content);

  if (payload.diagram) {
    const diagramCard = document.createElement("section");
    diagramCard.className = "artifact-card";
    diagramCard.innerHTML = `<h3>Verified ER diagram</h3><div class="mermaid"></div>`;
    diagramCard.querySelector(".mermaid").textContent = payload.diagram;
    artifacts.appendChild(diagramCard);
    requestAnimationFrame(() => {
      renderDiagram(diagramCard.querySelector(".mermaid"));
    });
  }

  if (payload.sources?.length) {
    artifacts.appendChild(makeDetails(
      "Retrieved sources",
      payload.sources.map(source => {
        const score = typeof source.score === "number" ? ` (${source.score.toFixed(3)})` : "";
        return `${source.qualified_name}${score}`;
      })
    ));
  }

  if (payload.tool_trace?.length) {
    artifacts.appendChild(makeDetails(
      "Agent tool trace",
      payload.tool_trace.map(step => `${step.tool}: ${step.summary}`)
    ));
  }

  messages.appendChild(fragment);
  messages.scrollTop = messages.scrollHeight;
}

async function renderDiagram(element) {
  for (let attempt = 0; attempt < 30 && !window.schemaSenseMermaid; attempt += 1) {
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  if (!window.schemaSenseMermaid) {
    element.textContent = "Mermaid could not load. Check network access.";
    return;
  }
  try {
    await window.schemaSenseMermaid.run({ nodes: [element] });
  } catch (error) {
    element.textContent = `Diagram rendering failed: ${error.message}`;
  }
}

function makeDetails(title, items) {
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  const list = document.createElement("ul");
  summary.textContent = title;
  for (const item of items) {
    const row = document.createElement("li");
    row.textContent = item;
    list.appendChild(row);
  }
  details.append(summary, list);
  return details;
}

function setLoading(loading) {
  sendButton.disabled = loading;
  input.disabled = loading;
  sendButton.textContent = loading ? "Thinking..." : "Send";
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  appendMessage("user", message);
  input.value = "";
  setLoading(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Request failed");
    appendMessage("assistant", payload.answer, payload);
  } catch (error) {
    appendMessage("assistant", `Error: ${error.message}`);
  } finally {
    setLoading(false);
    input.focus();
  }
});

input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll(".prompt-chip").forEach(button => {
  button.addEventListener("click", () => {
    input.value = button.textContent;
    input.focus();
  });
});

clearButton.addEventListener("click", async () => {
  await fetch("/api/clear", { method: "POST" });
  messages.innerHTML = "";
  appendMessage("assistant", "Conversation cleared. What would you like to explore?");
});

