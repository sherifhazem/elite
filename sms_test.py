from TaqnyatSms import client as TaqnyatClient

# البيانات الخاصة بك
BEARER_TOKEN = '78fadbffb8d0f05434c0189f6d9cbf9f'
SENDER_NAME = 'HENTAUTO' # لا يمكن تغير هذا الاسم لانه هو الاسم المصرح له من taqnyat بارسال الرسائل

# رقم الجوال بالصيغة الدولية والرسالة
recipient = "966597988313"
message_body = "مرحبا بك , هذه الرساله للتجريه ELITE"

def test_sms_send():
    # 1. تهيئة العميل
    # تم تغيير Client إلى TaqnyatClient (التي تشير إلى الكلاس client في مكتبة TaqnyatSms)
    sms_client = TaqnyatClient(BEARER_TOKEN)
    
    # 2. محاولة الإرسال
    # يتم وضع الرقم داخل قائمة [] حتى لو كان رقماً واحداً
    print(f"جاري محاولة الإرسال إلى {recipient}...")
    
    try:
        # تتطلب الدالة 4 معاملات: الجسم، المستلمون، المرسل، والجدولة (scheduled)
        # نضع None للجدولة إذا كنا نريد الإرسال الفوري
        response = sms_client.sendMsg(message_body, [recipient], SENDER_NAME, None)
        print("-" * 30)
        print("النتيجة من سيرفر تقنيات:")
        print(response)
        print("-" * 30)
    except Exception as e:
        print(f"حدث خطأ أثناء الإرسال: {e}")

if __name__ == "__main__":
    test_sms_send()
