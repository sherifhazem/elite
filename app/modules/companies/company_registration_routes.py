from flask import Blueprint, render_template, request, redirect, flash, url_for, jsonify
from http import HTTPStatus
from app.modules.companies.forms.company_registration_form import CompanyRegistrationForm
from app.modules.companies.services.company_registration_service import register_company_account

company_bp = Blueprint(
    "company",
    __name__,
    url_prefix="/company",
    template_folder="templates",
    static_folder="static",
)


@company_bp.route("/register", methods=["GET", "POST"])
def register_company():
    form = CompanyRegistrationForm()

    if request.method == "GET":
        return render_template("companies/register_company.html", form=form)

    if request.is_json:
        payload = {k: v for k, v in (getattr(request, "cleaned", {}) or {}).items() if not k.startswith("__")}
        result, status = register_company_account(payload)
        return jsonify(result), status

    if not form.validate_on_submit():
        missing_fields_labels = []
        other_errors = []

        # Collect errors
        for field_name, errors in form.errors.items():
            field = getattr(form, field_name)
            label = field.label.text
            for error in errors:
                # Check for common "required" error messages
                if error in ("هذا الحقل إلزامي.", "اختر مجال العمل", "اختر المدينة", "This field is required."):
                    missing_fields_labels.append(label)
                else:
                    other_errors.append(f"{label}: {error}")
        
        # Flash consolidated missing fields message
        if missing_fields_labels:
            flash(
                f"فضلاً تأكد من تعبئة الحقول الضرورية: {', '.join(missing_fields_labels)}",
                "danger"
            )

        # Flash other specific errors
        for err in other_errors:
            flash(err, "danger")

        return render_template("companies/register_company.html", form=form), HTTPStatus.BAD_REQUEST

    payload = {k: v for k, v in getattr(request, "cleaned", {}).items() if not k.startswith("__")}
    result, status = register_company_account(payload)

    if status == HTTPStatus.CREATED:
        flash("تم استلام طلب شركتك بنجاح.", "success")
        return redirect(url_for("company.register_company_success"))

    if isinstance(result, dict) and result.get("error"):
        flash(result["error"], "danger")

    return render_template("companies/register_company.html", form=form), status


@company_bp.route("/register/success", methods=["GET"])
def register_company_success():
    return render_template("companies/register_company_success.html")
