vsee
=====
Veil Sample Application

###Steps

1.cd ~/Projects

2.veil/bin/veil scaffold

3.cd vsee

4.update .vsee.cfg and src.__veil__.CODEBASE with your own

5.git remote add origin git@github.com:honovation/vsee.git && git push -u origin master

6.veil init

7.sudo veil install-server --upgrade-mode=latest

8.sudo veil :test install-server --upgrade-mode=latest

9.sudo veil up

10.veil backend database postgresql reset vsee

11.open browser and access: http://person.dev.dmright.com:8070/

###PyCharm Setting

1.Code Style => General: Right margin 150

2.Code Style => Python => Wrapping and Braces: untick all "Align when multiline"
