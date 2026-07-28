# Deploying DocTalk to HuggingFace Spaces

The Space runs both services in one container: FastAPI internally on :8000,
Streamlit public on :7860 (`Dockerfile.spaces` + `start.sh`).

## Steps (~10 minutes)

1. Create the Space: huggingface.co → New Space → name `doctalk` →
   SDK: **Docker** → Blank template → Public.

2. Add your API key as a secret (never commit it):
   Space → Settings → Variables and secrets → New secret →
   name `OPENAI_API_KEY`, value `sk-...`

3. Clone the Space repo and copy the project in:
   ```bash
   git clone https://huggingface.co/spaces/<your-username>/doctalk hf-doctalk
   cd hf-doctalk
   # copy from your project: src/ api.py ui.py requirements.txt start.sh
   #                         data/pdfs/ chroma_db/ Dockerfile.spaces
   mv Dockerfile.spaces Dockerfile
   ```
   Note: `chroma_db/` must be committed to the Space so the index ships with
   the app (Space storage is ephemeral — anything uploaded at runtime is lost
   on restart, but the baked-in index always works).

4. Space README front-matter — create `README.md` in the Space repo starting
   with exactly:
   ```yaml
   ---
   title: DocTalk
   emoji: 📄
   colorFrom: blue
   colorTo: indigo
   sdk: docker
   app_port: 7860
   pinned: false
   ---
   ```

5. Push:
   ```bash
   git add -A
   git commit -m "deploy DocTalk"
   git push
   ```
   The Space builds (~5 min) and goes live at
   `https://huggingface.co/spaces/<your-username>/doctalk`

## Sanity checks after deploy

- Ask "What does RVI stand for in average-reward Q-learning?" → should cite rp4.pdf
- Toggle reranking off and compare sources
- Check logs (Space → Logs) if the app doesn't start — most common issue is a
  missing `OPENAI_API_KEY` secret
