import os

from docutils.core import publish_string

from fabric.api import env
from fabtools import require
from fabtools.utils import run_as_root


def rst2man(fname):
    with open(fname) as buf:
        return publish_string(buf.read(), writer_name='manpage')


def require_man(section, name, use_sudo=False, update_mandb=True):
    if 'use_sudo' in env and env.use_sudo:
        use_sudo = True
    assert type(section) is int
    fname = os.path.join('files', 'man', 'man%d' % section, name + '.rst')
    if not os.path.exists(fname):
        raise ValueError('Manpage %s(%d) does not exist in "%s"' %
                         (name, section, fname))

    require.directory('/usr/local/share/man/man%d' % section,
                      use_sudo=use_sudo)
    require.file('/usr/local/share/man/man%d/%s.%d' % (section, name, section),
                 contents=rst2man(fname), use_sudo=use_sudo)
    if update_mandb:
        mandb()


def mandb():
    run_as_root('mandb')
