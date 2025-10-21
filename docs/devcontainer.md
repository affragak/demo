# Development Container Setup

This repository uses a Dev Container configuration with [DevPod](https://devpod.sh/) for consistent development environments across machines. The setup uses **Neovim** as the primary editor, with [Chezmoi](https://www.chezmoi.io/) for dotfile management and [mise](https://mise.jdx.dev/) for tool version management.

## Prerequisites

- [Docker](https://www.docker.com/get-started)
- [DevPod](https://devpod.sh/)

## Quick Start

Create and start the development container:

```bash
devpod up . --dotfiles git@github.com:user/dotfiles.git
```

This command will:
1. Build the container using the Dev Container configuration
2. Clone and apply your dotfiles via Chezmoi
3. Install all tools defined in `mise.toml`

The container will automatically install all required tools and configure your development environment.

## Container Configuration

### Base Image

Built on `mcr.microsoft.com/devcontainers/base:ubuntu-24.04` with [mise](https://mise.jdx.dev/) pre-installed for tool version management.

### Tool Management

Tools are managed at two levels:

#### Project Tools (mise.toml)

Project-specific tools installed automatically:

- **direnv** - Environment variable management
- **helm** - Kubernetes package manager
- **k9s** - Kubernetes CLI UI
- **kubectl** - Kubernetes command-line tool
- **kubens** - Kubernetes namespace switcher
- **python** 3.12 - Python runtime
- **uv** - Fast Python package installer

#### Global Tools (via Chezmoi dotfiles)

Personal development tools from `~/.config/mise/config.toml`:

- **bat** - Enhanced cat with syntax highlighting
- **chezmoi** - Dotfile manager
- **fzf** - Fuzzy finder
- **lsd** - Modern ls replacement
- **ripgrep** - Fast text search
- **fd** - Fast file finder
- **lazygit** - Terminal UI for git
- **neovim** - Text editor
- **node** - JavaScript runtime
- **usage** - CLI spec tool


### Dotfiles Structure

Chezmoi manages your dotfiles at `~/.local/share/chezmoi`:

```
~/.local/share/chezmoi/
├── setup                    # Initial setup script
├── dot_bashrc              # Bash configuration
├── dot_zshrc               # Zsh configuration
├── dot_config/             # Config directory
│   └── mise/
│       └── config.toml     # Global mise tools
├── bin/                    # Custom scripts
├── scripts/                # Helper scripts
└── .chezmoiscripts/        # Chezmoi automation scripts
```

### Port Forwarding

- Port `8000` is automatically forwarded from the container to your local machine

### Environment Variables

The container passes through the following environment variables from your local machine:

- `MISE_GITHUB_TOKEN` - GitHub token for mise (to prevent github API rate limit)

## Project Structure

```
.
├── .devcontainer/
│   ├── Dockerfile           # Container image definition
│   ├── devcontainer.json    # Dev Container configuration
│   └── scripts/
│       └── setup            # Post-creation setup script
├── mise.toml                # Tool version definitions
└── .envrc                   # direnv configuration
```


## Learn More

- [DevPod documentation](https://devpod.sh/docs/what-is-devpod)
- [Dev Containers specification](https://containers.dev/)
- [mise documentation](https://mise.jdx.dev/)
- [Chezmoi documentation](https://www.chezmoi.io/)
