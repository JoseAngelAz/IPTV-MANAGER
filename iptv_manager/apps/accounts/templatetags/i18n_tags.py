from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def tr(context, text):
    tr_dict = context.get('tr', {})
    if not tr_dict or not text:
        return text or ''
    key = (text.strip().lower()
           .replace(' ', '_')
           .replace('á', 'a').replace('é', 'e')
           .replace('í', 'i').replace('ó', 'o')
           .replace('ú', 'u').replace('ñ', 'n')
           .replace('¿', '').replace('?', '')
           .replace('¡', '').replace('!', '')
           .replace(':', '').replace(',', '')
           .replace('.', '').replace('(', '')
           .replace(')', '').replace('"', '')
           .replace("'", ''))
    return tr_dict.get(key, text)
