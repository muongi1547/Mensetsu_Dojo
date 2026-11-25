# Mensetsu Dojo

A two-month speaking plan and practice room for Japanese job interviews, aimed at international students applying for new-graduate AI engineer roles (automotive), with company prep for FPT.

- **Plan**: 8 weeks of daily tasks (about 60 minutes on weekdays), with recorded benchmarks in weeks 1, 4 and 8.
- **Questions**: 46 interview questions, each with a model answer and a step-by-step "What to say" guide.
- **Mock interview**: HR, technical, final and follow-up (深掘り) rounds.
- **Words & phrases**: interview keigo, survival phrases, common mistakes and technical vocabulary.
- **FPT prep**: company facts with sources and dates, plus questions to ask the interviewer.

It is a static site: `index.html` plus the JSON files in `data/`. There is no build step and no server code.

## Run it on your own computer

The page loads its content from `data/`, so serve the folder with a local web server. Opening `index.html` by double-clicking does not work, because browsers block those file loads.

```bash
git clone https://github.com/muongi1547/Mensetsu_Dojo.git
cd mensetsu-dojo
python3 -m http.server 8000
```

Then open http://localhost:8000 in Chrome or Edge. Press Ctrl+C in the terminal to stop the server.

## Put it online with GitHub Pages

1. In the repository on GitHub, open **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**, choose `main` and `/ (root)`, and select **Save**.
3. After a minute or two the site is live at `https://YOUR-USERNAME.github.io/mensetsu-dojo/`.

On a free GitHub account, Pages needs a public repository. GitHub Pro, which students get free through GitHub Education, also allows private ones. The published site is public either way. The empty `.nojekyll` file makes Pages serve the files exactly as they are.

Other static hosts (Netlify, Cloudflare Pages, Vercel) work the same way: upload the folder as it is.

## What works outside claude.ai

The page was first built as a Claude artifact. A few features use Claude, so they only work there.

| Feature | Your own copy | On claude.ai |
|---|---|---|
| Plan, questions, model answers, "What to say" guides, words, FPT prep | Yes | Yes |
| Read aloud | Browser voice (Kyoko on macOS, Google 日本語 in Chrome) | Claude voice or browser voice |
| Speaking practice | Timer with the target length | Dictation with transcript, 字/分 and filler count |
| AI feedback, AI mock interviewer, "How should I answer?" hints | No. The Mock tab gives prompts to paste into any AI chat | Yes |
| Progress | Saved in this browser only | Synced to your Claude account |
| Download the plan or your answers (.md) | Yes | Yes |

Progress does not move between claude.ai and your own copy, or between browsers. Use **Tools → Download my answers (.md)** to keep a copy.

## Changing the content

All the text is in `data/`:

| File | Contents |
|---|---|
| `questions.json` | Questions, what the interviewer checks, model answers, follow-ups (one question per line) |
| `guides.json` | The "What to say" steps for each question |
| `plan.json` | The 8-week plan, routines, rubric, AI prompts and resources |
| `language.json` | Phrases, keigo, common mistakes, work vocabulary, interview flow and manners |
| `vocab.json` | Technical vocabulary |
| `fpt.json` | Company facts with sources, and questions to ask |

Edit a file and reload the page. In `guides.json`, keep each step's `exampleJa` an exact piece of the question's `modelAnswerJa`: joined in order, the steps should reproduce the model answer.

## Notes

- This is unofficial study material. It is not affiliated with or endorsed by FPT. The company facts were collected in November 2026 and each one lists its source; check them again before an interview.
- The model answers describe an example candidate. Replace the 【 】 parts with your own facts, and have a teacher or your university's career centre check your final answers.
- Your answers and progress are stored only in your browser (localStorage). The page loads its fonts from Google Fonts.
