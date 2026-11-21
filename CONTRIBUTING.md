# How we branch

`main` is the snapshot we would show a supervisor. `dev` is where the project actually moves. Nobody pushes straight to either one.

## Branches

| Branch | What it is |
|---|---|
| `main` | Protected. Updated only by a pull request from `dev`, when a milestone is ready to freeze. |
| `dev` | Protected integration branch. All feature pull requests target `dev`. |
| `your-name/short-topic` | Where you work. Examples: `mustafa/classify-baseline`, `abdur/gold-labels`. |

GitHub rejects direct pushes, force-pushes, and deletion of `main` and `dev`. A pull request is the only way onto those branches. A review is not required, so one of you can merge when the other is not around. Add a required reviewer later if you want that gate.

## Daily loop

```powershell
git checkout dev
git pull origin dev
git checkout -b mustafa/short-topic
```

Do the work, commit on that branch, then:

```powershell
git push -u origin mustafa/short-topic
gh pr create --base dev --title "short topic" --body "what changed and how you checked it"
```

After the pull request is merged, update local `dev` and delete the feature branch.

```powershell
git checkout dev
git pull origin dev
git branch -d mustafa/short-topic
```

## What does not go in a commit

- `datasets/` images and archives
- `runs/` checkpoints
- `.env`, Kaggle tokens, anything with a password

## Updating `main`

Only from `dev`, and only when you mean to freeze a milestone (a defence, a report cutoff, a demo):

```powershell
gh pr create --base main --head dev --title "Freeze: what this snapshot contains"
```
