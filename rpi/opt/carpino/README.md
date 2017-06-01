--------------------------------
* BMW e87 CarPC Project
--------------------------------
 Small project to integrate OrangePi PC and Arduino Uno (With SparkFun CAN Bus Shield)
 with an BMW e87's K-CAN Bus. (100kbps can bus)


--------------------------------
* Changelog
--------------------------------
* 30.05.2017
 ** [Improvment] - Refresh the UI...make it more blink blink
 ** [Fix] - Number of small fixes

* 10.05.2017
 ** [Improvment] - Rewrite of big parts of the code

* 16.03.2017
 ** [New] - Player control from the interface added

* 15.03.2017
 ** [Fix] - Periodicly send ping command inside the mpd connection to avoid connection drops.
 ** [Improvment] - Renaming temp_thread function to status_thread.



--------------------------------
* Deps
--------------------------------
 - python-mpd
 - python-tornado
 - python-websocket-client
