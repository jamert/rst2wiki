from distutils.core import setup
import distutils.command.install_scripts
import distutils.command.install_data
import os
import shutil


PACKAGE = "rst2wiki"


install_requires = [
    'requests==2.6.0',
    'docutils==0.12',
    'Pygments==2.0.2',
    'rst2confluence==0.5.1',
]


scripts_dir = "bin"
script_files = ['rst2wiki']
scripts = list()

for b in script_files:
    scripts.append(os.path.join(scripts_dir, b) + ".py")


def get_data_files():
    data_dir = 'share'
    dest_dir = os.path.join('share', PACKAGE)
    accum = list()

    def deep(dir_):
        real_dir = os.path.join(data_dir, dir_)
        files = list()
        if not os.path.isdir(real_dir):
            return
        for f in os.listdir(real_dir):
            fname = os.path.join(real_dir, f)
            if os.path.isfile(fname):
                files.append(fname)
            else:
                deep(os.path.join(dir_, f))
        if files:
            accum.append((os.path.join(dest_dir, dir_), files))

    deep('')
    return accum


class strip_dot_py(distutils.command.install_scripts.install_scripts):
    def run(self):
        distutils.command.install_scripts.install_scripts.run(self)
        outfiles = self.get_outputs()
        for i, script in enumerate(outfiles):
            if script.endswith(".py"):
                newname = script[:-3]
                shutil.move(script, newname)
                outfiles[i] = newname


def run_setup():
    setup(name=PACKAGE,
          version='0.1.0',
          description='Tool to push reST docs to confluence',
          author='Artem Dayneko',
          author_email='a.dayneko@ngenix.net',
          url='http://www.ngenix.net',
          scripts=scripts,
          install_requires=install_requires,
          cmdclass={"install_scripts": strip_dot_py},
          data_files=get_data_files(),
          )

if __name__ == '__main__':
    run_setup()
