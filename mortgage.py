from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class MortgageResult:
    principal: float
    annual_rate: float
    years: int
    num_payments: int
    monthly_payment: float
    total_paid: float
    overpayment: float
    income_required: float
    affordability_ratio: float
    schedule: List["AmortizationRow"]
    chart_labels: List[int]
    chart_principal_series: List[float]
    chart_interest_series: List[float]


@dataclass
class AmortizationRow:
    month: int
    payment: float
    principal_component: float
    interest_component: float
    remaining_balance: float


AFFORDABILITY_RATIO = 0.35  # 35% платежа от ежемесячного дохода


def calculate_overpayment(principal: float, years: int, annual_rate: float, prepay_month: int = None, prepay_amount: float = None, prepay_strategy: str = "reduce_payment") -> MortgageResult:
    if principal <= 0:
        raise ValueError("Principal must be positive")
    if years <= 0:
        raise ValueError("Years must be positive")
    if annual_rate < 0:
        raise ValueError("Annual rate cannot be negative")

    num_payments = years * 12
    monthly_rate = (annual_rate / 100.0) / 12.0

    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        factor = (1 + monthly_rate) ** num_payments
        monthly_payment = principal * monthly_rate * factor / (factor - 1)

    total_paid = monthly_payment * num_payments
    overpayment = total_paid - principal
    income_required = monthly_payment / AFFORDABILITY_RATIO if AFFORDABILITY_RATIO > 0 else monthly_payment

    # Build amortization schedule with prepayment logic
    schedule: List[AmortizationRow] = []
    remaining = principal
    interest_series: List[float] = []
    principal_series: List[float] = []
    current_payment = monthly_payment
    actual_num_payments = num_payments
    
    for m in range(1, num_payments + 1):
        if monthly_rate == 0:
            interest_component = 0.0
        else:
            interest_component = remaining * monthly_rate
        
        principal_component = current_payment - interest_component
        if principal_component > remaining:
            principal_component = remaining
            monthly_payment_actual = principal_component + interest_component
        else:
            monthly_payment_actual = current_payment
        
        # Обычное погашение основного долга
        remaining = max(0.0, remaining - principal_component)
        
        # Досрочное погашение (происходит ПОСЛЕ обычного платежа)
        prepay_this_month = 0
        if prepay_month and prepay_amount and m == prepay_month and remaining >= prepay_amount:
            remaining = max(0.0, remaining - prepay_amount)
            prepay_this_month = prepay_amount
            
            if prepay_strategy == "reduce_term":
                # Пересчитываем срок с тем же платежом
                if remaining > 0:
                    if monthly_rate > 0:
                        # Для процентного кредита
                        remaining_months = -math.log(1 - (remaining * monthly_rate) / current_payment) / math.log(1 + monthly_rate)
                        actual_num_payments = m + int(math.ceil(remaining_months))
                    else:
                        # Для рассрочки (без процентов)
                        remaining_months = math.ceil(remaining / current_payment)
                        actual_num_payments = m + remaining_months
                else:
                    actual_num_payments = m
            elif prepay_strategy == "reduce_payment":
                # Пересчитываем платёж на оставшийся срок (начиная со следующего месяца)
                remaining_months = num_payments - m  # оставшиеся месяцы после текущего
                if remaining > 0 and remaining_months > 0:
                    if monthly_rate > 0:
                        # Для процентного кредита - используем остаток долга для пересчёта
                        factor = (1 + monthly_rate) ** remaining_months
                        current_payment = remaining * monthly_rate * factor / (factor - 1)
                    else:
                        # Для рассрочки (без процентов)
                        current_payment = remaining / remaining_months
                else:
                    current_payment = 0
        
        schedule.append(
            AmortizationRow(
                month=m,
                payment=monthly_payment_actual + prepay_this_month,
                principal_component=principal_component + prepay_this_month,
                interest_component=interest_component,
                remaining_balance=remaining,
            )
        )
        principal_series.append(principal_component)
        interest_series.append(interest_component)
        
        if remaining <= 0:
            actual_num_payments = m
            break

    labels = list(range(1, len(schedule) + 1))

    # Пересчитываем итоговые суммы на основе фактического графика
    actual_total_paid = sum(row.payment for row in schedule)
    actual_overpayment = actual_total_paid - principal

    return MortgageResult(
        principal=principal,
        annual_rate=annual_rate,
        years=years,
        num_payments=actual_num_payments,
        monthly_payment=monthly_payment,
        total_paid=actual_total_paid,
        overpayment=actual_overpayment,
        income_required=income_required,
        affordability_ratio=AFFORDABILITY_RATIO,
        schedule=schedule,
        chart_labels=labels,
        chart_principal_series=principal_series,
        chart_interest_series=interest_series,
    )


