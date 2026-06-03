---
name: screenshot
description: Take authenticated screenshots of a local dev server and visually verify UI changes. Use after editing any view, template, component, or layout file.
---

# Screenshot Skill

Use the `screenshot` CLI to visually verify UI changes against a running dev server. Always Read the saved image after taking a screenshot.

## When to use

After editing any view, template, component, or layout file:
1. Take a screenshot and Read the image to check it visually
2. For interactive elements (forms, buttons, inputs), also test the interaction with playwright-cli

## Dark / light mode

Check this project's CLAUDE.md for any mention of dark mode or light mode:
- If dark mode **is** mentioned: take one screenshot in each mode (`screenshot <path>` and `screenshot <path> --dark`)
- If dark/light mode is **not mentioned**: take a single screenshot, then note to the user that they may want to add a line to CLAUDE.md documenting whether this project supports dark/light mode (e.g. `## UI: This app supports dark mode and light mode`)

## CLI reference

```bash
screenshot /path                           # authenticated screenshot (default port 3000)
screenshot /path --dark                    # dark color scheme
screenshot /path --width 375 --height 812  # mobile viewport
screenshot /path --full-page               # full scrollable page
screenshot /path --port 8080               # custom port
screenshot /path --no-auth                 # skip authentication (public pages)
screenshot /path --auth-url "/login?token={token}&next={path}"  # custom auth URL template
```

Token is read from `DEV_AUTH_TOKEN` env var (default: `claude-screenshot-token`). Screenshots save to `tmp/screenshots/` in the current working directory.

## Desktop + mobile

For significant layout changes, take both desktop (default 1280×720) and mobile (`--width 375 --height 812`) screenshots.

## Interactive testing with playwright-cli

For forms, buttons, and Stimulus controllers — don't just screenshot, actually use the feature:

```bash
# Authenticate and navigate
playwright-cli open "http://localhost:3000/dev_auth/login?token=claude-screenshot-token&redirect_to=/path"
playwright-cli state-save dev-auth.json

# Restore auth and use the page
playwright-cli state-load dev-auth.json
playwright-cli goto http://localhost:3000/path
playwright-cli snapshot          # see element refs
playwright-cli fill e5 "value"   # fill an input
playwright-cli click e3          # click a button
playwright-cli screenshot        # capture result
playwright-cli close
```

## Dev auth pattern

The `screenshot` tool authenticates via a dev-only bypass endpoint. Any framework can implement this contract:

**Contract:** A route at (configurable) `/dev-auth/login?token=<token>&redirect_to=<path>` that validates the token against `DEV_AUTH_TOKEN`, sets a session as a dev user, and redirects. Only active in development.

### Rails

```ruby
# app/controllers/dev_auth_controller.rb
class DevAuthController < ApplicationController
  skip_before_action :authenticate_user!
  before_action { raise ActionController::RoutingError, "not found" unless Rails.env.local? }

  def login
    token = ENV.fetch("DEV_AUTH_TOKEN", "claude-screenshot-token")
    raise ActionController::RoutingError, "forbidden" unless params[:token] == token
    user = User.find_by(email: "claude-dev@localhost") or raise "Run bin/rails db:seed"
    sign_in user
    redirect_to params.fetch(:redirect_to, root_path)
  end
end

# config/routes.rb
get "dev_auth/login", to: "dev_auth#login" if Rails.env.local?
```

Seed the dev user:
```ruby
# db/seeds.rb
if Rails.env.local?
  User.find_or_create_by(email: "claude-dev@localhost") do |u|
    u.password = SecureRandom.hex
    u.admin = true
  end
end
```

### Django

```python
# myapp/views/dev_auth.py
import os
from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.http import HttpResponseForbidden
from django.shortcuts import redirect

def dev_login(request):
    if not settings.DEBUG:
        return HttpResponseForbidden()
    token = os.environ.get("DEV_AUTH_TOKEN", "claude-screenshot-token")
    if request.GET.get("token") != token:
        return HttpResponseForbidden()
    User = get_user_model()
    user = User.objects.get(email="claude-dev@localhost")
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect(request.GET.get("redirect_to", "/"))

# urls.py (only include when DEBUG=True)
if settings.DEBUG:
    urlpatterns += [path("dev-auth/login", dev_login)]
```

### Flask

```python
# blueprints/dev_auth.py
import os
from flask import Blueprint, current_app, abort, redirect, request
from flask_login import login_user
from myapp.models import User

bp = Blueprint("dev_auth", __name__)

@bp.route("/dev-auth/login")
def login():
    if not current_app.debug:
        abort(404)
    token = os.environ.get("DEV_AUTH_TOKEN", "claude-screenshot-token")
    if request.args.get("token") != token:
        abort(403)
    user = User.query.filter_by(email="claude-dev@localhost").first_or_404()
    login_user(user)
    return redirect(request.args.get("redirect_to", "/"))
```

### FastAPI

```python
# routers/dev_auth.py
import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("/dev-auth/login")
async def dev_login(token: str, redirect_to: str = "/", request: Request = None):
    if os.environ.get("ENV", "development") != "development":
        raise HTTPException(404)
    if token != os.environ.get("DEV_AUTH_TOKEN", "claude-screenshot-token"):
        raise HTTPException(403)
    request.session["user_email"] = "claude-dev@localhost"
    return RedirectResponse(redirect_to)
```

## Installation

```bash
curl -fsSL https://raw.githubusercontent.com/mickzijdel/agent-screenshot/main/install.sh | bash
```

Then add the PostToolUse hook to `~/.claude/settings.json` — see the repo README for the settings snippet.

Prerequisites: `pip install playwright && playwright install chromium`
