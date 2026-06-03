---
name: setup-auth
description: Set up the dev auth bypass route so the screenshot tool can authenticate. Invoke when screenshot fails with an auth/login redirect, or when the user explicitly asks to set up dev auth.
---

# vischeck:setup-auth

Before implementing anything, ask the user for permission:

> "To take authenticated screenshots I need to add a dev-only login bypass route to your app. This only activates in development/test and validates a token from `DEV_AUTH_TOKEN`. OK to add it?"

Only proceed once the user confirms.

## What to implement

A route at `/dev-auth/login?token=<token>&redirect_to=<path>` that:
1. Only activates in development/test mode
2. Validates the token against the `DEV_AUTH_TOKEN` env var (default: `claude-screenshot-token`)
3. Signs in a dev user (email: `claude-dev@localhost`)
4. Redirects to `redirect_to`

Pick the implementation for this project's framework:

## Rails

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
```

```ruby
# config/routes.rb — add inside the routes block
get "dev_auth/login", to: "dev_auth#login" if Rails.env.local?
```

```ruby
# db/seeds.rb — add inside a Rails.env.local? guard
if Rails.env.local?
  User.find_or_create_by(email: "claude-dev@localhost") do |u|
    u.password = SecureRandom.hex
    u.admin = true
  end
end
```

Then run `bin/rails db:seed` to create the dev user.

## Django

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
```

```python
# urls.py — only register in debug mode
if settings.DEBUG:
    urlpatterns += [path("dev-auth/login", dev_login)]
```

Create the dev user: `python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.get_or_create(email='claude-dev@localhost', defaults={'is_staff': True, 'is_superuser': True})"`

## Flask

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

Register the blueprint in your app factory and create the dev user via your seeding mechanism.

## FastAPI

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

Requires `starlette.middleware.sessions.SessionMiddleware` to be configured.

## After implementing

Verify the route works:
```bash
screenshot /some-path
```

If it redirects to a login page, the bypass isn't working — check the token and that the dev user exists.
