.. rst2wiki

    :page: 10814244
    :ancestor: 1147842
    :title: Python + OBS (типа веселье)


Сборка python-based deb-пакета под OBS
======================================

В качестве источников информации для этого документа использовались
`OBS Wiki <https://en.opensuse.org/openSUSE:Build_Service_Debian_builds>`_
и `рандомный блог <https://labs.spotify.com/2013/10/10/packaging-in-your-packaging-dh-virtualenv/>`_.

На примере пакета ``ncdn-stat`` будет показано, как сделать с нуля
python-based debian-пакет.

1. Делаем новый репозиторий для нашего пакета в нужном проекте::

     osc checkout beastie
     cd beastie
     osc mkpac ncdn-stat

2. Создаем новые файлы::

     cp ~/code/ncdn-stat/dist/ncdn-stat-0.5.0.tag.gz
     touch debian.control debian.rules debian.compat debian.changelog
     touch ncdn-stat.dsc

3. Содержимое debian.control. Внимательно заполнять Source, Package,
   Build-Depends (зависимости для сборки, в примере представлен минимальный набор),
   Depends (зависимости для исполнения)::

     Source: ncdn-stat
     Section: misc
     Priority: optional
     Maintainer: Artem Dayneko <a.dayneko@ngenix.net>
     Build-Depends: debhelper (>= 7.0.50~), python2.7 (>= 2.7.6), python-pip, python-virtualenv, dh-virtualenv

     Package: ncdn-stat
     Architecture: any
     Depends: ${misc:Depends}, python2.7
     Description: Helpers for collecting statistics from counters.

4. Содержимое debian.rules. Предполагается, что файл будет идентичен для всех
   deb-пакетов одного типа (python, ruby, etc.). Внимательнее с отступами - это Makefile,
   так что отступы делаются табами, а не пробелами::

     #!/usr/bin/make -f
     export DH_VIRTUALENV_INSTALL_ROOT=/opt

     %:
       dh $@ --with python-virtualenv

5. debian.changelog имеет весьма специфический (и строгий) формат.
   Обратите внимание на версию (-1)::

     ncdn-stat (0.5.0-1) trusty; urgency=low

       * Initial release

      -- Artem Dayneko <a.dayneko@ngenix.net>  Thu, 23 Apr 2015 19:47:49 +0300

6. debian.compat - везде одинаковый.::

     5

7. ncdn-stat.dsc почти повторяет по содержимому debian.control.
   Обратите внимание на Files - хэши и размеры (первые два поля)
   не обязательно должны быть верными (они заполнятся потом):::

     Format: 1.0
     Source: ncdn-stat
     Binary: ncdn-stat
     Architecture: any
     Version: 0.5.0-1
     Maintainer: Artem Dayneko <a.dayneko@ngenix.net>
     Build-Depends: debhelper (>= 7.0.50~), python2.7 (>= 2.7.6), python-pip, python-virtualenv, dh-virtualenv
     Package-List:
      ncdn-stat deb misc optional arch=any
     Files:
      3834f6429169e943871eeb4d81ee5f2a 30169 ncdn-stat-0.5.0.orig.tar.gz
      3834f6429169e943871eeb4d81ee5f2a 30169 ncdn-stat-0.5.0.diff.tar.gz

8. Если у пакета есть python-зависимости (а они есть почти всегда), то внутри архива
   дожен находиться файл ``requirements.txt`` в формате, соответствующем выводу
   команды ``pip freeze``. Пока что я не могу предложить ничего, кроме запихивания
   этого файла внуть архива руками. Его содержимое можно прочитать в поле
   ``install_requires`` в ``setup.py``. Пример:::

     futures==2.1.6
     gevent==1.0.1
     greenlet==0.4.5
     haigha==0.7.2
