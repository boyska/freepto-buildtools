from fabric.api import *
from fabric.decorators import runs_once
from fabtools import require, deb, service
#from fabric.contrib.files import append, exists
#from fabric.colors import green
PROXY='localhost:3142'

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
    #TODO: gitconfig
    deb.install(['build-essential', 'git'])
    require.file('/etc/gitconfig', source='files/gitconfig', use_sudo=True)


@runs_once
def livebuild():
    pkg('openssh-server live-build python git-core apt-cacher-ng zsh',
        'debootstrap')
    run('update-rc.d apt-cacher-ng defaults')
    service.start('apt-cacher-ng')
    require.directory('/var/build/')
    require.fild('/etc/profile.d/proxy.sh',
                 contents='export http_proxy="http://%s/"' % PROXY,
                 owner='root', group='root', mode='644')
    require.file('/usr/local/bin/manualbuild.sh',
                 source='files/bin/manualbuild.sh', owner='root', group='root',
                 mode='755')


@runs_once
def webserver():
    pkg('nginx-light')
    #TODO: configure nginx to serve builds


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


#### TASKS

@task
def base():
    keyrings()
    devel()
    livebuild()


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
