import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_, inspect
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me-in-env")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/postgres",
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Сначала войди в систему."
login_manager.login_message_category = "warning"


class Role:
    STUDENT = "STUDENT"
    EMPLOYEE = "EMPLOYEE"
    LAB_STAFF = "LAB_STAFF"
    ADMIN = "ADMIN"

    ALL = [STUDENT, EMPLOYEE, LAB_STAFF, ADMIN]


class EquipmentStatus:
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    LOANED = "LOANED"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"

    ALL = [AVAILABLE, RESERVED, LOANED, OUT_OF_SERVICE]


class ReservationStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

    ACTIVE = [PENDING, APPROVED]
    ALL = [PENDING, APPROVED, REJECTED, CANCELLED, EXPIRED]


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default=Role.STUDENT)
    is_active_account = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    reservations = db.relationship(
        "Reservation",
        foreign_keys="Reservation.user_id",
        back_populates="user",
        lazy=True,
    )
    approved_reservations = db.relationship(
        "Reservation",
        foreign_keys="Reservation.approved_by_id",
        lazy=True,
    )
    notifications = db.relationship("Notification", back_populates="user", lazy=True)
    audit_logs = db.relationship("AuditLog", back_populates="actor", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles: str) -> bool:
        return self.role in roles


class Equipment(db.Model):
    __tablename__ = "equipment"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    laboratory = db.Column(db.String(120), nullable=False)
    serial_number = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    status = db.Column(
        db.String(30), nullable=False, default=EquipmentStatus.AVAILABLE, index=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    reservations = db.relationship("Reservation", back_populates="equipment", lazy=True)
    loans = db.relationship("Loan", back_populates="equipment", lazy=True)


class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=False)
    start_at = db.Column(db.DateTime, nullable=False, index=True)
    end_at = db.Column(db.DateTime, nullable=False, index=True)
    purpose = db.Column(db.String(255))
    status = db.Column(
        db.String(30), nullable=False, default=ReservationStatus.PENDING, index=True
    )
    decision_note = db.Column(db.String(255))
    approved_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = db.relationship("User", foreign_keys=[user_id], back_populates="reservations")
    approved_by = db.relationship("User", foreign_keys=[approved_by_id])
    equipment = db.relationship("Equipment", back_populates="reservations")
    loan = db.relationship("Loan", back_populates="reservation", uselist=False)


class Loan(db.Model):
    __tablename__ = "loans"

    id = db.Column(db.Integer, primary_key=True)
    reservation_id = db.Column(
        db.Integer, db.ForeignKey("reservations.id"), nullable=False, unique=True
    )
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=False)
    checked_out_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    checked_in_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    check_out_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    check_in_at = db.Column(db.DateTime)
    due_at = db.Column(db.DateTime, nullable=False)
    condition_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    reservation = db.relationship("Reservation", back_populates="loan")
    equipment = db.relationship("Equipment", back_populates="loans")
    checked_out_by = db.relationship("User", foreign_keys=[checked_out_by_id])
    checked_in_by = db.relationship("User", foreign_keys=[checked_in_by_id])


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    channel = db.Column(db.String(30), nullable=False, default="IN_APP")
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    actor = db.relationship("User", back_populates="audit_logs")


@login_manager.user_loader

def load_user(user_id: str):
    return db.session.get(User, int(user_id))


@app.context_processor
def inject_now():
    return {"now": datetime.utcnow()}


def parse_dt(value: str):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None



def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            if current_user.role not in roles:
                abort(403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator



def create_notification(user_id: int, title: str, message: str) -> None:
    notification = Notification(user_id=user_id, title=title, message=message)
    db.session.add(notification)



def log_action(action: str, target_type: str, target_id=None, details: str | None = None):
    actor_id = current_user.id if current_user.is_authenticated else None
    db.session.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
    )



def has_conflict(equipment_id: int, start_at: datetime, end_at: datetime, exclude_id=None) -> bool:
    query = Reservation.query.filter(
        Reservation.equipment_id == equipment_id,
        Reservation.status.in_(ReservationStatus.ACTIVE),
        Reservation.start_at < end_at,
        Reservation.end_at > start_at,
    )
    if exclude_id:
        query = query.filter(Reservation.id != exclude_id)
    return db.session.query(query.exists()).scalar()


@app.route("/")
def index():
    stats = {
        "equipment_count": db.session.query(func.count(Equipment.id)).scalar() or 0,
        "reservation_count": db.session.query(func.count(Reservation.id)).scalar() or 0,
        "loan_count": db.session.query(func.count(Loan.id)).scalar() or 0,
        "available_count": db.session.query(func.count(Equipment.id))
        .filter(Equipment.status == EquipmentStatus.AVAILABLE)
        .scalar()
        or 0,
    }
    newest_equipment = Equipment.query.order_by(Equipment.created_at.desc()).limit(6).all()
    return render_template("index.html", stats=stats, newest_equipment=newest_equipment)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", Role.STUDENT)

        if not full_name or not email or not password:
            flash("Заполни все обязательные поля.", "danger")
            return render_template("register.html", roles=[Role.STUDENT, Role.EMPLOYEE])

        if role not in [Role.STUDENT, Role.EMPLOYEE]:
            role = Role.STUDENT

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Пользователь с таким email уже существует.", "danger")
            return render_template("register.html", roles=[Role.STUDENT, Role.EMPLOYEE])

        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Аккаунт создан. Теперь войди в систему.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", roles=[Role.STUDENT, Role.EMPLOYEE])


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Неверный email или пароль.", "danger")
            return render_template("login.html")

        if not user.is_active_account:
            flash("Аккаунт заблокирован.", "danger")
            return render_template("login.html")

        login_user(user)
        flash(f"С возвращением, {user.full_name}!", "success")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Ты вышел из системы.", "info")
    return redirect(url_for("index"))


@app.route("/equipment")
def equipment_list():
    category = request.args.get("category", "").strip()
    laboratory = request.args.get("laboratory", "").strip()
    status = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()

    query = Equipment.query
    if category:
        query = query.filter(Equipment.category == category)
    if laboratory:
        query = query.filter(Equipment.laboratory == laboratory)
    if status:
        query = query.filter(Equipment.status == status)
    if q:
        query = query.filter(
            or_(
                Equipment.name.ilike(f"%{q}%"),
                Equipment.serial_number.ilike(f"%{q}%"),
                Equipment.description.ilike(f"%{q}%"),
            )
        )

    equipment = query.order_by(Equipment.name.asc()).all()
    categories = [row[0] for row in db.session.query(Equipment.category).distinct().order_by(Equipment.category)]
    laboratories = [row[0] for row in db.session.query(Equipment.laboratory).distinct().order_by(Equipment.laboratory)]

    return render_template(
        "equipment_list.html",
        equipment=equipment,
        categories=categories,
        laboratories=laboratories,
        statuses=EquipmentStatus.ALL,
        filters={
            "category": category,
            "laboratory": laboratory,
            "status": status,
            "q": q,
        },
    )


@app.route("/equipment/<int:equipment_id>", methods=["GET", "POST"])
def equipment_detail(equipment_id):
    equipment = db.session.get(Equipment, equipment_id)
    if not equipment:
        abort(404)

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Для бронирования нужно войти в систему.", "warning")
            return redirect(url_for("login"))

        if current_user.role not in [Role.STUDENT, Role.EMPLOYEE, Role.LAB_STAFF, Role.ADMIN]:
            abort(403)

        start_at = parse_dt(request.form.get("start_at"))
        end_at = parse_dt(request.form.get("end_at"))
        purpose = request.form.get("purpose", "").strip()

        if equipment.status == EquipmentStatus.OUT_OF_SERVICE:
            flash("Этот предмет сейчас недоступен для бронирования.", "danger")
            return redirect(url_for("equipment_detail", equipment_id=equipment.id))

        if not start_at or not end_at or end_at <= start_at:
            flash("Проверь дату и время бронирования.", "danger")
            return redirect(url_for("equipment_detail", equipment_id=equipment.id))

        if has_conflict(equipment.id, start_at, end_at):
            flash("Выбранный интервал занят. Выбери другое время.", "danger")
            return redirect(url_for("equipment_detail", equipment_id=equipment.id))

        status = ReservationStatus.PENDING
        reservation = Reservation(
            user_id=current_user.id,
            equipment_id=equipment.id,
            start_at=start_at,
            end_at=end_at,
            purpose=purpose,
            status=status,
        )
        db.session.add(reservation)
        equipment.status = EquipmentStatus.RESERVED
        create_notification(
            current_user.id,
            "Создана новая заявка",
            f"Резервация для {equipment.name} создана на период {start_at:%d.%m.%Y %H:%M} - {end_at:%d.%m.%Y %H:%M}.",
        )
        log_action("RESERVATION_CREATED", "reservation", details=f"equipment={equipment.id}")
        db.session.commit()

        flash("Заявка создана. Она ожидает подтверждения лаборатории.", "success")
        return redirect(url_for("my_reservations"))

    reservations = (
        Reservation.query.filter_by(equipment_id=equipment.id)
        .order_by(Reservation.start_at.asc())
        .all()
    )
    return render_template(
        "equipment_detail.html",
        equipment=equipment,
        reservations=reservations,
        ReservationStatus=ReservationStatus,
    )


@app.route("/my/reservations")
@login_required
def my_reservations():
    reservations = (
        Reservation.query.filter_by(user_id=current_user.id)
        .order_by(Reservation.created_at.desc())
        .all()
    )
    loans = (
        Loan.query.join(Reservation)
        .filter(Reservation.user_id == current_user.id)
        .order_by(Loan.created_at.desc())
        .all()
    )
    return render_template("my_reservations.html", reservations=reservations, loans=loans)


@app.post("/my/reservations/<int:reservation_id>/cancel")
@login_required
def cancel_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        abort(404)
    if reservation.user_id != current_user.id and not current_user.has_role(Role.ADMIN, Role.LAB_STAFF):
        abort(403)
    if reservation.status not in [ReservationStatus.PENDING, ReservationStatus.APPROVED]:
        flash("Эту резервацию уже нельзя отменить.", "warning")
        return redirect(url_for("my_reservations"))
    if reservation.start_at <= datetime.utcnow():
        flash("Нельзя отменить резервацию после начала периода.", "warning")
        return redirect(url_for("my_reservations"))

    reservation.status = ReservationStatus.CANCELLED
    if reservation.equipment.status == EquipmentStatus.RESERVED:
        reservation.equipment.status = EquipmentStatus.AVAILABLE
    create_notification(
        reservation.user_id,
        "Резервация отменена",
        f"Резервация #{reservation.id} была отменена.",
    )
    log_action("RESERVATION_CANCELLED", "reservation", reservation.id)
    db.session.commit()
    flash("Резервация отменена.", "success")
    return redirect(url_for("my_reservations"))


@app.route("/notifications")
@login_required
def notifications():
    items = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template("notifications.html", items=items)


@app.post("/notifications/<int:notification_id>/read")
@login_required
def mark_notification_read(notification_id):
    notification = db.session.get(Notification, notification_id)
    if not notification:
        abort(404)
    if notification.user_id != current_user.id:
        abort(403)
    notification.is_read = True
    db.session.commit()
    return redirect(url_for("notifications"))


@app.route("/lab")
@role_required(Role.LAB_STAFF, Role.ADMIN)
def lab_dashboard():
    pending_reservations = (
        Reservation.query.filter_by(status=ReservationStatus.PENDING)
        .order_by(Reservation.start_at.asc())
        .all()
    )
    approved_reservations = (
        Reservation.query.filter_by(status=ReservationStatus.APPROVED)
        .order_by(Reservation.start_at.asc())
        .all()
    )
    active_loans = Loan.query.filter(Loan.check_in_at.is_(None)).order_by(Loan.due_at.asc()).all()
    return render_template(
        "lab_dashboard.html",
        pending_reservations=pending_reservations,
        approved_reservations=approved_reservations,
        active_loans=active_loans,
        EquipmentStatus=EquipmentStatus,
    )


@app.post("/lab/reservations/<int:reservation_id>/approve")
@role_required(Role.LAB_STAFF, Role.ADMIN)
def approve_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        abort(404)
    if reservation.status != ReservationStatus.PENDING:
        flash("Резервация уже обработана.", "warning")
        return redirect(url_for("lab_dashboard"))
    if has_conflict(reservation.equipment_id, reservation.start_at, reservation.end_at, exclude_id=reservation.id):
        flash("Нельзя подтвердить: найден конфликт по времени.", "danger")
        return redirect(url_for("lab_dashboard"))

    reservation.status = ReservationStatus.APPROVED
    reservation.approved_by_id = current_user.id
    reservation.equipment.status = EquipmentStatus.RESERVED
    create_notification(
        reservation.user_id,
        "Резервация подтверждена",
        f"Заявка #{reservation.id} на {reservation.equipment.name} была подтверждена.",
    )
    log_action("RESERVATION_APPROVED", "reservation", reservation.id)
    db.session.commit()
    flash("Резервация подтверждена.", "success")
    return redirect(url_for("lab_dashboard"))


@app.post("/lab/reservations/<int:reservation_id>/reject")
@role_required(Role.LAB_STAFF, Role.ADMIN)
def reject_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        abort(404)
    if reservation.status != ReservationStatus.PENDING:
        flash("Резервация уже обработана.", "warning")
        return redirect(url_for("lab_dashboard"))

    note = request.form.get("decision_note", "Отклонено лабораторией.").strip()
    reservation.status = ReservationStatus.REJECTED
    reservation.decision_note = note
    if reservation.equipment.status == EquipmentStatus.RESERVED:
        reservation.equipment.status = EquipmentStatus.AVAILABLE
    create_notification(
        reservation.user_id,
        "Резервация отклонена",
        f"Заявка #{reservation.id} отклонена. Причина: {note}",
    )
    log_action("RESERVATION_REJECTED", "reservation", reservation.id, note)
    db.session.commit()
    flash("Резервация отклонена.", "info")
    return redirect(url_for("lab_dashboard"))


@app.post("/lab/reservations/<int:reservation_id>/checkout")
@role_required(Role.LAB_STAFF, Role.ADMIN)
def checkout_reservation(reservation_id):
    reservation = db.session.get(Reservation, reservation_id)
    if not reservation:
        abort(404)
    if reservation.status != ReservationStatus.APPROVED:
        flash("Для выдачи нужна подтвержденная резервация.", "danger")
        return redirect(url_for("lab_dashboard"))
    if reservation.loan:
        flash("Выдача уже зарегистрирована.", "warning")
        return redirect(url_for("lab_dashboard"))

    loan = Loan(
        reservation_id=reservation.id,
        equipment_id=reservation.equipment_id,
        checked_out_by_id=current_user.id,
        due_at=reservation.end_at,
    )
    db.session.add(loan)
    reservation.equipment.status = EquipmentStatus.LOANED
    create_notification(
        reservation.user_id,
        "Оборудование выдано",
        f"Для резервации #{reservation.id} зафиксирована выдача. Срок возврата: {reservation.end_at:%d.%m.%Y %H:%M}.",
    )
    log_action("LOAN_CHECKOUT", "loan", details=f"reservation={reservation.id}")
    db.session.commit()
    flash("Выдача оборудования зафиксирована.", "success")
    return redirect(url_for("lab_dashboard"))


@app.post("/lab/loans/<int:loan_id>/checkin")
@role_required(Role.LAB_STAFF, Role.ADMIN)
def checkin_loan(loan_id):
    loan = db.session.get(Loan, loan_id)
    if not loan:
        abort(404)
    if loan.check_in_at is not None:
        flash("Возврат уже зафиксирован.", "warning")
        return redirect(url_for("lab_dashboard"))

    condition_note = request.form.get("condition_note", "").strip()
    new_status = request.form.get("equipment_status", EquipmentStatus.AVAILABLE)
    if new_status not in [EquipmentStatus.AVAILABLE, EquipmentStatus.OUT_OF_SERVICE]:
        new_status = EquipmentStatus.AVAILABLE

    loan.check_in_at = datetime.utcnow()
    loan.checked_in_by_id = current_user.id
    loan.condition_note = condition_note
    loan.equipment.status = new_status

    create_notification(
        loan.reservation.user_id,
        "Оборудование возвращено",
        f"Возврат по резервации #{loan.reservation_id} зарегистрирован. Статус оборудования: {new_status}.",
    )
    log_action("LOAN_CHECKIN", "loan", loan.id, condition_note)
    db.session.commit()
    flash("Возврат оборудования подтвержден.", "success")
    return redirect(url_for("lab_dashboard"))


@app.route("/admin/equipment")
@role_required(Role.ADMIN)
def admin_equipment_list():
    equipment = Equipment.query.order_by(Equipment.created_at.desc()).all()
    return render_template("admin_equipment_list.html", equipment=equipment)


@app.route("/admin/equipment/new", methods=["GET", "POST"])
@role_required(Role.ADMIN)
def admin_equipment_new():
    if request.method == "POST":
        item = Equipment(
            name=request.form.get("name", "").strip(),
            category=request.form.get("category", "").strip(),
            laboratory=request.form.get("laboratory", "").strip(),
            serial_number=request.form.get("serial_number", "").strip(),
            description=request.form.get("description", "").strip(),
            image_url=request.form.get("image_url", "").strip(),
            status=request.form.get("status", EquipmentStatus.AVAILABLE),
        )
        if not item.name or not item.category or not item.laboratory or not item.serial_number:
            flash("Заполни все обязательные поля.", "danger")
            return render_template("admin_equipment_form.html", item=None, statuses=EquipmentStatus.ALL)

        db.session.add(item)
        log_action("EQUIPMENT_CREATED", "equipment")
        db.session.commit()
        flash("Оборудование добавлено.", "success")
        return redirect(url_for("admin_equipment_list"))

    return render_template("admin_equipment_form.html", item=None, statuses=EquipmentStatus.ALL)


@app.route("/admin/equipment/<int:equipment_id>/edit", methods=["GET", "POST"])
@role_required(Role.ADMIN)
def admin_equipment_edit(equipment_id):
    item = db.session.get(Equipment, equipment_id)
    if not item:
        abort(404)

    if request.method == "POST":
        item.name = request.form.get("name", "").strip()
        item.category = request.form.get("category", "").strip()
        item.laboratory = request.form.get("laboratory", "").strip()
        item.serial_number = request.form.get("serial_number", "").strip()
        item.description = request.form.get("description", "").strip()
        item.image_url = request.form.get("image_url", "").strip()
        status = request.form.get("status", EquipmentStatus.AVAILABLE)
        if status in EquipmentStatus.ALL:
            item.status = status
        log_action("EQUIPMENT_UPDATED", "equipment", item.id)
        db.session.commit()
        flash("Оборудование обновлено.", "success")
        return redirect(url_for("admin_equipment_list"))

    return render_template("admin_equipment_form.html", item=item, statuses=EquipmentStatus.ALL)


@app.post("/admin/equipment/<int:equipment_id>/toggle")
@role_required(Role.ADMIN)
def admin_equipment_toggle(equipment_id):
    item = db.session.get(Equipment, equipment_id)
    if not item:
        abort(404)
    item.status = (
        EquipmentStatus.AVAILABLE
        if item.status == EquipmentStatus.OUT_OF_SERVICE
        else EquipmentStatus.OUT_OF_SERVICE
    )
    log_action("EQUIPMENT_TOGGLED", "equipment", item.id, item.status)
    db.session.commit()
    flash("Статус оборудования изменен.", "success")
    return redirect(url_for("admin_equipment_list"))


@app.route("/admin/users")
@role_required(Role.ADMIN)
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=users, roles=Role.ALL)


@app.post("/admin/users/<int:user_id>/role")
@role_required(Role.ADMIN)
def admin_user_role(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    role = request.form.get("role", Role.STUDENT)
    if role not in Role.ALL:
        flash("Недопустимая роль.", "danger")
        return redirect(url_for("admin_users"))
    user.role = role
    log_action("USER_ROLE_UPDATED", "user", user.id, role)
    db.session.commit()
    flash("Роль пользователя обновлена.", "success")
    return redirect(url_for("admin_users"))


@app.errorhandler(403)
def forbidden(_error):
    return render_template("error.html", title="403", message="Доступ запрещен."), 403


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", title="404", message="Страница не найдена."), 404



def bootstrap_demo_users():
    inspector = inspect(db.engine)
    if not inspector.has_table("users"):
        return

    demo_users = [
        (os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@ersu.local"), os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "admin123"), "Administrator", Role.ADMIN),
        (os.getenv("BOOTSTRAP_LAB_EMAIL", "lab@ersu.local"), os.getenv("BOOTSTRAP_LAB_PASSWORD", "lab123"), "Laboratory Staff", Role.LAB_STAFF),
        (os.getenv("BOOTSTRAP_STUDENT_EMAIL", "student@ersu.local"), os.getenv("BOOTSTRAP_STUDENT_PASSWORD", "student123"), "Student Demo", Role.STUDENT),
        (os.getenv("BOOTSTRAP_EMPLOYEE_EMAIL", "employee@ersu.local"), os.getenv("BOOTSTRAP_EMPLOYEE_PASSWORD", "employee123"), "Employee Demo", Role.EMPLOYEE),
    ]

    changed = False
    for email, password, full_name, role in demo_users:
        existing = User.query.filter_by(email=email).first()
        if existing:
            continue
        user = User(full_name=full_name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        changed = True

    if changed:
        db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        bootstrap_demo_users()
    app.run(debug=True)
