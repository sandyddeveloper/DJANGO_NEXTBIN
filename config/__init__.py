# Config app init
import django.utils.encoding
django.utils.encoding.smart_text = django.utils.encoding.smart_str
django.utils.encoding.force_text = django.utils.encoding.force_str

import django.utils.translation
django.utils.translation.ugettext = django.utils.translation.gettext
django.utils.translation.ugettext_lazy = django.utils.translation.gettext_lazy
