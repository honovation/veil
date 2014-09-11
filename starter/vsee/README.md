vsee
=====
Veil Sample Application

###Steps

1.`cd ~/Projects`

2.`veil/bin/veil scaffold vsee`

3.`cd vsee`

4.`update .config and src.__veil__.CODEBASE with your own`

5.`git remote add origin git@github.com:honovation/vsee.git && git push -u origin master`

6.`../veil/bin/veil init`

7.`sudo veil :test install-server --upgrade`

8.`sudo veil install-server`

9.`sudo veil up`

10.`veil backend database postgresql reset vsee`

11.open browser and access(you should add this example domain to your hosts file and make it point to 127.0.0.1): http://person.dev.dmright.com:2000/

###PyCharm Setting

1.Code Style => General: Right margin 150

2.Code Style => Python => Wrapping and Braces: un-tick all "Align when multiline"

###Notes
1.component中所有的module的外部依赖必须通过INSTALLER安装，这样能确保在import这些module时外部依赖已经安装；

2.`__init__.py`中不能访问resource的配置（如调用：get_website_parent_domain），因为在安装过程中import module时会执行`__init__.py`，而这时resource的配置还没有生成；

3.定义veil系统环境的`__env__`脚本中，不能引用需要安装外部依赖的veil component, 比如veil.utility.clock。因为，安装过程首先需要import `__env__`脚本，此时`__env__`脚本引用的veil component因为其外部依赖还没有安装会import失败。
