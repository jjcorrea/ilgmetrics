from django import template

register = template.Library()

#
# TAGS
#

@register.simple_tag(name="eval")
def do_eval(token):
    #print token
    return str(token)