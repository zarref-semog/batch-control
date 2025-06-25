from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
from PIL import Image
import os, json
from models import model
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from passlib.hash import sha256_crypt
from tools import converter_data, save_resized_image
from user import User

app = Flask(__name__)
app.secret_key = "batch-control-key"
app.config["DATABASE_FOLDER"] = "database"
app.config["UPLOAD_FOLDER"] = "uploads"

os.makedirs(app.config["DATABASE_FOLDER"], exist_ok=True)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(user_id)


@app.route("/register", methods=["GET", "POST"])
def register():
    db = model()

    if request.method == "POST":
        name = request.form["name"]
        trade_name = request.form.get("trade_name")
        cnpj = request.form.get("cnpj")
        address = request.form.get("address")
        email = request.form["email"]
        password = request.form["pw"]

        if db(db.user.email == email).isempty():
            hashed_pw = sha256_crypt.hash(password)
            db.user.insert(
                name=name,
                trade_name=trade_name,
                cnpj=cnpj,
                address=address,
                email=email,
                password=hashed_pw,
            )
            db.commit()
            flash("User registered successfully!", "success")
            return redirect(url_for("login"))
        else:
            flash("Email already registered.", "error")

    return render_template("register.html", simple_header=True)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "GET":
        return render_template("login.html", simple_header=True)

    email = request.form["email"]
    password = request.form["pw"]

    user = User(email, password)

    if user.get_id() is None:
        flash("Invalid login credentials", "error")
        return render_template("login.html", simple_header=True)

    login_user(user)
    return redirect(url_for("home"))


@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    db = model()
    page = int(request.args.get("page", 1))
    limit = 8
    offset = (page - 1) * limit

    # Filtros
    search = request.form.get("search", "").strip()
    status_id = request.form.get("status")
    date_filter = request.form.get("date")

    query = db.batch.id > 0  # sempre verdadeiro

    if search:
        query &= db.batch.code.contains(search)

    if status_id:
        query &= db.batch.status == int(status_id)

    if date_filter:
        try:
            from datetime import datetime

            parsed_date = datetime.strptime(date_filter, "%d/%m/%Y").date()
            query &= db.batch.production_date == parsed_date
        except ValueError:
            flash("Invalid date format", "error")

    total = db(query).count()

    results = db(query).select(
        db.batch.id,
        db.batch.code,
        db.batch.status,
        db.status.icon,
        left=db.status.on(db.batch.status == db.status.id),
        orderby=~db.batch.created_at,
        limitby=(offset, offset + limit),
    )

    batches = [
        {
            "id": row.batch.id,
            "code": row.batch.code,
            "icon": row.status.icon if row.status else "❓",
        }
        for row in results
    ]

    status_options = db(db.status).select(orderby=db.status.name)
    total_pages = (total + limit - 1) // limit

    return render_template(
        "home.html",
        batches=batches,
        status_options=status_options,
        current_page=page,
        total_pages=total_pages,
    )


@app.route("/batch", methods=["GET", "POST"])
@login_required
def create_batch():
    db = model()
    status_options = db(db.status).select()

    if request.method == "POST":
        images = [
            save_resized_image(f)
            for f in request.files.getlist("new_images[]")
            if f.filename
        ]

        form_data = {
            "code": request.form.get("code"),
            "production_date": converter_data(request.form.get("production_date")),
            "quantity": int(request.form.get("quantity") or 0),
            "owner": int(current_user.get_id() or 0),
            "status": int(request.form.get("status") or 0),
            "images": images,
            "details": json.loads(request.form.get("details") or "{}"),
        }

        result = db.batch.validate_and_insert(**form_data)

        errors = result["errors"]

        if errors:
            for field, error in errors.items():
                flash(f"{field.capitalize()}: {error}", "error")
            return render_template(
                "batch.html", batch=None, status_options=status_options
            )

        db.commit()
        flash("Batch created successfully!", "success")
        return redirect(url_for("edit_batch", id=result["id"]))

    return render_template("batch.html", batch=None, status_options=status_options)


@app.route("/batch/<int:id>", methods=["GET", "POST"])
@login_required
def edit_batch(id):
    db = model()
    batch = db.batch(id)
    if not batch:
        flash("Batch not found", "error")
        return redirect(url_for("home"))

    status_options = db(db.status).select()

    if request.method == "POST":
        if request.form.get("action") == "delete":
            for img in batch.images or []:
                try:
                    os.remove(os.path.join(app.config["UPLOAD_FOLDER"], img))
                except:
                    pass
            db(db.batch.id == id).delete()
            db.commit()
            flash("Batch deleted successfully", "success")
            return redirect(url_for("home"))

        to_delete = request.form.getlist("delete_images[]")
        updated_images = [img for img in (batch.images or []) if img not in to_delete]
        for img in to_delete:
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], img))
            except:
                pass
        for f in request.files.getlist("new_images[]"):
            if f.filename:
                updated_images.append(save_resized_image(f))

        form_data = {
            "code": request.form.get("code"),
            "production_date": converter_data(request.form.get("production_date")),
            "quantity": int(request.form.get("quantity") or 0),
            "status": int(request.form.get("status") or 0),
            "images": updated_images,
            "details": json.loads(request.form.get("details") or "{}"),
            "owner": int(current_user.get_id() or 0),
        }

        result = db.batch.validate_and_update(id, **form_data)
        errors = result["errors"]

        print(result)

        if errors:
            for field, error in errors.items():
                flash(f"{field.capitalize()}: {error}", "error")
            return render_template(
                "batch.html", batch=batch, status_options=status_options
            )

        db.commit()
        flash("Batch updated successfully!", "success")
        return redirect(url_for("edit_batch", id=id))

    return render_template("batch.html", batch=batch, status_options=status_options)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/dashboard")
@login_required
def dashboard():
    db = model()

    # Recuperar status e contar batches por status
    status_list = db(db.status).select(orderby=db.status.name)
    stats = []

    for status in status_list:
        count = db(db.batch.status == status.id).count()
        stats.append({
            "name": status.name,
            "icon": status.icon,
            "count": count,
        })

    return render_template("dashboard.html", stats=stats)


if __name__ == "__main__":
    app.run(debug=True)
