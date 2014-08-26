import os
import base64

from fabric.api import *
from fabric.colors import green
from fabric.decorators import runs_once
from fabric.context_managers import settings
from fabtools import require, deb, service
from fabtools.utils import run_as_root
from cuisine import file_exists, file_read, text_ensure_line, shell_safe
# from fabric.contrib.files import append, exists
# from fabric.colors import green

import iputils
if os.path.exists('conf.py'):
    import conf

# UTILITIES


def pkg(*args):
    """
    Package installation
    """
    l = []
    for p in args:
        if ' ' in p:
            l.extend(p.split())
        else:
            l.append(p)
    require.deb.packages(l)


@runs_once
def keyrings():
    """
    Refresh apt keys
    """
    deb.install(['debian-keyring', 'debian-archive-keyring'],
                options=["-y", "--force-yes"])
    sudo('apt-key update')


@runs_once
def devel():
    """
    Developer tools installation
    """
    # TODO: gitconfig
    deb.install(['build-essential', 'git'])
    require.file('/etc/gitconfig', source='files/gitconfig', use_sudo=True)


@runs_once
def aptcacher():
    pkg('apt-cacher-ng')
    run_as_root('update-rc.d apt-cacher-ng defaults')
    service.start('apt-cacher-ng')


@runs_once
def livebuild(proxy):
    print green("Livebuild with " + proxy)

    pkg('openssh-server live-build python git-core zsh',
        'debootstrap')
    require.directory('/var/build/')
    mount_line('tmpfs /var/tmp tmpfs defaults 0 0')
    run_as_root('cat /etc/fstab')
    require.file('/etc/http_proxy', contents="http://%s/" % proxy,
                 owner='root', group='root', mode='644',
                 verify_remote=True, use_sudo=True)
    require.file('/etc/profile.d/proxy.sh',
                 contents='export http_proxy="http://%s/"' % proxy,
                 owner='root', group='root', mode='644',
                 verify_remote=True, use_sudo=True)

    require.file('/usr/local/bin/manualbuild.sh',
                 source='files/bin/manualbuild.sh', owner='root', group='root',
                 mode='755',
                 verify_remote=True, use_sudo=True)
    require.file('/usr/local/bin/gitbuild.sh',
                 source='files/bin/gitbuild.sh', owner='root', group='root',
                 mode='755',
                 verify_remote=True, use_sudo=True)
    require.file('/etc/cron.daily/cacherepo',
                 source='files/bin/cron_cacherepo', owner='root', group='root',
                 mode='755',
                 verify_remote=True, use_sudo=True)


@runs_once
def webserver():
    pkg('nginx-light')
    require.file('/etc/nginx/sites-enabled/default',
                 source='files/nginx', owner='root', group='root',
                 mode='644', use_sudo=True)


@runs_once
def doc():
    pkg('live-boot-doc live-config-doc')
    # pkg('live-manual-txt')


def auto_build(url, repository, branch='master'):
    '''
    this should start a build "reacting" to a github webhook
    '''
    pass


@runs_once
def sys_utils():
    """
    Sysadmin tools installation
    """
    pkg('zsh', 'psmisc', 'psutils', 'vim', 'less', 'most', 'screen', 'lsof',
        'htop', 'strace', 'ltrace')
    # TODO: screenrc (escape!)
    require.file('/etc/vim/vimrc.local',
                 contents="syntax enable\nset modeline si ai ic scs bg=dark\n",
                 owner='root', group='root', use_sudo=True)
    require.file('/etc/zsh/zshrc', source='files/shell/zshrc', owner='root',
                 group='root', use_sudo=True)
    require.file('/etc/zsh/zshrc.local', source='files/shell/zshrc.local',
                 owner='root', group='root', use_sudo=True)
    require.user('root', shell='/usr/bin/zsh')


def net_utils():
    """
    Networking tools installation
    """
    pkg('nethogs', 'bwm-ng', 'iptables', 'iptables-persistent', 'curl',
        'dnsutils', 'vnstat', 'iptraf', 'iotop')


# TASKS

@task
def base(proxy='127.0.0.1:3142'):
    with settings(use_sudo=True):
        require.file("/etc/apt/apt.conf",
                     contents='Acquire::http { Proxy "http://%s"; };' % proxy,
                     use_sudo=True)
        keyrings()
        devel()
        if iputils.is_my_ip(proxy.split(':')[0]):
            aptcacher()
        livebuild(proxy)


@task
def update():
    with settings(use_sudo=True):
        deb.update_index()


@task
def fulloptional():
    with settings(use_sudo=True):
        sys_utils()
        net_utils()
        doc()
        webserver()


def file_update(location, updater=lambda x: x, use_sudo=False):
    """
    Updates the content of the given by passing the existing
    content of the remote file at the given location to the 'updater'
    function. Return true if file content was changed.
    """
    assert file_exists(location), "File does not exists: " + location
    old_content = file_read(location)
    new_content = updater(old_content)
    if (old_content == new_content):
        return False
    runner = run_as_root if env.use_sudo or use_sudo else run
    runner('echo "%s" | openssl base64 -A -d -out %s' %
           (base64.b64encode(new_content), shell_safe(location)))
    return True


def mount_line(line):
    if file_update('/etc/fstab', lambda _: text_ensure_line(_, line)):
        run_as_root('mount -a')


@task
def qemu(central='127.0.0.1'):
    if iputils.is_my_ip(central):
        pkg('libvirt0 qemu-kvm')
    else:
        pkg('nfs-common')
        mount_line('%s:/var/lib/libvirt/images /var/www nfs defaults 0 0' %
                   central)
