[![Latest Release](http://tvlinker.ozmartians.com/images/button-latest-release.png)](https://github.com/ozmartian/tvlinker/releases/latest)

[![Build Status](https://travis-ci.org/ozmartian/tvlinker.svg?branch=master)](https://travis-ci.org/ozmartian/tvlinker)

## TVLinker

![TVLinker](http://tvlinker.ozmartians.com/images/header-logo.png)

## Important Note

Due to technical reasons, TVLinker now requires a local installation of NodeJS on your machine in order to run some JavaScript to get past CloudFlare's bot checks. This could be done with Qt but that would drag in the WebEngine (Chromium-based) dependency which is 3-4 times larger in size than a simple NodeJS server installation.

You can install NodeJS without needing to think about it, just [download from the official site here](https://nodejs.org/en/download/current).

## Arch Linux AUR

Just use your favourite AUR helper script/app and look for AUR package named 'tvlinker'. Example:

    pacaur -S tvlinker
          or
    yaourt -S tvlinker

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
