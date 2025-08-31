from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from flask import Flask, render_template, request

from mortgage import calculate_overpayment


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")


@app.template_filter("money")
def money_filter(value: float) -> str:
    try:
        return f"{value:,.2f}".replace(",", " ")
    except Exception:
        return str(value)


@app.template_filter("intspace")
def intspace_filter(value: float | int | str) -> str:
    try:
        num = float(str(value).replace(" ", "").replace(",", "."))
        integer_part = int(abs(num))
        sign = "-" if num < 0 else ""
        return sign + format(integer_part, ",").replace(",", " ")
    except Exception:
        return str(value)


@dataclass
class FormData:
    principal: Optional[float]
    down_payment: Optional[float]
    years: Optional[int]
    annual_rate: Optional[float]
    error: Optional[str] = None


def parse_form(principal_raw: str, years_raw: str, rate_raw: str, down_payment_raw: str, is_installment: bool = False) -> Tuple[Optional[FormData], Optional[str]]:
    try:
        principal = float(principal_raw)
        years = int(float(years_raw))
        if is_installment:
            annual_rate = 0.0
        else:
            annual_rate = float(rate_raw or 0)
        down_payment = float(down_payment_raw or 0)
    except (TypeError, ValueError):
        return None, "Пожалуйста, введите корректные числовые значения."

    if principal <= 0:
        return None, "Стоимость недвижимости должна быть больше 0."
    if years <= 0:
        return None, "Срок в годах должен быть больше 0."
    if not is_installment and annual_rate < 0:
        return None, "Процентная ставка не может быть отрицательной."
    if down_payment < 0:
        return None, "Первоначальный взнос не может быть отрицательным."
    if down_payment >= principal:
        return None, "Первоначальный взнос должен быть меньше стоимости недвижимости."

    return FormData(principal=principal, down_payment=down_payment, years=years, annual_rate=annual_rate), None


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error_message = None
    form_initial = {
        "principal": request.form.get("principal", ""),
        "down_payment": request.form.get("down_payment", ""),
        "years": request.form.get("years", ""),
        "rate": request.form.get("rate", ""),
        "prepay_month": request.form.get("prepay_month", ""),
        "prepay_amount": request.form.get("prepay_amount", ""),
        "prepay_strategy": request.form.get("prepay_strategy", "reduce_payment"),
        "prepayment_enabled": request.form.get("prepayment_enabled") == "1",
        "is_installment": request.form.get("is_installment") == "1",
    }

    if request.method == "POST":
        is_installment = request.form.get("is_installment") == "1"
        form_data, error_message = parse_form(
            request.form.get("principal", ""),
            request.form.get("years", ""),
            request.form.get("rate", ""),
            request.form.get("down_payment", ""),
            is_installment
        )

        if error_message is None and form_data is not None:
            effective_principal = form_data.principal - (form_data.down_payment or 0)
            
            # Обработка досрочного погашения
            prepay_month = None
            prepay_amount = None
            prepay_strategy = "reduce_payment"
            
            prepayment_enabled = request.form.get("prepayment_enabled") == "1"
            prepay_month_raw = request.form.get("prepay_month", "").strip()
            prepay_amount_raw = request.form.get("prepay_amount", "").strip()
            
            # Досрочное погашение учитывается только если галочка активна И поля заполнены
            if prepayment_enabled and prepay_month_raw and prepay_amount_raw:
                try:
                    prepay_month = int(float(prepay_month_raw.replace(" ", "").replace(",", ".")))
                    prepay_amount = float(prepay_amount_raw.replace(" ", "").replace(",", "."))
                    prepay_strategy = request.form.get("prepay_strategy", "reduce_payment")
                    
                    if prepay_month <= 0:
                        error_message = "Месяц досрочного платежа должен быть больше 0."
                    elif prepay_amount <= 0:
                        error_message = "Сумма досрочного платежа должна быть больше 0."
                except (TypeError, ValueError):
                    error_message = "Некорректные данные досрочного погашения."
            
            if error_message is None:
                calculation = calculate_overpayment(
                    principal=effective_principal,
                    years=form_data.years,
                    annual_rate=form_data.annual_rate,
                    prepay_month=prepay_month,
                    prepay_amount=prepay_amount,
                    prepay_strategy=prepay_strategy,
                )
                result = calculation


    return render_template("index.html", result=result, error_message=error_message, form_initial=form_initial)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)


