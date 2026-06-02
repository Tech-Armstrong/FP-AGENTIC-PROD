# Deploy — Single Container (all 4 services in one box)

This app is **4 little programs** (a Next.js website + 3 Python services). These files pack all four
into **one Docker container** so you build/push/run a single image.

| Service | Port (inside container) | Started by |
|---|---|---|
| Next.js frontend | **3000** (the only public one) | `npm start` |
| Chat agent | 8000 | `agent/main.py` |
| Airtable + planning API | 8001 | `backend/airtable_main.py` |
| OCR policy service | 8010 | `ocr-service/main.py` |

Inside the box the website talks to the other three over `localhost`, so **only port 3000 is exposed**.
A process manager called **supervisord** keeps all four running.

## Files added
- `Dockerfile` — builds the website (Node 20) and packs it with the Python services (Python 3.11).
- `deploy/supervisord.conf` — tells supervisord how to start all four services.
- `.dockerignore` — keeps secrets and junk out of the image.

---

## 1. Build it (on your laptop, needs Docker Desktop)

```bash
# from the chatwithyourdata/ folder
docker build -t chatwithyourdata:latest .
```

## 2. Run it locally to test

Create a `.env` from `.env.example` and fill in your keys (Azure OpenAI, Airtable, Tavily). Then:

```bash
docker run --env-file .env -p 3000:3000 chatwithyourdata:latest
```

Open http://localhost:3000. `docker logs <container-id>` shows all four services in one stream.

> If you'd rather not install Docker, skip to step 3 — Azure can build the image *for you* from these files.

---

## 3. Put it on Azure (Container Apps) — [Portal-friendly]

You already have an Azure subscription. One-time setup (Portal: "Create a resource"):
1. **Resource Group** — e.g. `rg-chatwithyourdata-demo` (a folder for everything; delete it to clean up).
2. **Azure Container Registry (ACR)** — e.g. `acrchatdata` (the shelf your image lives on).
3. **Container Apps Environment** — e.g. `cae-chatdata` (where the container runs).

Build & push the image to ACR (Azure builds it — no Docker needed locally). This is the only
command-line step; run it in the Azure Portal's **Cloud Shell** (the `>_` icon top-right):

```bash
az acr build --registry acrchatdata --image chatwithyourdata:v1 .
```

Then **[Portal]** create one **Container App** from that image:
- Image: `acrchatdata.azurecr.io/chatwithyourdata:v1`
- **Ingress: External**, target port **3000**.
- **Scaling:** min replicas `0` (scale-to-zero = near-zero cost when idle), max `3`.
- **Secrets / Env vars:** add the keys from `.env.example` (Azure OpenAI `AZURE_OPENAI_*` **and**
  `AZURE_API_*`, `AIRTABLE_*`, `TAVILY_API_KEY`). The `*_URL`/`*_PORT` wiring already defaults to
  localhost inside the image, so you only need to supply the **secrets**.

## 4. Light security gate (no login in the app yet)
**[Portal]** On the Container App, turn on **Authentication ("Easy Auth")** with **Microsoft Entra ID**
so only company logins can open it. No code change needed.

## 5. Test
Open the Container App's public URL → sign in → pick a client → **Make plan** → try the chat sidebar.
If something fails, open the Container App's **Log stream** — the usual cause is a missing/mistyped
env var (note the two Azure naming sets: `AZURE_OPENAI_*` for the chat agent, `AZURE_API_*` for the
planning nodes and direct-Next chat).

---

## Notes & trade-offs of the single-container approach
- **Simpler & cheaper to run** (one image, one app) — great for an internal demo.
- **Trade-off:** all four scale together and share one box; you can't scale just the chat agent. Fine
  at small scale; if usage grows a lot, splitting into separate Container Apps is the next step
  (see `C:\Users\Armstrong Admin\.claude\plans\i-want-you-to-partitioned-crescent.md`).
- **OCR optional:** if policy-document upload isn't part of the demo, you can remove the `[program:ocr]`
  block from `deploy/supervisord.conf` and the `ocr-service` COPY/requirements lines from the Dockerfile.
