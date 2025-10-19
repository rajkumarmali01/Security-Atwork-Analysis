from fpdf import FPDF
from datetime import datetime
from io import BytesIO

# -------------------------------------------------------
# 1️⃣ Class for Maruti Agency Bill Layout
# -------------------------------------------------------
class MarutiBill(FPDF):
    def header(self):
        # Red header bar
        self.set_fill_color(200, 0, 0)
        self.rect(10, 10, 190, 15, 'F')

        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "મારુતિ એજન્સી", ln=1, align="C")

        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", size=9)
        self.set_xy(10, 25)
        self.cell(0, 5, "શુભમ કોમ્પલેક્ષ, નેત્રંગ રોડ, રાજપારડી, જી. ભરૂચ.  M: 94291 26777", ln=1, align="C")
        self.set_font("Helvetica", "B", 9)
        self.set_xy(10, 30)
        self.cell(0, 5, "GST : 24AGVPM7286K1ZH", ln=1, align="C")

    def footer(self):
        self.set_y(-25)
        self.set_font("Helvetica", size=9)
        self.cell(0, 5, "Subject to Jhagadia Jurisdiction", ln=1, align="L")
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, "વતી, મારુતિ એજન્સી", ln=1, align="R")

    # ---------------------------------------------------
    # Draw the Bill Layout
    # ---------------------------------------------------
    def draw_bill(self, bill_no, customer_name, items):
        self.add_page()
        self.set_font("Helvetica", size=11)

        # Customer + Date line
        self.set_xy(15, 40)
        self.cell(90, 8, f"નામ : {customer_name}")
        self.cell(40, 8, f"બીલ નંબર : {bill_no}")
        self.cell(40, 8, f"તારીખ : {datetime.now().strftime('%d-%m-%Y')}", ln=1)

        # Table header
        headers = ["ITEM", "RATE", "WEIGHT NOS", "GST", "AMOUNT"]
        col_widths = [70, 30, 30, 25, 35]
        self.set_fill_color(230, 230, 230)
        self.set_font("Helvetica", "B", 11)
        y_start = 55
        x = 15
        for i, head in enumerate(headers):
            self.rect(x, y_start, col_widths[i], 10)
            self.cell(col_widths[i], 10, head, align="C", fill=True)
            x += col_widths[i]
        self.ln()

        # Table rows
        self.set_font("Helvetica", size=10)
        y = y_start + 10
        total = 0
        for (item, rate, qty, gst, amt) in items:
            x = 15
            for val, w in zip([item, rate, qty, gst, amt], col_widths):
                self.rect(x, y, w, 8)
                self.cell(w, 8, str(val), align="C")
                x += w
            total += amt
            y += 8

        # Total line
        self.set_font("Helvetica", "B", 11)
        self.rect(15, y, sum(col_widths[:-1]), 10)
        self.cell(sum(col_widths[:-1]), 10, "TOTAL", align="R")
        self.rect(15 + sum(col_widths[:-1]), y, col_widths[-1], 10)
        self.cell(col_widths[-1], 10, f"₹ {total}", align="C", ln=1)

        # Amount in words
        self.set_y(y + 15)
        self.set_font("Helvetica", size=10)
        self.cell(0, 6, f"Rs. in Words : {num2words(total)} Only", ln=1)

# -------------------------------------------------------
# 2️⃣ Helper: Number → Words
# -------------------------------------------------------
def num2words(num):
    import inflect
    p = inflect.engine()
    return p.number_to_words(num, andword="")

# -------------------------------------------------------
# 3️⃣ Example usage
# -------------------------------------------------------
if __name__ == "__main__":
    items = [
        ("Rice", 80, 10, "5%", 800),
        ("Sugar", 45, 5, "5%", 225),
        ("Oil", 150, 2, "5%", 300),
        ("Tea", 180, 1, "5%", 180),
    ]

    pdf = MarutiBill()
    pdf.draw_bill("001", "Rajesh Patel", items)

    buffer = BytesIO()
    pdf.output(buffer)
    with open("Maruti_Invoice.pdf", "wb") as f:
        f.write(buffer.getvalue())

    print("✅ Maruti Agency bill generated successfully!")