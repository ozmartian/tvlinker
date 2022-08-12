[![Build Status](https://travis-ci.org/ozmartian/tvlinker.svg?branch=master)](https://travis-ci.org/ozmartian/tvlinker)

![TVLinker](http://tvlinker.ozmartians.com/images/header-banner.png) 
[![Latest Release](http://tvlinker.ozmartians.com/images/button-latest-release.png)](https://github.com/ozmartian/tvlinker/releases/latest)

## Arch Linux AUR

Just use your favourite AUR helper script/app and look for AUR package named 'tvlinker-git'. Example:

    yay -S tvlinker-git

## Ubuntu/Mint/Debian and all other Ubuntu derivatives

Users can install the latest release via:

    ppa:ozmartian/apps

If you are new to PPAs then just issue the following commands in a terminal:

    sudo add-apt-repository ppa:ozmartian/apps
    sudo apt-get update
    sudo apt-get install tvlinker

## What is TVLinker?

 PyQt5 based desktop widget for scraping and downloading TV shows from Scene-RLS.com

 **Recently updated for Scene-RLS.com due to tv-release.net closing down**

 You get link scraping together with integration to the real-debrid link unrestrictor
 service via their API (NOTE: a valid real-debrid account is required for link unrestricting
 to work).

 Supports a number of download managers across platforms:

    Built-in (window/linux)
    Aria2 RPC Daemon (windows/linux)
    Internet Download Manager (windows)
    KGet (linux)
    Persepolis (windows/linux)
    pyload (windows/linux)
