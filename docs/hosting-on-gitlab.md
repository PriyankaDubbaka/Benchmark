# Hosting the dashboard on BAM GitLab

**Status on 10 Nov 2026: not hosted yet.** The setup is written and sits in the repository. It has not been pushed to BAM's GitLab and has not been tested there. The steps below take about 15 minutes if Pages and a runner are available.

## What the setup is

Two pieces.

**1. A command that builds a read-only copy of the dashboard**

```
python3 -m bambench export-site public
```

It writes a folder of plain files (HTML, CSS, JavaScript and a few JSON files). No server and no database are needed to show it. The copy contains:

- the leaderboard, model cards and the open-track document list
- closed-track scores only for systems published with `export-closed`, which needs 20 or more scored pages
- no closed-track document names, page text, page images or raw model output
- no annotation, compare or run pages, since those need the cluster

**2. `.gitlab-ci.yml` in the repository root**

```yaml
stages:
  - test
  - deploy

default:
  image: python:3.12-slim

test:
  stage: test
  before_script:
    - apt-get update -qq && apt-get install -y -qq --no-install-recommends poppler-utils git
  script:
    - python -m unittest discover -q tests

pages:
  stage: deploy
  script:
    - python -m bambench export-site public
  artifacts:
    paths:
      - public
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

GitLab reads this file by itself. On every push it runs the tests. On a push to the default branch it also builds the copy and publishes it with GitLab Pages.

## Look at it today, without GitLab

On your laptop or the cluster login node:

```
git pull
python3 -m bambench export-site public
python3 -m http.server -d public 8000
```

Then open http://127.0.0.1:8000. That is exactly what colleagues would see.

## Put it on BAM GitLab

1. **Create an empty project** in BAM GitLab (New project, Create blank project, no README). Set visibility to Internal or Private. Copy its clone URL.

2. **Push the code from the cluster.** The Pages job only runs on the default branch, so push the current work as `main`:

   ```
   cd ~/Benchmark
   git pull
   git remote add bam <clone URL of the new project>
   git push bam pw2/compare-and-models:main
   ```

   Check first that no closed-track file is in the history. This must print only `data/closed/README.md`:

   ```
   git log --all --name-only --pretty=format: -- data/closed | sort -u
   ```

   `data/closed/` is ignored by git, and the commit hook blocks it as long as you ran `git config core.hooksPath .githooks` once in that clone.

3. **Watch the pipeline.** In the project, open Build, Pipelines. You should see `test`, then `pages`. When `pages` is green, the address is under Deploy, Pages.

4. **Limit who can open it.** Settings, General, Visibility, then Pages: choose "Only project members" or "Everyone with access", depending on whether all BAM staff should see it. Decide this with the team lead before sharing the link.

5. **Updating later.** After new closed-track results are cleared with `python3 -m bambench export-closed` and committed, `git push bam <branch>:main` rebuilds the page.

## Three things to check with IT

- **Is GitLab Pages switched on at BAM?** It is an administrator setting on self-hosted GitLab. If the Deploy menu has no Pages entry, ask IT.
- **Is there a CI runner for your project?** Without one the pipeline stays "pending". Ask IT for a shared runner.
- **Can the runner download from the internet?** The jobs pull a `python:3.12-slim` image and install Poppler with `apt-get`. If BAM's runner is offline, the `pages` job still works with any local Python 3.11+ image, because the export needs no extra packages. Only the `test` job needs Poppler.

If Pages is not available at all, the same `public` folder can be put on any internal web server or a shared drive. It is just files.

## Before you share the link

- The public certificates in `dataset/` are marked "redistribution permission unverified". Inside BAM that is fine. Do not make the GitLab project public before that is cleared.
- All scores still rest on draft labels from one annotator. The page says so at the top.
