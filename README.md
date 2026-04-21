# UM DiningClaw

Your AI-powered guide to the best dining halls on campus.

**[View the live site](https://qzjgeorge.github.io/UM-DiningClaw/)**

## What is this?

Michigan Dining runs 8 dining halls across campus, each with different menus every day. DiningClaw checks them all and uses AI to figure out where the best food is tonight — highlighting standout dishes, interesting cuisines, and premium proteins.

## How it works

When you run the pipeline locally, it:

1. **Reads** the dinner menus from all U-M dining halls
2. **Evaluates** the options using the Claude API
3. **Publishes** a fresh recommendation to the website

The generated site lives in `docs/`, so GitHub Pages can serve it directly from the repository.

## Run it locally

```bash
conda env create -f environment.yml
conda activate diningclaw
printf 'ANTHROPIC_API_KEY="your-key-here"\n' > .env
python3 main.py
```

`.env` is git-ignored and used by `publish.sh`. You can still export `ANTHROPIC_API_KEY`
in your shell if you prefer.

## Publish changes

Run the site update locally, then commit and push the regenerated `docs/` output:

```bash
./publish.sh
```

`publish.sh` runs the pipeline, stages the updated site files, creates a dated commit, and pushes to `main`.

The script will automatically prefer the `diningclaw` Conda environment if it exists.
You can override that with `CONDA_ENV_NAME` or force a specific interpreter with
`DININGCLAW_PYTHON=/path/to/python ./publish.sh`.

## Contributing

Ideas, suggestions, and contributions are all welcome! Feel free to:

- [Open an issue](https://github.com/QZJGeorge/UM-DiningClaw/issues) for bugs, feature requests, or feedback
- Submit a pull request if you'd like to contribute directly
- Star the repo if you find it useful
