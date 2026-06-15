from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Context, Template
from django.template.loader import get_template
from django.utils.encoding import smart_str
from django.utils.safestring import SafeText
from django.conf import settings


def get_email_template(header, data):
    email_template_file = open(
        str(settings.EMAIL_TEMPLATE) + "/" + header["template_name"] + ".txt", "r", encoding="cp437", errors='ignore')

    body_template_html = Template(email_template_file.read())
    context_data = Context(data)
    body_template_html = body_template_html.render(context_data)
    content = smart_str(body_template_html)
    html=get_template('base.html').render({'EMAIL_MESSAGE_HTML': content})
    html_stripped = ' '.join(str(smart_str(html)).split())
    html = SafeText(html_stripped)
    return html


def send_email(header, body_var):
    """
    :param header:
    :param body_var:
    :return:
    """
    template = get_email_template(header, body_var)
    if header.get('reply-to'):
        headers_data={'Reply-To': header.get('reply-to', [])}
    else:
        headers_data=header.get('reply-to', [])
    try:
        msg = EmailMessage(
            settings.EMAIL_HEADER.format(header["subject"]),
            template,
            from_email=settings.FROM_EMAIL,
            to=header["to"],
            cc=header.get('cc', []),
            bcc=[],
            headers=headers_data
            
        )
        if header.get("file_path", None):
            for path in header["file_path"]:
                msg.attach_file(path)
        msg.content_subtype = 'html'
        msg.send()

    except Exception:
        pass
