import os

from fabric.api import *
from fabric.colors import green, red, blue
from fabric.decorators import runs_once
from fabtools import require, deb, service
from cuisine import file_update, text_ensure_line
#from fabric.contrib.files import append, exists
#from fabric.colors import green

import iputils
if os.path.exists('conf.py'):
    import conf

### UTILITIES


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
    run('update-rc.d apt-cacher-ng defaults')
    service.start('apt-cacher-ng')


@runs_once
def livebuild(proxy):
    print green("Livebuild with " + proxy)
    pkg('openssh-server live-build python git-core zsh',
        'debootstrap')
    require.directory('/var/build/')
    require.file('/etc/http_proxy', contents="http://%s/" % proxy,
                 owner='root', group='root', mode='644',
                 verify_remote=True)
    require.file('/etc/profile.d/proxy.sh',
                 contents='export http_proxy="http://%s/"' % proxy,
                 owner='root', group='root', mode='644',
                 verify_remote=True)
    require.file('/usr/local/bin/manualbuild.sh',
                 source='files/bin/manualbuild.sh', owner='root', group='root',
                 mode='755',
                 verify_remote=True)


@runs_once
def webserver():
    pkg('nginx-light')
    require.file('/etc/nginx/sites-enabled/default',
                 source='files/nginx', owner='root', group='root',
                 mode='644')


@runs_once
def doc():
    pkg('live-boot-doc live-config-doc')
    #pkg('live-manual-txt')


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
                 "syntax enable\nset modeline si ai ic scs bg=dark\n",
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
    require.file("/etc/apt/apt.conf",
                 contents='Acquire::http { Proxy "http://%s"; };' % proxy)
    keyrings()
    devel()
    if iputils.is_my_ip(proxy.split(':')[0]):
        aptcacher()
    livebuild(proxy)


@task
def update():
    deb.update_index()


@task
def fulloptional():
    base()
    sys_utils()
    net_utils()
    doc()
    webserver()


@task
def qemu(central='127.0.0.1'):
    if iputils.is_my_ip(central):
        pkg('libvirt0 qemu-kvm')
    else:
        pkg('nfs-common')
        # TODO: aggiungere questa riga a fstab
        mount_line = '%s:/var/lib/libvirt/images /var/www nfs defaults 0 0' % \
            central
        if file_update('/etc/fstab',
                       lambda _: text_ensure_line(_, mount_line)):
            run('mount -a')

