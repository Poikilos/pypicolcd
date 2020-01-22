#!/bin/bash
name=lcd-fb.service
if [ ! -f "$name" ]; then
    wget -O /tmp/$name.tmp https://github.com/poikilos/pypicolcd/raw/master/$name
else
    cp $name /tmp/$name.tmp
fi

if [ -z "$UNPRIV_USER" ]; then
    UNPRIV_USER=$USER
    echo "* installing as user '$UNPRIV_USER'"
fi
if [ -z "$UNPRIV_GROUP" ]; then
    UNPRIV_GROUP=`id -gn`
    echo "* installing as group '$UNPRIV_GROUP'"
fi

LCD_FB_PATH="`command -v lcd-fb`"

if [ ! -f "$LCD_FB_PATH" ]; then
    echo "lcd-fb is not in the path. Make sure you have activated the virtualenv or that you have otherwise installed:"
    echo "  pip install --upgrade https://github.com/poikilos/pypicolcd/archive/master.zip"
    # exit 1
fi

sed -i.bak "s/^\\(User=\).*/\\1$UNPRIV_USER/" /tmp/$name.tmp
sed -i.bak "s/^\\(Group=\).*/\\1$UNPRIV_GROUP/" /tmp/$name.tmp
LCD_FB_PATH_ESCAPED="${LCD_FB_PATH//\//\\\/}"  # two slashes to replace all
sed -i.bak "s/^\\(ExecStart=\).*/\\1$LCD_FB_PATH_ESCAPED/" /tmp/$name.tmp
echo "Enter password for root:"
su - -c "mv -f /tmp/$name.tmp /tmp/$name && mv -f /tmp/$name /etc/systemd/system/ && systemctl enable lcd-fb && systemctl start lcd-fb"

result=`ps aux | grep python | grep lcd-fb`
if [ ! -z "$result" ]; then
    echo "* lcd-fb is running as '$result'."
else
    echo "* lcd-fb does not appear to be running."
fi
