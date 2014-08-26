==============================================================
online-testing 
==============================================================

-----------------------------------------------
test freepto images without downloading
-----------------------------------------------

:Author: boyska <piuttosto@logorroici.org>
:Date: 2014
:Manual section: 7
:Manual group: live-build

Abstract
=====================

Sometimes, the test to run is very simple. Downloading the image with a
domestic connection can require lot of time. The main idea is to execute the
virtual machine on a remote server, and control it using VNC.

Not every test can be run this way: some tests require bare metal; some other
require particular vm configurations that are not possible in this way

Setup
=====================

::

  apt-get install qemu-kvm

``freepto-buildtools`` contains a script called ``emu-vnc`` which is all you
need to have.

Also, make sure that users that need to run the script are part of the ``kvm``
group::

  gpasswd -a USERNAME kvm``

Usage examples
=====================

On the server, run::

  emu-vnc my.img

On your computer, run::

  vncviewer -quality 1 -depth 8 -owncmap -via friggipizza localhost

See Also
========

``emu-vnc(1)``, ``xtightvncviewer(1)``, ``kvm(1)``
