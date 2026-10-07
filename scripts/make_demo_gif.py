"""Render docs/demo.gif: an animated walkthrough of the DocTalk pipeline.

The question and answer are the real Q10 entry from eval_results.txt; the chunk
count is what src.ingest produces for the 5 PDFs in data/pdfs. Run from the repo root:
    python scripts/make_demo_gif.py
"""
import textwrap

from PIL import Image, ImageDraw, ImageFont

W, H = 960, 540
BG, PANEL, FG, DIM = (15, 23, 42), (30, 41, 59), (226, 232, 240), (148, 163, 184)
ACCENT, GREEN = (96, 165, 250), (74, 222, 128)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
f_title, f_body, f_small, f_mono = (ImageFont.truetype(BOLD, 28), ImageFont.truetype(FONT, 20),
                                    ImageFont.truetype(FONT, 15), ImageFont.truetype(MONO, 17))

QUESTION = "What does RVI stand for in the context of average-reward Q-learning?"
ANSWER = ('In the context of average-reward Q-learning, RVI stands for "Relative Value Iteration." '
          "This term is used to refer to a family of Q-learning algorithms that are based on the "
          "RVI approach, which operates without knowledge of the Markov Decision Process (MDP) "
          "model parameters.  (Source: rp4.pdf, Page: 1)")
STEPS = ["1 Ingest", "2 Retrieve", "3 Rerank", "4 Answer"]


def base(step, caption):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((40, 28), "DocTalk", font=f_title, fill=FG)
    d.text((176, 38), "ask your PDFs, get cited answers", font=f_body, fill=DIM)
    x = 40
    for i, name in enumerate(STEPS):
        on = i <= step
        d.rounded_rectangle((x, 90, x + 205, 126), 8, fill=ACCENT if i == step else PANEL)
        d.text((x + 14, 98), name, font=f_body, fill=BG if i == step else (FG if on else DIM))
        x += 220
    d.rounded_rectangle((40, 150, W - 40, 470), 12, fill=PANEL)
    d.text((40, 495), caption, font=f_small, fill=DIM)
    return img, d


def question_bar(d, text):
    d.text((64, 170), "Q", font=f_body, fill=ACCENT)
    d.text((96, 170), text, font=f_body, fill=FG)


frames, durations = [], []


def add(img, ms):
    frames.append(img)
    durations.append(ms)


CAP = "Pipeline walkthrough. Question and answer text are from eval_results.txt (Q10)."

# 1 ingest: five PDFs flow into chunks
for n in range(6):
    img, d = base(0, CAP)
    d.text((64, 175), "PyMuPDF  ->  100-word chunks  ->  MiniLM embeddings  ->  ChromaDB", font=f_body, fill=FG)
    for i in range(5):
        y = 235 + i * 40
        d.rounded_rectangle((64, y, 220, y + 30), 6, fill=BG)
        d.text((78, y + 5), f"rp{i+1}.pdf", font=f_mono, fill=FG if i < n else DIM)
    counts = [67, 58, 56, 317, 168]
    for i in range(min(n, 5)):
        d.text((250, 240 + i * 40), f"{counts[i]} chunks", font=f_mono, fill=GREEN)
    if n == 5:
        d.text((520, 300), "666 chunks stored", font=f_title, fill=GREEN)
        d.text((520, 345), "384-dim vectors, persistent", font=f_body, fill=DIM)
    add(img, 450)
add(img, 900)

# 2 retrieve: question typed
for i in range(0, len(QUESTION) + 1, 3):
    img, d = base(1, CAP)
    question_bar(d, QUESTION[:i] + ("|" if i < len(QUESTION) else ""))
    add(img, 60)
img, d = base(1, CAP)
question_bar(d, QUESTION)
d.text((64, 230), "Embed the question, fetch the 10 closest chunks from ChromaDB", font=f_body, fill=FG)
for i in range(10):
    d.rounded_rectangle((64 + i * 86, 290, 64 + i * 86 + 74, 340), 6, fill=BG, outline=ACCENT)
    d.text((64 + i * 86 + 12, 306), f"#{i+1}", font=f_mono, fill=ACCENT)
add(img, 1600)

# 3 rerank: keep top 3
img, d = base(2, CAP)
question_bar(d, QUESTION)
d.text((64, 230), "gpt-4o-mini scores each chunk 1-10: does it ANSWER the question?", font=f_body, fill=FG)
d.text((64, 262), "Reference lists mention the keywords but score low and drop out.", font=f_small, fill=DIM)
for i in range(10):
    kept = i < 3
    d.rounded_rectangle((64 + i * 86, 310, 64 + i * 86 + 74, 360), 6, fill=BG,
                        outline=GREEN if kept else DIM, width=3 if kept else 1)
    d.text((64 + i * 86 + 12, 326), f"#{i+1}", font=f_mono, fill=GREEN if kept else DIM)
d.text((64, 385), "Keep the top 3 as context", font=f_body, fill=GREEN)
add(img, 2200)

# 4 answer typed
lines_src = textwrap.wrap(ANSWER, 78)
full = "\n".join(lines_src)
for i in range(0, len(full) + 1, 5):
    img, d = base(3, CAP)
    question_bar(d, QUESTION)
    for j, line in enumerate(full[:i].split("\n")):
        d.text((96, 225 + j * 30), line, font=f_body, fill=FG)
    add(img, 45)
img, d = base(3, CAP)
question_bar(d, QUESTION)
for j, line in enumerate(lines_src):
    d.text((96, 225 + j * 30), line, font=f_body, fill=FG)
d.text((96, 420), "Cited: rp4.pdf, page 1", font=f_body, fill=GREEN)
add(img, 3500)

frames[0].save("docs/demo.gif", save_all=True, append_images=frames[1:], duration=durations,
               loop=0, optimize=True)
print(f"wrote docs/demo.gif ({len(frames)} frames)")
