#!/bin/bash
name=lcd-fb.service
if [ ! -f "$name" ]; then
    cd /tmp
    wget -O $name.tmp https://github.com/poikilos/pypicolcd/raw/master/$name
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

sed -i.bak "s/^\\(User=\).*/\\1$UNPRIV_USER/" /tmp/$name.tmp
sed -i.bak "s/^\\(Group=\).*/\\1$UNPRIV_GROUP/" /tmp/$name.tmp
sudo mv -f /tmp/$name.tmp /tmp/$name

sudo mv /tmp/$name /etc/systemd/system/

sudo systemctl enable lcd-fb
sudo systemctl start lcd-fb
