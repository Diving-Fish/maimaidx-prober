import math
import aiosmtplib
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
from email.header import Header
import time

def _format(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

async def send_mail(payload, mail_config):
    sender, to, subject = payload["sender"], payload["to"], payload["subject"]
    if "type" in payload:
        msg = MIMEText(payload["body"], payload["type"], 'utf-8')
    else:
        msg = MIMEText(payload["body"], 'plain', 'utf-8')
    msg['From'] = _format(f"{sender} <{mail_config['user']}>")
    msg['To'] = _format(f"{to} <{to}>")
    # currently, send mail will be forbidden when subject is same.
    # so we add time after subject to ensure sending successfully.
    msg['Subject'] = Header(subject + f"({time.strftime('%Y-%m-%d %H:%M:%S')})", 'utf-8').encode()
    try:
        st = time.time_ns()
        async with aiosmtplib.SMTP(
            hostname=mail_config['smtp_server'],
            port=465,
            use_tls=True
        ) as smtp:
            await smtp.login(mail_config['user'], mail_config['pwd'])
            await smtp.send_message(msg)
            print(f"Send email to {to} succeed ({math.floor((time.time_ns() - st) / 1e6)} ms)")
    except aiosmtplib.SMTPException as e:
        print("Send email to {to} failed: %s" % e)
