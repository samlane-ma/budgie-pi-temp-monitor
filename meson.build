project(
  'budgie-pi-temp-monitor',
  version: '0.0.1-dev',
  license: 'GPL3+',
  meson_version: '>= 0.40.0'
)


application_id = 'budgie-pi-temp-monitor'

prefix = get_option('prefix')
libdir = join_paths(prefix, get_option('libdir'))
datadir = join_paths(prefix, get_option('datadir'))

PIXMAPS_DIR = join_paths(datadir, 'pixmaps')

subdir('src')
subdir('icons')

install_data('schema/com.github.samlane-ma.budgie-pi-temp-monitor.gschema.xml',
    install_dir: '/usr/share/glib-2.0/schemas'
)

meson.add_install_script('meson_post_install')
