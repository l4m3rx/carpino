#!/bin/sh
#
# rc.M		This file is executed by init(8) when the system is being
#		initialized for one of the "multi user" run levels (i.e.
#		levels 1 through 6).  It usually does mounting of file
#		systems et al.
#
# Version:	@(#)/etc/rc.d/rc.M	2.23	Wed Feb 26 19:20:58 PST 2003
#
# Author:	Fred N. van Kempen, <waltje@uwalt.nl.mugnet.org>
#		Heavily modified by Patrick Volkerding <volkerdi@slackware.com>
#

# Tell the viewers what's going to happen.
echo "Going multiuser..."

# Update all the shared library links:
#if [ -x /sbin/ldconfig ]; then
  echo "Updating shared library links:  /sbin/ldconfig &"
  /sbin/ldconfig &
#fi

# Screen blanks after 15 minutes idle time, and powers down in one hour
# if the kernel supports APM or ACPI power management:
#/bin/setterm -blank 15 -powersave powerdown -powerdown 60

# OPi Custom settings
if [ -x /etc/rc.d/rc.opi ]; then
  /etc/rc.d/rc.opi
fi

# Set the hostname.
/bin/hostname dopi

# Set the permissions on /var/log/dmesg according to whether the kernel
# permits non-root users to access kernel dmesg information:
touch /var/log/dmesg
chmod 640 /var/log/dmesg

# Save the contents of 'dmesg':
/bin/dmesg -s 65536 > /var/log/dmesg

# Start the system logger.
if [ -x /etc/rc.d/rc.syslog -a -x /usr/sbin/syslogd -a -d /var/log ]; then
  . /etc/rc.d/rc.syslog start
fi

# Update the X font indexes:
#if [ -x /usr/bin/fc-cache ]; then
#  # Prevent error when the system time is not correct (happens on ARM Versatile)
#  find /usr/share/fonts -type d -print0 | xargs -0 touch
#  echo "Updating X font indexes:  /usr/bin/fc-cache -f &"
#  /usr/bin/fc-cache -f &
#fi

# Run rc.udev again.  This will start udev if it is not already running
# (for example, upon return from runlevel 1), otherwise it will trigger it
# to look for device changes and to generate persistent rules if needed.
if grep -wq sysfs /proc/mounts && grep -q devtmpfs /proc/filesystems ; then
  if ! grep -wq nohotplug /proc/cmdline ; then
    if [ -x /etc/rc.d/rc.udev ]; then
      /bin/sh /etc/rc.d/rc.udev start
    fi
  fi
fi

# Initialize the networking hardware.
if [ -x /etc/rc.d/rc.inet1 ]; then
  . /etc/rc.d/rc.inet1
fi

# Hostapd
if [ -x /etc/rc.d/rc.hostapd ]; then
  . /etc/rc.d/rc.hostapd start
fi
# Start D-Bus:
if [ -x /etc/rc.d/rc.messagebus ]; then
  sh /etc/rc.d/rc.messagebus start
fi

# Start Bluetooth:
if [ -x /etc/rc.d/rc.bluetooth ]; then
  sh /etc/rc.d/rc.bluetooth start
fi

# Start networking daemons:
if [ -x /etc/rc.d/rc.inet2 ]; then
  . /etc/rc.d/rc.inet2
fi

# Mount any additional filesystem types that haven't already been mounted:
mount -a -v 2> /dev/null | grep -v -e "already mounted" -e "ignored" | cut -f 1 -d : | tr -d ' ' | while read dev ; do mount | grep "${dev} " ; done

# Remove stale locks and junk files (must be done after mount -a!)
/bin/rm -f /var/lock/* /var/spool/uucp/LCK..* /tmp/.X*lock /tmp/core /core 2> /dev/null
/bin/rm -rf /var/spool/cron/cron.?????? 2> /dev/null

# Remove stale hunt sockets so the game can start.
if [ -r /tmp/hunt -o -r /tmp/hunt.stats ]; then
  echo "Removing your stale hunt sockets from /tmp."
  /bin/rm -f /tmp/hunt*
fi

# Ensure basic filesystem permissions sanity.
chmod 755 / 2> /dev/null
chmod 1777 /tmp /var/tmp

# Enable CPU frequency scaling:
if [ -x /etc/rc.d/rc.cpufreq ]; then
  . /etc/rc.d/rc.cpufreq start
fi

# Update any existing icon cache files:
#if find /usr/share/icons -maxdepth 2 2> /dev/null | grep -q icon-theme.cache ; then
#  for theme_dir in /usr/share/icons/* ; do
#    if [ -r ${theme_dir}/icon-theme.cache ]; then
#      echo "Updating icon-theme.cache in ${theme_dir}..."
#      /usr/bin/gtk-update-icon-cache -t -f ${theme_dir} 1> /dev/null 2> /dev/null &
#    fi
#  done
  # This would be a large file and probably shouldn't be there.
#  if [ -r /usr/share/icons/icon-theme.cache ]; then
#    echo "Deleting icon-theme.cache in /usr/share/icons..."
    #/usr/bin/gtk-update-icon-cache -t -f /usr/share/icons 1> /dev/null 2> /dev/null &
#    rm -f /usr/share/icons/icon-theme.cache
#  fi
#fi

# Update mime database:
#if [ -x /usr/bin/update-mime-database -a -d /usr/share/mime ]; then
#  echo "Updating MIME database:  /usr/bin/update-mime-database /usr/share/mime &"
#  /usr/bin/update-mime-database /usr/share/mime 1> /dev/null 2> /dev/null &
#fi

# Start console-kit-daemon:
if [ -x /etc/rc.d/rc.consolekit ]; then
  sh /etc/rc.d/rc.consolekit start
fi

# Start HAL:
if [ -x /etc/rc.d/rc.hald ]; then
  sh /etc/rc.d/rc.hald start
fi

# Start system-wide PulseAudio daemon (not recommended, nor required in
# order to use PulseAudio -- see the script for details):
if [ -x /etc/rc.d/rc.pulseaudio ]; then
  . /etc/rc.d/rc.pulseaudio start
fi

# These GTK+/pango files need to be kept up to date for
# proper input method, pixbuf loaders, and font support.
#if [ -x /usr/bin/update-gtk-immodules ]; then
#  echo "Updating gtk.immodules:"
#  echo "  /usr/bin/update-gtk-immodules &"
#  /usr/bin/update-gtk-immodules > /dev/null 2>&1 &
#fi
#if [ -x /usr/bin/update-gdk-pixbuf-loaders ]; then
#  echo "Updating gdk-pixbuf.loaders:"
#  echo "  /usr/bin/update-gdk-pixbuf-loaders &"
#  /usr/bin/update-gdk-pixbuf-loaders > /dev/null 2>&1 &
#fi
#if [ -x /usr/bin/update-pango-querymodules ]; then
#  echo "Updating pango.modules:"
#  echo "  /usr/bin/update-pango-querymodules &"
#  /usr/bin/update-pango-querymodules > /dev/null 2>&1 &
#fi
#if [ -x /usr/bin/glib-compile-schemas ]; then
#  echo "Compiling GSettings XML schema files:"
#  echo "  /usr/bin/glib-compile-schemas /usr/share/glib-2.0/schemas &"
#  /usr/bin/glib-compile-schemas /usr/share/glib-2.0/schemas >/dev/null 2>&1 &
#fi

# Start dnsmasq, a simple DHCP/DNS server:
if [ -x /etc/rc.d/rc.dnsmasq ]; then
  /etc/rc.d/rc.dnsmasq start
fi

# Start snmpd:
#if [ -x /etc/rc.d/rc.snmpd ]; then
#  /etc/rc.d/rc.snmpd start
#fi


# Turn on process accounting.  To enable process accounting, make sure the
# option for BSD process accounting is enabled in your kernel, and then
# create the file /var/log/pacct (touch /var/log/pacct).  By default, process
# accounting is not enabled (since /var/log/pacct does not exist).  This is
# because the log file can get VERY large.
if [ -x /sbin/accton -a -r /var/log/pacct ]; then
  chmod 640 /var/log/pacct
  /sbin/accton /var/log/pacct
fi

# Start crond (Dillon's crond):
# If you want cron to actually log activity to /var/log/cron, then change
# -l notice to -l info to increase the logging level.
if [ -x /usr/sbin/crond ]; then
  /usr/sbin/crond -l notice
fi

# Start atd (manages jobs scheduled with 'at'):
if [ -x /usr/sbin/atd ]; then
  /usr/sbin/atd -b 15 -l 1
fi

# Load ALSA (sound) defaults:
if [ -x /etc/rc.d/rc.alsa ]; then
  . /etc/rc.d/rc.alsa
fi

# Start mpd
if [ -x /etc/rc.d/rc.mpd ]; then
  /etc/rc.d/rc.mpd start
fi

# Load a custom screen font if the user has an rc.font script.
if [ -x /etc/rc.d/rc.font ]; then
  . /etc/rc.d/rc.font
fi

# Load a custom keymap if the user has an rc.keymap script.
if [ -x /etc/rc.d/rc.keymap ]; then
  . /etc/rc.d/rc.keymap
fi

# Start Apache web server:
if [ -x /etc/rc.d/rc.httpd ]; then
  . /etc/rc.d/rc.httpd start
fi

# If there are SystemV init scripts for this runlevel, run them.
if [ -x /etc/rc.d/rc.sysvinit ]; then
  . /etc/rc.d/rc.sysvinit
fi

# Start ympd
if [ -x /etc/rc.d/rc.ympd ]; then
  /etc/rc.d/rc.ympd start
fi

# MediaTomb
if [ -x /etc/rc.d/rc.mediatomb ]; then
    /etc/rc.d/rc.mediatomb start
fi

# Start carpino Project
if [ -x /etc/rc.d/rc.carpino ]; then
  /etc/rc.d/rc.carpino start
fi


# Start the local setup procedure.
if [ -x /etc/rc.d/rc.local ]; then
  . /etc/rc.d/rc.local
fi

# All done.
