# Deploying DocTalk to HuggingFace Spaces

The Space runs everything in one container. FastAPI runs internally on port 8000 and Streamlit is the public app on port 7860. `Dockerfile.spaces` and `start.sh` handle this.

## Steps, about 10 minutes

1. Make the Space: huggingface.co, New Space, name it `doctalk`, pick **Docker** as the SDK, blank template, public.

2. Add your OpenAI key as a secret so it never touches the repo:
   Space page, Settings, Variables and secrets, New secret. Name it `OPENAI_API_KEY`, paste your `sk-...` key.

3. Clone the Space repo and copy the project into it:
   ```bash
   git clone https://huggingface.co/spaces/<your-username>/doctalk hf-doctalk
   cd hf-doctalk
   # copy these over from the project:
   #   src/  api.py  ui.py  requirements.txt  start.sh
   #   data/pdfs/  chroma_db/  Dockerfile.spaces
   mv Dockerfile.spaces Dockerfile
   ```
   Yes, `chroma_db/` gets committed here even though it's gitignored on GitHub. Space storage is wiped on every restart, so the index has to ship inside the image or the app boots with nothing.

4. The Space needs a README.md that starts with this exact block (this is how Spaces knows what to run):
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

5. Push it:
   ```bash
   git add -A
   git commit -m "deploy DocTalk"
   git push
   ```
   The build takes around 5 minutes, then the app is live at
   `https://huggingface.co/spaces/<your-username>/doctalk`

## After it's live

- Upload a PDF and ask something, make sure answers cite the right file and page
- If it won't start, check the Logs tab. Nine times out of ten it's the missing `OPENAI_API_KEY` secret
- Anything uploaded to the live Space disappears on restart. That's expected, storage is ephemeral

## A note on auth

Pushing to HuggingFace over HTTPS asks for your HF username and a token (huggingface.co, Settings, Access Tokens, make one with write permission). Use the token as the password.
