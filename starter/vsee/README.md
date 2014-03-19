vsee
=====
Veil Sample Application

###Steps

1.cd ~/Projects

2.veil/bin/veil scaffold

3.cd vsee

4.git remote add origin git@github.com:honovation/vsee.git && git push -u origin master

6.veil init

7.update .vsee.cfg

8.sudo veil install-server --upgrade-mode=latest

9.sudo veil :test install-server --upgrade-mode=latest

10.sudo veil up

11.veil backend database postgresql reset vsee

12.open browser and access: http://person.dev.dmright.com:8070/

###PyCharm Setting

1.Code Style => General: Right margin 150

2.Code Style => Python => Wrapping and Braces: untick all "Align when multiline"
