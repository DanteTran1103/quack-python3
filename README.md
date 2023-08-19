## Quack - Reuse modules

#### Problem
Currently, We dont have anything which helps us in reusing open source (especialy in git repositories) code. We see code - like it - clone it - copy file / folder and put it in our project and same code gets push in our repository, why? Why code redundancies?

#### Solution
Should be straightforward copy paste and put third party libraries in .gitignore - simple! And there shouldn't be any complexity needed to update libraries with the latest changes.

#### Quack Way
* Add third party repository to quack configuration yaml.
* Provide exact details (like an address) such as module / file path, hexsha, branch and tag.
* Run `quack` That's it!

### Features:
* Insert any module from any git repository, as a part of your project.
* Handle dependencies - execute nested quack modules.
* Multiple profiles to deal with different level of complexity.
* Works on UNIX (Mac OS X, Linux)

### Installation
##### 1) Install python3
Quack requires Python to run, follow [this guide](https://programwithus.com/learn/python/install-python3-mac) to install python3.

Note, if you already installed python3, you can skip this step.

##### 2) Build from this repo
This method will always include the latest features, but sometimes will not work at all. Oops!

Clone the repo, then use setup.py to install the package. Note, this process will differ only slightly in a non-bash shell.
```fish
$ git clone https://github.com/zonito/quack.git
$ cd quack
$ python3 setup.py install
```
Note, depending on your computer's settings, you may need to `sudo python3 setup.py install`.

### Examples:

##### Configurations
```yaml
name: Quack
description: Quack configuration
version: 0.0.6
gitignore: false

modules:
  pyanalytic:
    repository: https://github.com/zonito/PyAnalytics.git
    path: pyanalytics
    branch: dev
  subscribe:
    repository: https://github.com/zonito/subscribe.git
    hexsha: 9e3e9642cfea36f4ae216d27df100134920143b9
  toggleicon:
    repository: https://github.com/zonito/z-toggleicon.git
    tag: v1.0

profiles:
  init:
    tasks: ['modules',
            'quack:pyanalytic/build.yaml:update',
            'cmd:pwd']
  update:
    tasks: ['modules:subscribe']
    dependencies:
      quack: 'pyanalytic/build.yaml:update'
  clean:
    tasks: ['-modules']
```

##### Adding quack plugins to your project

Once you have quack installed, adding quack plugins to your project is done with the quack.yaml configuration file.

Add a file called quack.yaml to the root of your project. The pre-commit config file describes:

| properties      | Details                                                         |
|-----------------|-----------------------------------------------------------------|
| **name**        | Project name                                                    |
| **description** | Project description (Optional)                                  |
| **version**     | Project version (Optional)                                      |
| **gitignore**   | Update git ignore for sub module included (Optional, default: true)  |
| **modules**     | Declared modules used within your project. <ul><li>`folder name`:</li><ul><li>`repository`: Git repository url.</li><li>`path`: module path within given git repository</li><li>`branch`: provide branch name to checkout from git repository.</li><li>`hexsha`: Provide sha1 key to checkout till specific commits</li><li>`tag`: Provide tag to checkout till specific release tag</li><li>`isfile`: Copy file instead of creating folder.</li></ul>|
| **profiles**    | List of profiles for keep things separate for different stuffs. <ul><li> `task_name`: Default task (`init` task mandatory) </li> <ul><li>`tasks`: List of tasks or execute nested quack. </li><li>`dependencies`: List of dependencies before executing tasks</li><ul><li>`quack`: Nested quack. (Syntax: `module/quack_config.yaml:profile_name`)</li></ul></ul></ul>|

##### Command
```
$ quack
```
Above command will look for `quack.yaml` file or create, if not found, and execute `init` profile's instructions as a default profile.

```
$ quack -y quack.yaml -p update
```
You can provide your custom `yaml` file (such as `build.yaml`). Above command will execute given `update` profile within `build.yaml` configuration file.

##### Command line arguments

* `-h`, `--help`: version splash page // usage
* `-p`: `--profile`: Run specific profile. `default: init`
* `-y`: `--yaml`: Provide custom yaml. `default: quack.yaml`
