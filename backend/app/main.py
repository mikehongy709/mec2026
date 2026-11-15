from bottle import Bottle, run, template, request, response, static_file, redirect
import json
import os
import time

import httplib2

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
CLIENT_SECRET_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "client_secret.json")
)

USER_HISTORY_STORE_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "user_history.json")
)



app = Bottle()



def get_session_from_environ(wsgi_environ):
    return wsgi_environ.get("beaker.session")


@app.route("/query", method="GET")
def query():
    query = request.query.get("q", "")
    if not query:
        return json.dumps({"error": "missing-query"})

    start_time = time.time()
    results = _search(query)
    end_time = time.time()

    response.content_type = "application/json"
    return json.dumps(
        {
            "query": query,
            "results": results,
            "time_taken": end_time - start_time,
        }
    )

@app.route("/query/temperature", method="GET")
def query_temperature():
    temperature = request.query.get("t", "")
    if not temperature:
        return json.dumps({"error": "missing-temperature"})

    start_time = time.time()
    results = _search(temperature)
    end_time = time.time()

    response.content_type = "application/json"
    return json.dumps(
        {
            "temperature": temperature,
            "results": results,
            "time_taken": end_time - start_time,
        }
    )


@app.route("/history")
def history_search():
    response.content_type = "application/json"
    user_email = _get_current_user_email()
    if not user_email:
        return json.dumps({})
    return json.dumps(_get_user_top_n(user_email, 20))


@app.route("/")
def index():
    r = static_file("index.html", root=FRONTEND_DIR)
    response.set_header("Cache-Control", "no-store")
    response.set_header("Pragma", "no-cache")
    response.set_header("Expires", "0")
    return r


@app.route("/<filename:path>")
def serve_static(filename):
    r = static_file(filename, root=FRONTEND_DIR)
    if filename.endswith(".js") or filename.endswith(".html"):
        response.set_header("Cache-Control", "no-store")
        response.set_header("Pragma", "no-cache")
        response.set_header("Expires", "0")
    return r


@app.get("/login")
def google_login():
    flow = flow_from_clientsecrets(
        CLIENT_SECRET_PATH,
        scope="https://www.googleapis.com/auth/plus.me https://www.googleapis.com/auth/userinfo.email",
        redirect_uri="http://localhost:8080/redirect",
    )
    uri = flow.step1_get_authorize_url()
    return redirect(str(uri))


@app.get("/redirect")
def oauth_redirect():
    code = request.query.get("code", "")
    if not code:
        return redirect("/")

    with open(CLIENT_SECRET_PATH, "r") as f:
        cs = json.load(f)["web"]

    scope = ["profile", "email"]
    flow = OAuth2WebServerFlow(
        client_id=cs["client_id"],
        client_secret=cs["client_secret"],
        scope=scope,
        redirect_uri="http://localhost:8080/redirect",
    )
    credentials = flow.step2_exchange(code)

    http = httplib2.Http()
    http = credentials.authorize(http)
    users_service = build("oauth2", "v2", http=http)
    user_document = users_service.userinfo().get().execute()
    user_email = user_document["email"]

    session_object = get_session_from_environ(request.environ)
    session_object["email_address"] = user_email
    session_object.save()
    return redirect("/")


@app.get("/logout")
def sign_out_and_clear_session():
    session_object = get_session_from_environ(request.environ)
    session_object.delete()
    return redirect("/")


@app.get("/api/session")
def api_get_session_status():
    session_object = get_session_from_environ(request.environ)
    current_email_address = (
        session_object.get("email_address") if session_object else None
    )
    response.content_type = "application/json"
    return json.dumps(
        {
            "signed_in": bool(current_email_address),
            "email_address": current_email_address,
        }
    )


@app.get("/api/user/history/recent10")
def api_user_history_recent10():
    email = _get_current_user_email()
    if not email:
        response.status = 401
        return json.dumps({"error": "signin-required"})
    response.content_type = "application/json"
    return json.dumps(_get_user_recent_n(email, 10))


@app.get("/api/user/history/top20")
def api_user_history_top20():
    email = _get_current_user_email()
    if not email:
        response.status = 401
        return json.dumps({"error": "signin-required"})
    response.content_type = "application/json"
    return json.dumps(_get_user_top_n(email, 20))


@app.post("/api/user/history/clear")
def api_user_history_clear():
    email = _get_current_user_email()
    if not email:
        response.status = 401
        return json.dumps({"error": "signin-required"})
    data = _load_user_histories()
    data[email] = {"counts": {}, "recent": []}
    _save_user_histories(data)
    response.content_type = "application/json"
    return json.dumps({"ok": True})


@app.error(404)
def error404(error):
    return static_file("404.html", root=FRONTEND_DIR)


if __name__ == "__main__":
    init_db()
    run(
        app=beaker_session_middleware_app,
        host='0.0.0.0',
        port=8080,
        debug=True,
        reloader=True,
    )
