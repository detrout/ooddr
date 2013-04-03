Out of Date Repository
----------------------

My efforts at scanning through a hierarchy of related debian
package repositories and find which ones still need to be built.

Currently you can do 

outdated -p <path to a repository package file> <project root>

The project root is a tree of unpacked debian source trees.

I'm using this to try to figure out how to build newer versions of KDE
on debian, and KDE SC has enough packages in that its really useful to
group packages into seperate sub-directories.

TODO
----

I'd really like something to read watch files.

LICENSE
-------

I'm not really sure if it should be GPLed, but I started there.


