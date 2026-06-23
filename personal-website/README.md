# chandan-123kumar.github.io

Personal website for Chandan Kumar — Senior AI Engineer.

Plain HTML + CSS + vanilla JS. No build step.

## Local preview

```
cd personal-website
python3 -m http.server 8000
```

Open http://localhost:8000.

## Deploy

1. Create a new GitHub repository named `chandan-123kumar.github.io` (user site — name must match your GitHub username).
2. From this directory:
   ```
   git init
   git add .
   git commit -m "Initial site"
   git branch -M main
   git remote add origin git@github.com:chandan-123kumar/chandan-123kumar.github.io.git
   git push -u origin main
   ```
3. GitHub Pages auto-publishes from `main`. Visit https://chandan-123kumar.github.io within ~1 minute.

## Editing

- Copy: edit `index.html`.
- Visual style: edit CSS custom properties in `styles.css`.
- Resume PDF: replace `resume.pdf`.
- YouTube URL: search `script.js` and `index.html` for `href="#"` and update.
