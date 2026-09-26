import hashlib, hmac, json

def test_razorpay_webhook_signature(monkeypatch):
    from app.services import payment
    monkeypatch.setattr(payment.settings, 'payment_provider', 'razorpay')
    monkeypatch.setattr(payment.settings, 'razorpay_webhook_secret', 'test-webhook-secret')
    body=b'{"event":"payment.captured"}'
    signature=hmac.new(b'test-webhook-secret', body, hashlib.sha256).hexdigest()
    assert payment.verify_webhook(body, signature) is True
    assert payment.verify_webhook(body, 'bad') is False

def test_local_webhook_bypasses_provider_signature(monkeypatch):
    from app.services import payment
    monkeypatch.setattr(payment.settings, 'payment_provider', 'local')
    monkeypatch.setattr(payment.settings, 'razorpay_webhook_secret', '')
    assert payment.verify_webhook(b'{}', '') is True


def test_twilio_verify_delivery_contract(monkeypatch):
    from app.services import otp
    from app.config import settings
    class Resp:
        status_code = 201
        text = ""
    calls = {}
    def fake_post(url, data, auth, timeout):
        calls.update(url=url, data=data, auth=auth, timeout=timeout)
        return Resp()
    monkeypatch.setattr(settings, 'sms_provider', 'twilio')
    monkeypatch.setattr(settings, 'twilio_account_sid', 'AC_test')
    monkeypatch.setattr(settings, 'twilio_auth_token', 'token')
    monkeypatch.setattr(settings, 'twilio_verify_service_sid', 'VA_test')
    monkeypatch.setattr(otp.httpx, 'post', fake_post)
    assert otp._send_twilio_verify('+919999999999') == 'twilio_verify'
    assert calls['data']['To'] == '+919999999999'
    assert calls['data']['Channel'] == 'sms'


def test_smtp_delivery_contract(monkeypatch):
    from app.services import otp
    from app.config import settings
    class FakeSMTP:
        def __init__(self, host, port, timeout):
            self.host, self.port, self.timeout = host, port, timeout
            self.sent = False
        def __enter__(self): return self
        def __exit__(self, *exc): return False
        def starttls(self): pass
        def login(self, user, password): pass
        def send_message(self, message):
            self.sent = True
            assert message['To'] == 'student@example.edu'
            assert 'CampusCart' in message['Subject']
    monkeypatch.setattr(settings, 'smtp_host', 'smtp.example.test')
    monkeypatch.setattr(settings, 'smtp_from', 'noreply@example.test')
    monkeypatch.setattr(otp.smtplib, 'SMTP', FakeSMTP)
    assert otp._send_email('student@example.edu', 'code') == 'smtp'
