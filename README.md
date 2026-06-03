# vischeck

A Claude Code plugin for visual verification of UI changes. Bundles a screenshot CLI, a smart PostToolUse hook, and a skill with dev auth bypass patterns for any framework.

## What's included

| Component | Purpose |
|-----------|---------|
| `bin/screenshot` | Authenticated screenshot CLI via Playwright — auto-added to PATH |
| `hooks/` | PostToolUse hook — reminds Claude to verify view edits visually |
| `skills/verify/` | `vischeck:verify` skill — full instructions + framework dev auth snippets |

## Install

```bash
/plugin install github:mickzijdel/vischeck
```

No manual `settings.json` editing or binary copying needed — the plugin handles everything.

**Prerequisite:** `pip install playwright && playwright install chromium`

## Usage

The `screenshot` command is available in any Claude Code session once the plugin is active:

```bash
screenshot /dashboard                           # authenticated screenshot
screenshot /dashboard --dark                    # dark color scheme
screenshot /dashboard --width 375 --height 812  # mobile viewport
screenshot /dashboard --full-page               # full scrollable page
screenshot /dashboard --port 8080               # non-default port
screenshot /dashboard --no-auth                 # public page, skip login
screenshot /dashboard --auth-url "/login?token={token}&next={path}"  # custom auth URL
```

Screenshots save to `tmp/screenshots/` in the current working directory. Token is read from `DEV_AUTH_TOKEN` env var (default: `claude-screenshot-token`).

## Dev auth bypass

Implement a lightweight dev-only endpoint in your framework so `screenshot` can authenticate:

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
# views/dev_auth.py
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

# urls.py
if settings.DEBUG:
    urlpatterns += [path("dev-auth/login", dev_login)]
```

### Flask

```python
# blueprints/dev_auth.py
import os
from flask import Blueprint, abort, current_app, redirect, request
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

## Hook behaviour

After every `Write` or `Edit` on a view/template file, Claude is reminded to invoke `vischeck:verify`. The hook also:

- Checks `CLAUDE.md` for dark/light mode mentions — if found, suggests testing both; if absent, suggests documenting it
- Detects interactive elements (forms, buttons) and suggests playwright-cli testing

## Dark / light mode

Add a line to your project's `CLAUDE.md` so the hook gives the right advice:

```markdown
## UI: This app supports dark mode and light mode
```
