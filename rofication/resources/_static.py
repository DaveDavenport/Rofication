from .._util import Resource

value_font = Resource(env_name='font', xres_name='i3xrocks.value.font', default='Source Code Pro Medium 13')

notify_none = Resource(env_name='i3xrocks_label_notify_none', xres_name='i3xrocks.label.notify.none', default='N')
notify_some = Resource(env_name='i3xrocks_label_notify_some', xres_name='i3xrocks.label.notify.some', default='N')
notify_error = Resource(env_name='i3xrocks_label_notify_error', xres_name='i3xrocks.label.notify.error', default='N')

value_color = Resource(env_name='color', xres_name='i3xrocks.value.color', default='#D8DEE9')
label_color = Resource(env_name='label_color', xres_name='i3xrocks.label.color', default='#7B8394')
nominal_color = Resource(env_name='background_color', xres_name='i3xrocks.nominal', default='#D8DEE9')
critical_color = Resource(xres_name='i3xrocks.critical.color', default='#BF616A')
