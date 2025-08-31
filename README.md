# project1-mortgage
A mortgage calculator made with Cursor AI (vibe coding).

You can use it to calculate your prospective mortgage and download the result as an .xlsx file. Calculate a monthly payment, total payments, and overpayment on a mortgage. 

The interface is styled in art‑deco and adapted for mobile devices.

## Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the development server:
   ```bash
   python app.py
   ```

3. Open in browser: [http://127.0.0.1:5000/]

## Form Fields

- Loan amount  
- Term (in years)  
- Annual interest rate  

## Formulas

For a non‑zero interest rate, the annuity payment formula is used:

\[
A = P \cdot r \cdot \frac{(1+r)^n}{(1+r)^n - 1}
\]

where **P** is the loan amount, **r** is the monthly rate, and **n** is the number of payments.  
For a zero interest rate, the monthly payment is simply **P / n**.

**Overpayment**: \( A \cdot n - P \).  

## Stack

- Python 3.10+
- Flask 3
- HTML/CSS (responsive, Art Deco)