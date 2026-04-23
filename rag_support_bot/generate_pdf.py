from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT

FAQ_CONTENT = [
    ("ShopEasy E-Commerce Support Knowledge Base", None, "title"),

    ("1. Orders & Tracking", None, "section"),
    ("Q: How do I place an order?", "To place an order, browse our catalog, add items to your cart, proceed to checkout, and provide your shipping and payment details. You will receive a confirmation email within 5 minutes of placing a successful order.", "qa"),
    ("Q: How can I track my order?", "Once your order is shipped, you will receive a tracking number via email and SMS. You can use this number on our website under 'Track Order', or visit the courier partner's website directly. Tracking updates are available within 24 hours of shipment.", "qa"),
    ("Q: Can I modify or cancel my order?", "Orders can be modified or cancelled within 30 minutes of placement. After 30 minutes, the order enters processing and cannot be changed. To request cancellation, go to 'My Orders' > select the order > click 'Cancel'. Refunds are processed within 5–7 business days.", "qa"),
    ("Q: My order shows delivered but I haven't received it.", "If your order status shows delivered but you haven't received it, first check with neighbours or building reception. If still missing, raise a complaint within 48 hours via 'My Orders' > 'Report an Issue'. Our team will investigate with the courier and resolve within 72 hours.", "qa"),
    ("Q: What happens if my order is delayed?", "If your order exceeds the estimated delivery date by more than 2 days, you will automatically receive a delivery delay notification. You can also contact our support team for expedited resolution. In cases of significant delay, we offer a discount coupon as compensation.", "qa"),

    ("2. Payments & Billing", None, "section"),
    ("Q: What payment methods do you accept?", "We accept all major credit and debit cards (Visa, Mastercard, RuPay), UPI (GPay, PhonePe, Paytm), net banking, EMI options, and ShopEasy Wallet. Cash on Delivery (COD) is available for orders under ₹5000 in select pin codes.", "qa"),
    ("Q: I was charged twice for one order. What should I do?", "If you notice a duplicate charge, do not panic. First, check if both transactions show in your bank statement. Sometimes a failed payment attempt is temporarily blocked and auto-reversed within 5–7 business days. If both charges are confirmed, contact support immediately with your order ID and bank statement screenshot. We will initiate a refund within 24 hours.", "qa"),
    ("Q: How does EMI work on ShopEasy?", "EMI is available on purchases above ₹3000 using select credit cards. At checkout, choose 'Pay via EMI', select your bank and tenure (3, 6, 9, or 12 months). No-cost EMI options are available on select products. Processing fees, if any, will be displayed before confirmation.", "qa"),
    ("Q: Why was my payment declined?", "Payments can be declined due to insufficient balance, incorrect card details, bank security blocks, or UPI limit exceeded. Try an alternative payment method or contact your bank. If the amount was deducted but order failed, it will be automatically refunded within 5–7 business days.", "qa"),
    ("Q: How do I get an invoice for my order?", "GST invoices are automatically generated for all orders. Download them from 'My Orders' > select order > 'Download Invoice'. Business customers can add their GSTIN in account settings for B2B invoices.", "qa"),

    ("3. Returns & Refunds", None, "section"),
    ("Q: What is your return policy?", "We offer a 10-day return window for most products from the date of delivery. Items must be unused, in original packaging, and with all tags intact. Electronics have a 7-day replacement-only policy. Certain items like innerwear, perishables, and customized products are non-returnable.", "qa"),
    ("Q: How do I initiate a return?", "Go to 'My Orders', select the item, click 'Return/Replace', choose the reason, and schedule a pickup. Our courier will collect the item within 3–5 business days. Ensure the product is packed securely. Refund is initiated after quality check at our warehouse.", "qa"),
    ("Q: When will I receive my refund?", "After the returned item passes quality check (2–3 business days), refund is processed as follows: Original payment method: 5–7 business days. ShopEasy Wallet: instant. UPI: 1–3 business days. For COD orders, refund is credited to your bank account via NEFT within 7 days.", "qa"),
    ("Q: My refund was rejected. Why?", "Refunds may be rejected if the item shows signs of use, damage caused by the customer, missing accessories or packaging, or if the return window has expired. You will receive a detailed rejection reason via email. You may appeal within 48 hours by contacting support with evidence.", "qa"),
    ("Q: Can I exchange a product instead of returning it?", "Yes, exchanges are available for size or colour variants of the same product, subject to availability. Initiate via 'My Orders' > 'Return/Replace' > 'Exchange'. If the desired variant is unavailable, a refund will be issued automatically.", "qa"),

    ("4. Account & Security", None, "section"),
    ("Q: How do I reset my password?", "Click 'Forgot Password' on the login page, enter your registered email or mobile number, and follow the OTP verification. Your password reset link expires in 15 minutes. If you don't receive it, check spam or try resending after 2 minutes.", "qa"),
    ("Q: My account has been hacked or compromised.", "If you suspect unauthorized access, immediately click 'Forgot Password' to regain control. Then go to Settings > Security > Log Out All Devices. Review your recent orders for unauthorized purchases. Contact our fraud team at fraud@shopeasy.in immediately. Do not share your OTP or password with anyone, including our staff.", "qa"),
    ("Q: How do I update my phone number or email?", "Go to Account Settings > Personal Information > Edit. OTP verification on the new number/email is required. For security reasons, you cannot change both email and phone number simultaneously. Changes take effect immediately.", "qa"),
    ("Q: How do I delete my ShopEasy account?", "Account deletion is permanent and irreversible. All order history, wallet balance, and saved information will be lost. To delete, go to Settings > Account > Delete Account. Any pending orders must be completed or cancelled first. Wallet balance must be withdrawn before deletion.", "qa"),

    ("5. Products & Sellers", None, "section"),
    ("Q: How do I know if a product is authentic?", "All sellers on ShopEasy are verified. Look for the 'ShopEasy Assured' badge for products that are quality-checked by us. Electronics and branded goods include serial number verification. If you suspect a counterfeit product, report it via 'My Orders' > 'Report Fake Product'.", "qa"),
    ("Q: A product I received is different from what was shown.", "If you receive a wrong or different product, raise a complaint within 48 hours via 'My Orders' > 'Report an Issue' > 'Wrong Product Received'. Attach clear photos. We will arrange a reverse pickup and send the correct product or issue a full refund.", "qa"),
    ("Q: How do I write a product review?", "After delivery, go to 'My Orders' > select product > 'Write a Review'. You can rate 1–5 stars, write a review, and upload photos or videos. Reviews are published after a 24-hour moderation check. Reviews help other buyers make informed decisions.", "qa"),
    ("Q: Can I contact the seller directly?", "You can message sellers via the product page > 'Ask a Question' or from your order page > 'Contact Seller'. Response time varies by seller, typically 24–48 hours. For urgent issues like delivery problems, always contact ShopEasy Support directly for faster resolution.", "qa"),

    ("6. Shipping & Delivery", None, "section"),
    ("Q: What are the delivery charges?", "Delivery is free for orders above ₹499. For orders below ₹499, a flat delivery fee of ₹40 applies. Express delivery (1–2 days) is available in metro cities for an additional ₹99. ShopEasy Plus members enjoy free delivery on all orders.", "qa"),
    ("Q: Do you deliver internationally?", "Currently, ShopEasy delivers only within India. We cover 27,000+ pin codes. For remote areas, delivery may take 7–10 business days. International shipping is on our roadmap for 2025.", "qa"),
    ("Q: Can I change my delivery address after placing an order?", "Address can be changed within 30 minutes of placing the order. After that, it cannot be changed as the order enters processing. For critical cases, contact support immediately and we will try to intercept with the courier, though this is not guaranteed.", "qa"),
    ("Q: What is ShopEasy Plus?", "ShopEasy Plus is our premium membership at ₹299/year or ₹49/month. Benefits include free delivery on all orders, early access to sales, exclusive member discounts, priority customer support, and free returns on all eligible products.", "qa"),

    ("7. Escalation & Complaints", None, "section"),
    ("Q: How do I escalate an unresolved issue?", "If your issue is not resolved within the promised timeline, you can escalate via: Live Chat > 'Escalate to Senior Agent', Email: escalation@shopeasy.in, or Call our senior support line at 1800-XXX-XXXX (Mon–Sat, 9AM–6PM). Escalated cases are resolved within 24 hours.", "qa"),
    ("Q: How do I file a formal complaint?", "For formal complaints, write to grievance@shopeasy.in with your order ID, issue description, and supporting documents. Our Grievance Officer will respond within 48 hours as per consumer protection regulations.", "qa"),
    ("Q: What if I want to report fraud or a scam?", "Report any fraud, phishing, or scam activity immediately to fraud@shopeasy.in or call our fraud hotline. Do not make any payments outside the ShopEasy platform. ShopEasy will never ask for your OTP, CVV, or net banking credentials.", "qa"),
]

def generate_pdf(output_path="data/shopeasy_support_kb.pdf"):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('title', parent=styles['Heading1'],
                                  fontSize=20, spaceAfter=20, textColor='#1a1a2e')
    section_style = ParagraphStyle('section', parent=styles['Heading2'],
                                    fontSize=14, spaceAfter=10, spaceBefore=20,
                                    textColor='#16213e')
    question_style = ParagraphStyle('question', parent=styles['Normal'],
                                     fontSize=11, spaceAfter=4, spaceBefore=10,
                                     fontName='Helvetica-Bold')
    answer_style = ParagraphStyle('answer', parent=styles['Normal'],
                                   fontSize=10, spaceAfter=8, leading=14,
                                   leftIndent=10)

    story = []
    for item in FAQ_CONTENT:
        if item[2] == "title":
            story.append(Paragraph(item[0], title_style))
            story.append(Paragraph("Version 1.0 | Customer Support Knowledge Base", styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
        elif item[2] == "section":
            story.append(Paragraph(item[0], section_style))
        elif item[2] == "qa":
            story.append(Paragraph(item[0], question_style))
            story.append(Paragraph(item[1], answer_style))

    doc.build(story)
    print(f"✅ PDF generated: {output_path}")

if __name__ == "__main__":
    generate_pdf()
